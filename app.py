# CIB Financial Analysis Engine - standalone Streamlit app
# Start with: streamlit run financial_app.py
# Add more EGX symbols inside STOCKS below, e.g. "MFPC.CA".

import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# =========================
# CONFIGURATION
# =========================
STOCKS = [
    "COMI.CA",  # CIB - Commercial International Bank Egypt
]

PERIOD = "5y"
MAX_WORKERS = 4

st.set_page_config(
    page_title="EGX Financial Analyzer",
    page_icon="📊",
    layout="wide",
)

# =========================
# HELPERS
# =========================
def safe_float(x):
    try:
        x = float(x)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan


def pct(x):
    return np.nan if pd.isna(x) else x * 100.0


def growth(first, last):
    first, last = safe_float(first), safe_float(last)
    if pd.isna(first) or pd.isna(last) or first == 0:
        return np.nan
    return (last / first - 1) * 100


def cagr(first, last, years):
    first, last = safe_float(first), safe_float(last)
    if pd.isna(first) or pd.isna(last) or first <= 0 or last <= 0 or years <= 0:
        return np.nan
    return ((last / first) ** (1 / years) - 1) * 100


def latest_value(series):
    if series is None or len(series) == 0:
        return np.nan
    s = pd.to_numeric(series, errors="coerce").dropna()
    return safe_float(s.iloc[0]) if len(s) else np.nan


def historical_growth(series):
    if series is None or len(series) < 2:
        return np.nan
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 2:
        return np.nan
    return growth(s.iloc[-1], s.iloc[0])


def get_statement_row(df, names):
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            return df.loc[name]
    return None


def get_yf_info(symbol):
    ticker = yf.Ticker(symbol)
    try:
        info = ticker.info
    except Exception:
        info = {}
    return ticker, info


# =========================
# SCORING
# Scores are intentionally transparent and rule-based.
# Missing data does NOT receive a false positive.
# =========================
def score_growth(revenue_g, earnings_g, eps_g):
    vals = [x for x in [revenue_g, earnings_g, eps_g] if pd.notna(x)]
    if not vals:
        return np.nan
    score = 50.0
    score += np.clip(np.nanmean(vals) * 1.2, -40, 40)
    return float(np.clip(score, 0, 100))


def score_profitability(roe, roa, margin):
    vals = []
    if pd.notna(roe): vals.append(np.clip(roe * 3.0, 0, 100))
    if pd.notna(roa): vals.append(np.clip(roa * 12.0, 0, 100))
    if pd.notna(margin): vals.append(np.clip(margin * 2.0, 0, 100))
    return float(np.mean(vals)) if vals else np.nan


def score_health(debt_equity, current_ratio):
    vals = []
    if pd.notna(debt_equity):
        # For banks D/E is structurally high, so this is only a generic
        # supplementary metric, not a bank-specific solvency judgment.
        vals.append(float(np.clip(80 - max(debt_equity - 2, 0) * 10, 0, 100)))
    if pd.notna(current_ratio):
        vals.append(float(np.clip(current_ratio * 50, 0, 100)))
    return float(np.mean(vals)) if vals else np.nan


def score_cashflow(fcf, net_income):
    if pd.isna(fcf) or pd.isna(net_income) or net_income == 0:
        return np.nan
    ratio = fcf / net_income
    return float(np.clip(50 + ratio * 50, 0, 100))


def score_valuation(pe, pb):
    vals = []
    if pd.notna(pe) and pe > 0:
        vals.append(np.clip(100 - pe * 5, 0, 100))
    if pd.notna(pb) and pb > 0:
        vals.append(np.clip(100 - pb * 30, 0, 100))
    return float(np.mean(vals)) if vals else np.nan


def score_dividend(yield_pct, payout_pct):
    vals = []
    if pd.notna(yield_pct):
        vals.append(np.clip(yield_pct * 12, 0, 100))
    if pd.notna(payout_pct):
        # middle-range payout is treated as more sustainable than extremes
        vals.append(np.clip(100 - abs(payout_pct - 45) * 1.4, 0, 100))
    return float(np.mean(vals)) if vals else np.nan


def weighted_score(scores):
    weights = {
        "growth": 0.22,
        "profitability": 0.22,
        "health": 0.18,
        "cashflow": 0.14,
        "valuation": 0.16,
        "dividend": 0.08,
    }
    available = {k: v for k, v in scores.items() if pd.notna(v)}
    if not available:
        return np.nan
    total_w = sum(weights[k] for k in available)
    return sum(available[k] * weights[k] for k in available) / total_w


