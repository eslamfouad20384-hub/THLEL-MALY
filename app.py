# -*- coding: utf-8 -*-
"""EGX Banks Financial Intelligence PRO
Version 1.2 — daily-candle price source
Financial analysis only; public data may be incomplete or delayed.
"""

import math
import time
from datetime import datetime, date, time as dt_time
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

APP_VERSION = "1.2 Daily Candle Price"
CACHE_TTL = 1800
CAIRO_TZ = ZoneInfo("Africa/Cairo")

st.set_page_config(
    page_title="EGX Banks Financial Intelligence PRO",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BANKS = (
    {"symbol": "COMI.CA", "name": "البنك التجاري الدولي - CIB", "short": "CIB"},
    {"symbol": "HDBK.CA", "name": "بنك التعمير والإسكان", "short": "HDBK"},
    {"symbol": "ADIB.CA", "name": "مصرف أبوظبي الإسلامي - مصر", "short": "ADIB"},
    {"symbol": "CIEB.CA", "name": "بنك قناة السويس", "short": "CIEB"},
    {"symbol": "QNBA.CA", "name": "بنك قطر الوطني الأهلي", "short": "QNBA"},
    {"symbol": "FAIT.CA", "name": "بنك فيصل الإسلامي المصري", "short": "FAIT"},
    {"symbol": "EXPA.CA", "name": "البنك المصري لتنمية الصادرات", "short": "EXPA"},
    {"symbol": "EGBE.CA", "name": "البنك المصري الخليجي", "short": "EGBE"},
    {"symbol": "SAUD.CA", "name": "بنك الشركة المصرفية العربية الدولية", "short": "SAUD"},
    {"symbol": "CANA.CA", "name": "بنك قناة السويس/رمز يحتاج تحقق", "short": "CANA"},
)

# ---------- Helpers ----------
def finite_num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else np.nan
    except (TypeError, ValueError):
        return np.nan


def safe_div(a, b):
    a, b = finite_num(a), finite_num(b)
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return np.nan
    return a / b


def fmt_num(value, decimals=2):
    x = finite_num(value)
    return "—" if not np.isfinite(x) else f"{x:,.{decimals}f}"


def fmt_pct(value, decimals=1):
    x = finite_num(value)
    return "—" if not np.isfinite(x) else f"{x * 100:.{decimals}f}%"


def clean_text(value, fallback="غير متاح"):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text and text.lower() not in {"none", "nan", "null"} else fallback


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_daily_candle_price(symbol: str):
    """Return latest completed daily candle close, not Yahoo info/currentPrice.

    EGX normally trades Sunday–Thursday. The current Cairo date is excluded until
    15:00 Cairo time so an in-progress daily candle is not mislabeled as a close.
    This still depends on the freshness/completeness of Yahoo Finance data.
    """
    now = datetime.now(CAIRO_TZ)
    try:
        hist = yf.Ticker(symbol).history(
            period="10d", interval="1d", auto_adjust=False, actions=False,
            raise_errors=False,
        )
        if hist is None or hist.empty or "Close" not in hist.columns:
            return {"price": np.nan, "date": None, "source": "Yahoo Finance daily OHLC", "status": "فشل تحميل الشموع اليومية"}

        hist = hist.copy()
        hist = hist.loc[pd.to_numeric(hist["Close"], errors="coerce").notna()]
        hist = hist.loc[hist["Close"].astype(float) > 0]
        if hist.empty:
            return {"price": np.nan, "date": None, "source": "Yahoo Finance daily OHLC", "status": "لا يوجد إغلاق صالح"}

        def index_date(idx):
            ts = pd.Timestamp(idx)
            if ts.tzinfo is not None:
                # Daily candles are keyed to the exchange date; preserve that date.
                return ts.date()
            return ts.date()

        today_cairo = now.date()
        eligible = []
        for idx, row in hist.iterrows():
            bar_date = index_date(idx)
            # Exclude today's candle before 15:00 Cairo time, because it may be forming.
            if bar_date == today_cairo and now.time() < dt_time(15, 0):
                continue
            eligible.append((bar_date, float(row["Close"])))

        if not eligible:
            # If only today's in-progress bar was returned, don't label it as a completed close.
            return {"price": np.nan, "date": None, "source": "Yahoo Finance daily OHLC", "status": "لا توجد شمعة مكتملة متاحة بعد"}

        bar_date, close_price = max(eligible, key=lambda item: item[0])
        age_days = (today_cairo - bar_date).days
        status = "آخر إغلاق يومي متاح" if age_days <= 5 else f"تحذير: آخر شمعة أقدم من {age_days} يومًا"
        return {
            "price": close_price,
            "date": bar_date.isoformat(),
            "source": "Yahoo Finance — Daily OHLC / Close",
            "status": status,
        }
    except Exception as exc:
        return {"price": np.nan, "date": None, "source": "Yahoo Finance daily OHLC", "status": f"خطأ تحميل: {type(exc).__name__}"}


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def retrieve_bank_data(bank_definition: tuple, cost_of_equity: float):
    """Load one bank. Accept tuple pairs or a dict to avoid tuple/dict regression."""
    if isinstance(bank_definition, dict):
        bank = dict(bank_definition)
    else:
        bank = dict(bank_definition)

    symbol = bank["symbol"]
    record = {
        "symbol": symbol,
        "name": bank.get("name", symbol),
        "short": bank.get("short", symbol.replace(".CA", "")),
        "price": np.nan,
        "price_date": None,
        "price_source": "Yahoo Finance — Daily OHLC / Close",
        "price_status": "لم يتم تحميل السعر",
        "currency": "EGP (تحقق من المصدر)",
        "market_cap": np.nan,
        "book_value_per_share": np.nan,
        "roe": np.nan,
        "roa": np.nan,
        "profit_margin": np.nan,
        "dividend_yield": np.nan,
        "trailing_pe": np.nan,
        "price_to_book": np.nan,
        "total_revenue": np.nan,
        "net_income": np.nan,
        "total_assets": np.nan,
        "total_equity": np.nan,
        "total_debt": np.nan,
        "data_quality": 0.0,
        "data_notes": [],
        "error": "",
    }

    # Mandatory price source: latest completed daily candle Close.
    candle = get_daily_candle_price(symbol)
    record.update({
        "price": candle["price"],
        "price_date": candle["date"],
        "price_source": candle["source"],
        "price_status": candle["status"],
    })

    try:
        ticker = yf.Ticker(symbol)
        info = {}
        try:
            info = ticker.get_info() or {}
        except Exception:
            try:
                info = ticker.info or {}
            except Exception:
                info = {}

        # Never use info/currentPrice/regularMarketPrice to override the candle close.
        mapping = {
            "currency": "currency",
            "market_cap": "marketCap",
            "book_value_per_share": "bookValue",
            "roe": "returnOnEquity",
            "roa": "returnOnAssets",
            "profit_margin": "profitMargins",
            "dividend_yield": "dividendYield",
            "trailing_pe": "trailingPE",
            "price_to_book": "priceToBook",
            "total_revenue": "totalRevenue",
            "net_income": "netIncomeToCommon",
            "total_assets": "totalAssets",
            "total_equity": "totalStockholderEquity",
            "total_debt": "totalDebt",
        }
        for out_key, info_key in mapping.items():
            val = info.get(info_key)
            if out_key == "currency":
                if val:
                    record[out_key] = str(val)
            else:
                record[out_key] = finite_num(val)

        # Fill missing basic fundamentals from latest annual/quarterly statements where available.
        try:
            income = ticker.income_stmt
            if income is None or income.empty:
                income = ticker.financials
            if income is not None and not income.empty:
                col = income.columns[0]
                if not np.isfinite(record["total_revenue"]):
                    for key in ("Total Revenue", "Operating Revenue", "Revenue"):
                        if key in income.index:
                            record["total_revenue"] = finite_num(income.loc[key, col]); break
                if not np.isfinite(record["net_income"]):
                    for key in ("Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operation Net Minority Interest"):
                        if key in income.index:
                            record["net_income"] = finite_num(income.loc[key, col]); break
        except Exception:
            record["data_notes"].append("قائمة الدخل غير متاحة من Yahoo Finance")

        try:
            balance = ticker.balance_sheet
            if balance is not None and not balance.empty:
                col = balance.columns[0]
                for out_key, candidates in {
                    "total_assets": ("Total Assets",),
                    "total_equity": ("Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"),
                    "total_debt": ("Total Debt", "Long Term Debt", "Current Debt"),
                }.items():
                    if not np.isfinite(record[out_key]):
                        for key in candidates:
                            if key in balance.index:
                                record[out_key] = finite_num(balance.loc[key, col]); break
        except Exception:
            record["data_notes"].append("الميزانية غير متاحة من Yahoo Finance")

    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: تعذر تحميل بعض البيانات المالية"

    # Quality measures field coverage, not whether the figures have been independently audited.
    quality_fields = [
        "price", "book_value_per_share", "roe", "roa", "profit_margin",
        "trailing_pe", "price_to_book", "total_revenue", "net_income",
        "total_assets", "total_equity", "dividend_yield",
    ]
    available = sum(np.isfinite(finite_num(record.get(k))) for k in quality_fields)
    record["data_quality"] = round(100 * available / len(quality_fields), 1)
    if not np.isfinite(record["price"]):
        record["data_notes"].append("لم يتوفر سعر إغلاق يومي مكتمل؛ تم ترك السعر فارغًا بدل استخدام سعر قديم من info")
    if not record["price_date"]:
        record["data_notes"].append("تاريخ آخر شمعة غير متاح")
    if record["currency"] not in ("EGP", "EGp"):
        record["data_notes"].append(f"عملة المصدر: {record['currency']}؛ تحقق من وحدة السعر والقوائم قبل الاعتماد")
    return record


def valuation_engine(r, cost_of_equity):
    price = finite_num(r.get("price"))
    bvps = finite_num(r.get("book_value_per_share"))
    roe = finite_num(r.get("roe"))
    eps = np.nan
    net_income = finite_num(r.get("net_income"))
    market_cap = finite_num(r.get("market_cap"))
    shares = safe_div(market_cap, price)
    if np.isfinite(net_income) and np.isfinite(shares) and shares > 0:
        eps = net_income / shares

    # Justified P/B: simplified bank valuation, not a substitute for audited bank-specific modelling.
    justified_pb = np.nan
    if np.isfinite(roe) and cost_of_equity > 0:
        justified_pb = float(np.clip(roe / cost_of_equity, 0.25, 2.5))

    residual_income_value = np.nan
    if np.isfinite(bvps) and bvps > 0 and np.isfinite(roe) and cost_of_equity > 0:
        sustainable_growth = float(np.clip(roe * 0.35, 0.00, 0.08))
        if cost_of_equity > sustainable_growth:
            residual_income_value = bvps + ((roe - cost_of_equity) * bvps) / (cost_of_equity - sustainable_growth)
            residual_income_value = max(0.0, residual_income_value)

    pb_value = justified_pb * bvps if np.isfinite(justified_pb) and np.isfinite(bvps) and bvps > 0 else np.nan
    pe_value = eps * 7.0 if np.isfinite(eps) and eps > 0 else np.nan
    candidates = [x for x in (residual_income_value, pb_value, pe_value) if np.isfinite(x) and x > 0]
    fair = float(np.median(candidates)) if candidates else np.nan
    low = float(np.percentile(candidates, 25)) if len(candidates) >= 2 else (fair * 0.85 if np.isfinite(fair) else np.nan)
    high = float(np.percentile(candidates, 75)) if len(candidates) >= 2 else (fair * 1.15 if np.isfinite(fair) else np.nan)
    return {
        "eps_estimated": eps,
        "justified_pb": justified_pb,
        "pb_value": pb_value,
        "residual_income_value": residual_income_value,
        "pe_value": pe_value,
        "fair_value": fair,
        "fair_low": low,
        "fair_high": high,
        "buy_10": fair * 0.90 if np.isfinite(fair) else np.nan,
        "buy_20": fair * 0.80 if np.isfinite(fair) else np.nan,
        "buy_30": fair * 0.70 if np.isfinite(fair) else np.nan,
        "upside_pct": safe_div(fair, price) - 1 if np.isfinite(fair) and np.isfinite(price) and price > 0 else np.nan,
        "valuation_methods": len(candidates),
    }


def scenario_engine(r, fair_value):
    price = finite_num(r.get("price"))
    roe = finite_num(r.get("roe"))
    if not np.isfinite(fair_value) or fair_value <= 0:
        return {"target_3y_bear": np.nan, "target_3y_base": np.nan, "target_3y_bull": np.nan}
    # Scenario multipliers are transparent assumptions, not forecasts from a full bank model.
    roe_adj = float(np.clip(roe if np.isfinite(roe) else 0.12, 0.05, 0.25))
    base_growth = float(np.clip((roe_adj - 0.10) * 0.30, -0.02, 0.06))
    bear = fair_value * ((1 + min(base_growth, 0.01)) ** 3) * 0.80
    base = fair_value * ((1 + base_growth) ** 3)
    bull = fair_value * ((1 + max(base_growth + 0.04, 0.03)) ** 3) * 1.15
    return {"target_3y_bear": bear, "target_3y_base": base, "target_3y_bull": bull}


def score_bank(r, v):
    parts = []
    roe = finite_num(r.get("roe"))
    roa = finite_num(r.get("roa"))
    dy = finite_num(r.get("dividend_yield"))
    pb = finite_num(r.get("price_to_book"))
    if np.isfinite(roe): parts.append(float(np.clip(roe / 0.20, 0, 1)) * 25)
    if np.isfinite(roa): parts.append(float(np.clip(roa / 0.025, 0, 1)) * 15)
    if np.isfinite(dy): parts.append(float(np.clip(dy / 0.08, 0, 1)) * 10)
    if np.isfinite(pb) and pb > 0: parts.append(float(np.clip(1.5 / pb, 0, 1)) * 15)
    upside = finite_num(v.get("upside_pct"))
    if np.isfinite(upside): parts.append(float(np.clip((upside + 0.20) / 0.60, 0, 1)) * 20)
    q = finite_num(r.get("data_quality"))
    if np.isfinite(q): parts.append(float(np.clip(q / 100, 0, 1)) * 15)
    # Do not scale incomplete metrics up to 100: missing fields reduce score coverage.
    max_possible = 25 + 15 + 10 + 15 + 20 + 15
    actual_weight = sum({"roe":25 if np.isfinite(roe) else 0, "roa":15 if np.isfinite(roa) else 0,
                         "dy":10 if np.isfinite(dy) else 0, "pb":15 if np.isfinite(pb) and pb > 0 else 0,
                         "upside":20 if np.isfinite(upside) else 0, "quality":15 if np.isfinite(q) else 0}.values())
    raw = sum(parts) * max_possible / actual_weight if actual_weight else 0
    # Data quality penalty prevents sparse records from appearing overly strong.
    return round(float(np.clip(raw * (0.55 + 0.45 * (q / 100 if np.isfinite(q) else 0)), 0, 100)), 1)


def analyze_bank(bank_def, cost_of_equity):
    # Pass a tuple of pairs into cache-safe function; it normalizes to dict internally.
    bank_tuple = tuple(sorted(dict(bank_def).items()))
    r = retrieve_bank_data(bank_tuple, float(cost_of_equity))
    v = valuation_engine(r, float(cost_of_equity))
    s = scenario_engine(r, v["fair_value"])
    result = {**r, **v, **s}
    result["score"] = score_bank(result, v)
    price = finite_num(result.get("price"))
    fair = finite_num(result.get("fair_value"))
    if not np.isfinite(price): result["recommendation"] = "لا يوجد سعر يومي موثوق"
    elif not np.isfinite(fair): result["recommendation"] = "بيانات غير كافية للتقييم"
    elif fair / price >= 1.25: result["recommendation"] = "قيمة محتملة — راجع البيانات"
    elif fair / price >= 1.05: result["recommendation"] = "مراقبة / تقييم مقبول"
    elif fair / price < 0.90: result["recommendation"] = "السعر أعلى من القيمة المقدرة"
    else: result["recommendation"] = "محايد"
    return result


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_all_banks_cached(bank_definitions, cost_of_equity):
    banks = []
    for item in bank_definitions:
        banks.append(dict(item) if isinstance(item, dict) else dict(item))
    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(analyze_bank, bank, cost_of_equity): bank for bank in banks}
        for future in as_completed(futures):
            bank = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append({"symbol": bank.get("symbol", "?"), "error": type(exc).__name__})
    return results, errors