# =========================
# ANALYSIS
# =========================
@st.cache_data(ttl=3600, show_spinner=False)
def analyze_stock(symbol):
    ticker, info = get_yf_info(symbol)

    annual_income = ticker.financials
    annual_balance = ticker.balance_sheet
    annual_cash = ticker.cashflow

    # Current market data
    price = safe_float(info.get("currentPrice"))
    if pd.isna(price):
        try:
            hist = ticker.history(period="5d", auto_adjust=False)
            if not hist.empty:
                price = safe_float(hist["Close"].dropna().iloc[-1])
        except Exception:
            pass

    market_cap = safe_float(info.get("marketCap"))
    pe = safe_float(info.get("trailingPE"))
    pb = safe_float(info.get("priceToBook"))
    dividend_yield = safe_float(info.get("dividendYield"))
    payout = safe_float(info.get("payoutRatio"))
    roe = safe_float(info.get("returnOnEquity"))
    roa = safe_float(info.get("returnOnAssets"))
    profit_margin = safe_float(info.get("profitMargins"))
    debt_equity = safe_float(info.get("debtToEquity"))
    current_ratio = safe_float(info.get("currentRatio"))

    revenue = get_statement_row(
        annual_income,
        ["Total Revenue", "Operating Revenue", "Revenue"]
    )
    net_income = get_statement_row(
        annual_income,
        ["Net Income", "Net Income Common Stockholders"]
    )
    eps = get_statement_row(
        annual_income,
        ["Diluted EPS", "Basic EPS"]
    )
    op_cash = get_statement_row(
        annual_cash,
        ["Operating Cash Flow", "Total Cash From Operating Activities"]
    )
    capex = get_statement_row(
        annual_cash,
        ["Capital Expenditure", "Capital Expenditures"]
    )

    # Convert dividend yield/payout from decimal to percentage.
    dy_pct = pct(dividend_yield)
    payout_pct = pct(payout)

    revenue_g = historical_growth(revenue)
    earnings_g = historical_growth(net_income)
    eps_g = historical_growth(eps)

    fcf = np.nan
    if op_cash is not None and capex is not None:
        ocf = latest_value(op_cash)
        cx = latest_value(capex)
        if pd.notna(ocf) and pd.notna(cx):
            fcf = ocf + cx if cx < 0 else ocf - cx

    latest_ni = latest_value(net_income)

    scores = {
        "growth": score_growth(revenue_g, earnings_g, eps_g),
        "profitability": score_profitability(pct(roe), pct(roa), pct(profit_margin)),
        "health": score_health(debt_equity, current_ratio),
        "cashflow": score_cashflow(fcf, latest_ni),
        "valuation": score_valuation(pe, pb),
        "dividend": score_dividend(dy_pct, payout_pct),
    }

    financial_score = weighted_score(scores)
    coverage = len([v for v in scores.values() if pd.notna(v)]) / len(scores) * 100

    # Recent annual values table
    annual = pd.DataFrame()
    if annual_income is not None and not annual_income.empty:
        rows = {}
        for label, names in {
            "Revenue": ["Total Revenue", "Operating Revenue", "Revenue"],
            "Net Income": ["Net Income", "Net Income Common Stockholders"],
            "EPS": ["Diluted EPS", "Basic EPS"],
        }.items():
            row = get_statement_row(annual_income, names)
            if row is not None:
                rows[label] = pd.to_numeric(row, errors="coerce")
        if rows:
            annual = pd.DataFrame(rows)

    return {
        "symbol": symbol,
        "name": info.get("longName", symbol),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "price": price,
        "market_cap": market_cap,
        "pe": pe,
        "pb": pb,
        "dividend_yield": dy_pct,
        "payout": payout_pct,
        "roe": pct(roe),
        "roa": pct(roa),
        "profit_margin": pct(profit_margin),
        "debt_equity": debt_equity,
        "current_ratio": current_ratio,
        "revenue_growth": revenue_g,
        "earnings_growth": earnings_g,
        "eps_growth": eps_g,
        "fcf": fcf,
        "financial_score": financial_score,
        "data_coverage": coverage,
        "scores": scores,
        "annual": annual,
    }


def fmt(x, suffix="", decimals=2):
    return "—" if pd.isna(x) else f"{x:.{decimals}f}{suffix}"


# =========================
# UI
# =========================
st.title("📊 EGX Financial Analyzer")
st.caption("تحليل مالي مستقل عن التحليل الفني — البداية بسهم CIB / COMI.CA")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    st.write("**الأسهم الحالية:**")
    st.code("\n".join(STOCKS))
    st.info("لإضافة سهم: ضعه داخل STOCKS بنفس صيغة Yahoo Finance مثل MFPC.CA.")
    if st.button("🔄 تحديث البيانات"):
        analyze_stock.clear()
        st.rerun()

results = []
progress = st.progress(0)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(analyze_stock, s): s for s in STOCKS}
    for i, future in enumerate(as_completed(futures), 1):
        symbol = futures[future]
        try:
            results.append(future.result())
        except Exception as e:
            results.append({
                "symbol": symbol,
                "name": symbol,
                "financial_score": np.nan,
                "data_coverage": 0,
                "error": str(e),
                "scores": {},
                "annual": pd.DataFrame(),
            })
        progress.progress(i / len(futures))

progress.empty()

if not results:
    st.error("مفيش أسهم للتحليل.")
    st.stop()

results = sorted(
    results,
    key=lambda x: x.get("financial_score", -np.inf)
    if pd.notna(x.get("financial_score", np.nan)) else -np.inf,
    reverse=True,
)

# Main ranking table
table_rows = []
for r in results:
    s = r.get("scores", {})
    table_rows.append({
        "السهم": r["symbol"],
        "الشركة": r.get("name", ""),
        "Financial Score": r.get("financial_score", np.nan),
        "Growth": s.get("growth", np.nan),
        "Profitability": s.get("profitability", np.nan),
        "Financial Health": s.get("health", np.nan),
        "Cash Flow": s.get("cashflow", np.nan),
        "Valuation": s.get("valuation", np.nan),
        "Dividend": s.get("dividend", np.nan),
        "Data Coverage %": r.get("data_coverage", np.nan),
    })

df = pd.DataFrame(table_rows)
st.subheader("🏆 الترتيب المالي")
st.dataframe(
    df.style.format({
        "Financial Score": "{:.1f}",
        "Growth": "{:.1f}",
        "Profitability": "{:.1f}",
        "Financial Health": "{:.1f}",
        "Cash Flow": "{:.1f}",
        "Valuation": "{:.1f}",
        "Dividend": "{:.1f}",
        "Data Coverage %": "{:.0f}",
    }, na_rep="—"),
    use_container_width=True,
    hide_index=True,
)

# Detailed cards
for r in results:
    st.divider()
    st.subheader(f"{r['symbol']} — {r.get('name', '')}")

    if r.get("error"):
        st.error(r["error"])
        continue

    cols = st.columns(4)
    cols[0].metric("Financial Score", fmt(r["financial_score"], "", 1))
    cols[1].metric("السعر الحالي", fmt(r["price"], " EGP", 2))
    cols[2].metric("P/E", fmt(r["pe"], "", 2))
    cols[3].metric("P/B", fmt(r["pb"], "", 2))

    cols = st.columns(4)
    cols[0].metric("ROE", fmt(r["roe"], "%", 2))
    cols[1].metric("ROA", fmt(r["roa"], "%", 2))
    cols[2].metric("Profit Margin", fmt(r["profit_margin"], "%", 2))
    cols[3].metric("Dividend Yield", fmt(r["dividend_yield"], "%", 2))

    cols = st.columns(4)
    cols[0].metric("Revenue Growth", fmt(r["revenue_growth"], "%", 2))
    cols[1].metric("Earnings Growth", fmt(r["earnings_growth"], "%", 2))
    cols[2].metric("EPS Growth", fmt(r["eps_growth"], "%", 2))
    cols[3].metric("Data Coverage", fmt(r["data_coverage"], "%", 0))

    st.markdown("**توزيع الدرجة**")
    score_df = pd.DataFrame(
        [{"البند": k, "Score": v} for k, v in r["scores"].items()]
    )
    st.dataframe(
        score_df.style.format({"Score": "{:.1f}"}, na_rep="—"),
        use_container_width=True,
        hide_index=True,
    )

    if not r["annual"].empty:
        st.markdown("**البيانات السنوية المتاحة من Yahoo Finance**")
        st.dataframe(
            r["annual"].style.format("{:,.2f}", na_rep="—"),
            use_container_width=True,
        )

st.divider()
st.caption(
    "مهم: ده محرك تحليل مالي عام كبداية. البنوك لها مقاييس متخصصة (مثل NIM، NPL، CAR، Cost/Income، "
    "Loan/Deposit)، لذلك النسخة القادمة الأفضل نضيف Bank Financial Engine مخصوص لـ CIB والبنوك، "
    "وبعدين Engines مختلفة للقطاعات غير البنكية."
)