def make_display_df(records):
    rows = []
    for r in records:
        rows.append({
            "الترتيب": 0,
            "البنك": r.get("name"),
            "الرمز": r.get("symbol"),
            "السعر (إغلاق يومي)": r.get("price"),
            "تاريخ الشمعة": r.get("price_date"),
            "حالة السعر": r.get("price_status"),
            "القيمة العادلة التقديرية": r.get("fair_value"),
            "قيمة عادلة - منخفض": r.get("fair_low"),
            "قيمة عادلة - مرتفع": r.get("fair_high"),
            "شراء بخصم 10%": r.get("buy_10"),
            "شراء بخصم 20%": r.get("buy_20"),
            "شراء بخصم 30%": r.get("buy_30"),
            "العائد المحتمل": r.get("upside_pct"),
            "ROE": r.get("roe"),
            "ROA": r.get("roa"),
            "القيمة الدفترية للسهم": r.get("book_value_per_share"),
            "P/B من المصدر": r.get("price_to_book"),
            "عائد التوزيعات": r.get("dividend_yield"),
            "النتيجة / 100": r.get("score"),
            "جودة البيانات %": r.get("data_quality"),
            "التوصيف": r.get("recommendation"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["score", "data_quality"], ascending=False, na_position="last").reset_index(drop=True)
        df["الترتيب"] = np.arange(1, len(df) + 1)
    return df


# ---------- UI ----------
st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px;}
.hero {padding: 1.2rem 1.4rem; border-radius: 16px; background: linear-gradient(120deg,#102a43,#176b87); color: white; margin-bottom: 1rem;}
.hero h1 {color:white; margin:0;}
.small-note {font-size:0.88rem; color:#64748b;}
</style>
<div class="hero"><h1>🏦 EGX Banks Financial Intelligence PRO</h1><p>محرك مالي للبنوك المصرية — السعر من آخر شمعة يومية مكتملة، دون الاعتماد على currentPrice.</p></div>
""", unsafe_allow_html=True)

st.warning("تنبيه: البيانات العامة قد تكون ناقصة أو متأخرة. التقييمات تقديرية وليست توصية شراء أو بيع. تحقق من القوائم المالية المنشورة وإفصاحات البورصة قبل اتخاذ قرار.")

with st.expander("⚙️ إعدادات التقييم", expanded=False):
    cost_of_equity_pct = st.slider("تكلفة حقوق الملكية المفترضة (%)", min_value=15, max_value=35, value=25, step=1)
    cache_refresh = st.button("🔄 تحديث البيانات الآن (مسح الكاش)")
    if cache_refresh:
        st.cache_data.clear()
        st.rerun()
    st.caption("تكلفة حقوق الملكية افتراض يغيّر التقييم؛ ليست قيمة منشورة من البنك.")

cost_of_equity = cost_of_equity_pct / 100
if st.button("🚀 تحميل وتحليل البنوك", type="primary", use_container_width=True):
    st.session_state["run_bank_scan"] = True

if st.session_state.get("run_bank_scan", False):
    with st.spinner("جاري تحميل الشموع اليومية والبيانات المالية المتاحة..."):
        bank_definitions = tuple(tuple(sorted(bank.items())) for bank in BANKS)
        records, errors = load_all_banks_cached(bank_definitions, cost_of_equity)
    df = make_display_df(records)
    st.session_state["bank_records"] = records
    st.session_state["bank_df"] = df
    st.session_state["bank_errors"] = errors

if "bank_df" not in st.session_state:
    st.info("اضغط «تحميل وتحليل البنوك» لبدء جلب البيانات تلقائيًا.")
else:
    df = st.session_state["bank_df"].copy()
    records = st.session_state.get("bank_records", [])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("عدد البنوك", len(df))
    c2.metric("سعر يومي متاح", int(df["السعر (إغلاق يومي)"].apply(lambda x: np.isfinite(finite_num(x))).sum()))
    c3.metric("قيمة عادلة محسوبة", int(df["القيمة العادلة التقديرية"].apply(lambda x: np.isfinite(finite_num(x))).sum()))
    c4.metric("متوسط جودة البيانات", f"{df['جودة البيانات %'].mean():.1f}%" if len(df) else "—")

    st.subheader("📊 ترتيب البنوك")
    display_cols = ["الترتيب", "البنك", "الرمز", "السعر (إغلاق يومي)", "تاريخ الشمعة", "حالة السعر", "القيمة العادلة التقديرية", "شراء بخصم 20%", "العائد المحتمل", "ROE", "القيمة الدفترية للسهم", "النتيجة / 100", "جودة البيانات %", "التوصيف"]
    st.dataframe(
        df[display_cols], use_container_width=True, hide_index=True,
        column_config={
            "السعر (إغلاق يومي)": st.column_config.NumberColumn(format="%.2f"),
            "القيمة العادلة التقديرية": st.column_config.NumberColumn(format="%.2f"),
            "شراء بخصم 20%": st.column_config.NumberColumn(format="%.2f"),
            "العائد المحتمل": st.column_config.NumberColumn(format="%.1%%"),
            "ROE": st.column_config.NumberColumn(format="%.1%%"),
            "القيمة الدفترية للسهم": st.column_config.NumberColumn(format="%.2f"),
            "النتيجة / 100": st.column_config.NumberColumn(format="%.1f"),
            "جودة البيانات %": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    st.download_button(
        "⬇️ تنزيل النتائج CSV",
        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=f"EGX_Banks_Analysis_{date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("🔎 تقرير بنك بالتفصيل")
    choices = {f"{r.get('name')} ({r.get('symbol')})": r for r in records}
    selected = st.selectbox("اختر البنك", list(choices.keys()))
    r = choices[selected]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("آخر إغلاق يومي", fmt_num(r.get("price")), help=f"تاريخ الشمعة: {r.get('price_date') or 'غير متاح'}")
    m2.metric("القيمة العادلة التقديرية", fmt_num(r.get("fair_value")))
    m3.metric("القيمة الدفترية للسهم", fmt_num(r.get("book_value_per_share")))
    m4.metric("جودة البيانات", f"{fmt_num(r.get('data_quality'), 1)}%")

    st.caption(f"مصدر السعر: {r.get('price_source')} | حالة السعر: {r.get('price_status')} | تاريخ الشمعة: {r.get('price_date') or 'غير متاح'}")
    if not np.isfinite(finite_num(r.get("price"))):
        st.error("لم يتم العثور على سعر إغلاق يومي مكتمل. لن يتم استبداله بسعر currentPrice أو سعر من مصدر آخر.")
    elif r.get("price_date"):
        try:
            age = (date.today() - date.fromisoformat(r["price_date"])).days
            if age > 5:
                st.warning(f"آخر شمعة متاحة أقدم من المعتاد ({age} يومًا). لا تتعامل مع السعر باعتباره حديثًا قبل التحقق من المصدر.")
        except Exception:
            pass

    st.markdown("#### التقييم ومناطق الشراء")
    valuation_rows = [
        ("القيمة العادلة التقديرية", r.get("fair_value")),
        ("نطاق القيمة العادلة - منخفض", r.get("fair_low")),
        ("نطاق القيمة العادلة - مرتفع", r.get("fair_high")),
        ("قيمة طريقة P/B", r.get("pb_value")),
        ("قيمة طريقة Residual Income", r.get("residual_income_value")),
        ("قيمة P/E (مضاعف افتراضي 7x)", r.get("pe_value")),
        ("منطقة شراء بخصم 10%", r.get("buy_10")),
        ("منطقة شراء بخصم 20%", r.get("buy_20")),
        ("منطقة شراء بخصم 30%", r.get("buy_30")),
        ("العائد المحتمل مقابل السعر", fmt_pct(r.get("upside_pct"))),
        ("عدد طرق التقييم المتاحة", r.get("valuation_methods")),
        ("التقييم الوصفي", r.get("recommendation")),
    ]
    st.dataframe(pd.DataFrame(valuation_rows, columns=["البند", "القيمة"]), use_container_width=True, hide_index=True)

    st.markdown("#### سيناريوهات 3 سنوات (افتراضية)")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("متحفظ", fmt_num(r.get("target_3y_bear")))
    sc2.metric("أساسي", fmt_num(r.get("target_3y_base")))
    sc3.metric("متفائل", fmt_num(r.get("target_3y_bull")))
    st.caption("السيناريوهات ناتجة عن افتراضات مبسطة مرتبطة بالعائد على حقوق الملكية والقيمة العادلة؛ ليست توقعات مضمونة.")

    st.markdown("#### جودة البيانات وملاحظات المصدر")
    notes = r.get("data_notes") or []
    if notes:
        for note in notes:
            st.write(f"- {note}")
    else:
        st.write("لم يتم تسجيل ملاحظات إضافية؛ هذا لا يعني أن البيانات مدققة أو مكتملة.")
    if r.get("error"):
        st.warning(r["error"])

    st.subheader("🧾 منهجية المحرك وحدوده")
    st.markdown("""
    - **السعر:** آخر `Close` من شمعة يومية على Yahoo Finance. لا يستخدم `info['currentPrice']` لتحديد السعر.
    - **اكتمال الشمعة:** يتم استبعاد شمعة تاريخ اليوم قبل الساعة 15:00 بتوقيت القاهرة لتجنب شمعة قد تكون قيد التكوين. بيانات المصدر نفسها قد تتأخر.
    - **القيمة العادلة:** مزيج وسيط من Residual Income وP/B مبرر وP/E بمضاعف افتراضي، فقط عند توافر المدخلات.
    - **مهم للبنوك:** P/E=7x وتكلفة حقوق الملكية واحتفاظ الأرباح افتراضات قابلة للنقاش؛ يجب تطوير النموذج باستخدام إفصاحات البنك ونموذج قطاعي مدقق.
    - **البيانات المالية:** Yahoo Finance لا يوفر كل القوائم أو النسب للبنوك المصرية. الخانات الناقصة تظل فارغة ولا يتم اختلاقها.
    - **الرموز:** القائمة ابتدائية، ويجب التحقق من كل رمز مقابل قائمة EGX الرسمية. بعض الرموز قد لا تعمل أو قد تحتاج تصحيحًا.
    """)

    if st.session_state.get("bank_errors"):
        with st.expander("عرض أخطاء التحميل"):
            st.dataframe(pd.DataFrame(st.session_state["bank_errors"]), use_container_width=True, hide_index=True)

st.markdown("<p class='small-note'>EGX Banks Financial Intelligence PRO · إصدار 1.2 · تحليل معلومات عامة، وليس نصيحة استثمارية.</p>", unsafe_allow_html=True)
