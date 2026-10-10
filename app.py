import io
import math
import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# ============================================================
# EGX BANKS FINANCIAL ANALYZER PRO
# Financial analysis only - no technical indicators
# ============================================================

APP_NAME = "EGX Banks Financial Analyzer PRO"
APP_VERSION = "1.0.0"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------- UI -----------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    .main {
        direction: rtl;
    }

    h1, h2, h3, p, label {
        text-align: right;
    }

    .hero {
        padding: 24px;
        border-radius: 16px;
        background: linear-gradient(120deg, #10243a, #176b66);
        color: white;
        margin-bottom: 20px;
    }

    .hero h1, .hero p {
        color: white;
        text-align: right;
    }

    .notice {
        padding: 12px 16px;
        border-radius: 10px;
        background: #fff4d6;
        color: #704d00;
        margin: 12px 0;
    }

    .good {
        color: #14804a;
        font-weight: 700;
    }

    .bad {
        color: #c62828;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: rgba(120, 140, 160, 0.08);
        border: 1px solid rgba(120, 140, 160, 0.2);
        padding: 12px;
        border-radius: 12px;
    }

    [data-testid="stDataFrame"] {
        direction: ltr;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero">
        <h1>🏦 EGX Banks Financial Analyzer PRO</h1>
        <p>
        محرك تحليل مالي وتقييم استثماري للبنوك المصرية
        <br>
        القوائم المالية • جودة البيانات • القيمة العادلة • هامش الأمان
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------------- Bank universe ----------------------

BANKS = {
    "COMI.CA": "البنك التجاري الدولي - CIB",
    "HDBK.CA": "بنك التعمير والإسكان",
    "ADIB.CA": "مصرف أبوظبي الإسلامي - مصر",
    "CIEB.CA": "كريدي أجريكول مصر",
    "QNBA.CA": "بنك قطر الوطني الأهلي",
    "FAIT.CA": "بنك فيصل الإسلامي المصري",
    "EXPA.CA": "البنك المصري لتنمية الصادرات",
    "EGBE.CA": "البنك المصري الخليجي",
    "SAUD.CA": "البنك السعودي المصري",
    "CANA.CA": "بنك قناة السويس",
    "UBEE.CA": "بنك الاتحاد الوطني - تحقق من حالة الإدراج والرمز",
    "AMER.CA": "رمز يحتاج إلى مراجعة قبل اعتباره سهمًا مصرفيًا",
}


# --------------------- Data dictionary ----------------------

NUMERIC_FIELDS = [
    "total_assets_mn",
    "total_equity_mn",
    "net_profit_mn",
    "net_interest_income_mn",
    "operating_income_mn",
    "operating_expenses_mn",
    "impairment_provisions_mn",
    "gross_loans_mn",
    "npl_mn",
    "loan_loss_allowance_mn",
    "customer_deposits_mn",
    "cash_and_cb_balances_mn",
    "investment_securities_mn",
    "total_liabilities_mn",
    "shares_outstanding_mn",
    "eps_egp",
    "dividend_per_share_egp",
    "capital_adequacy_pct",
    "nim_pct",
]

REQUIRED_FIELDS = [
    "ticker",
    "period_end",
    "period_type",
    "basis",
    "total_assets_mn",
    "total_equity_mn",
    "net_profit_mn",
    "operating_income_mn",
    "operating_expenses_mn",
    "gross_loans_mn",
    "customer_deposits_mn",
    "shares_outstanding_mn",
    "source_name",
    "source_date",
]

QUALITY_FIELDS = [
    "total_assets_mn",
    "total_equity_mn",
    "net_profit_mn",
    "operating_income_mn",
    "operating_expenses_mn",
    "gross_loans_mn",
    "customer_deposits_mn",
    "shares_outstanding_mn",
    "source_name",
    "source_date",
]


def empty_financial_template():
    """Return a clean template with one row per bank."""
    rows = []

    for ticker, name in BANKS.items():
        row = {
            "ticker": ticker,
            "bank_name": name,
            "period_end": "",
            "period_type": "FY",
            "basis": "Consolidated",
            "source_name": "",
            "source_url": "",
            "source_date": "",
        }

        for field in NUMERIC_FIELDS:
            row[field] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)


def normalize_ticker(value):
    if pd.isna(value):
        return ""

    ticker = str(value).strip().upper()

    if ticker and not ticker.endswith(".CA"):
        ticker += ".CA"

    return ticker


def parse_numeric(series):
    """
    Convert numeric columns safely.
    Commas are treated as thousands separators.
    Decimal commas must be normalized before upload.
    """
    return pd.to_numeric(
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .replace(
            {
                "": np.nan,
                "nan": np.nan,
                "None": np.nan,
                "N/A": np.nan,
                "NA": np.nan,
                "-": np.nan,
            }
        ),
        errors="coerce",
    )


def load_financial_data(uploaded_file):
    if uploaded_file is None:
        return None

    try:
        if uploaded_file.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        df.columns = [
            str(c).strip().lower().replace(" ", "_")
            for c in df.columns
        ]

        if "ticker" not in df.columns:
            raise ValueError("الملف لازم يحتوي على عمود ticker.")

        df["ticker"] = df["ticker"].apply(normalize_ticker)

        if "bank_name" not in df.columns:
            df["bank_name"] = df["ticker"].map(BANKS).fillna("غير معروف")

        for field in NUMERIC_FIELDS:
            if field not in df.columns:
                df[field] = np.nan
            else:
                df[field] = parse_numeric(df[field])

        text_fields = [
            "period_end",
            "period_type",
            "basis",
            "source_name",
            "source_url",
            "source_date",
        ]

        for field in text_fields:
            if field not in df.columns:
                df[field] = ""

            df[field] = df[field].fillna("").astype(str).str.strip()

        if "period_type" in df.columns:
            df["period_type"] = df["period_type"].replace("", "FY")

        if "basis" in df.columns:
            df["basis"] = df["basis"].replace("", "Consolidated")

        return df

    except Exception as exc:
        st.error(f"تعذر قراءة الملف: {exc}")
        return None


# ------------------------ Price engine -----------------------

@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_price(ticker):
    """
    Best-effort price retrieval.
    Never treats a missing price as zero.
    """
    result = {
        "price": np.nan,
        "price_date": "",
        "currency": "",
        "price_source": "Yahoo Finance",
        "price_status": "غير متاح",
    }

    try:
        history = yf.Ticker(ticker).history(
            period="1mo",
            interval="1d",
            auto_adjust=False,
        )

        if history is None or history.empty:
            result["price_status"] = "لا توجد بيانات سعر"
            return result

        close = history["Close"].dropna()

        if close.empty:
            result["price_status"] = "السعر غير متاح"
            return result

        last_price = float(close.iloc[-1])
        last_date = pd.Timestamp(close.index[-1])

        if last_price <= 0 or not math.isfinite(last_price):
            result["price_status"] = "السعر غير صالح"
            return result

        result["price"] = last_price
        result["price_date"] = last_date.strftime("%Y-%m-%d")
        result["price_status"] = "تم جلب السعر"

        return result

    except Exception as exc:
        result["price_status"] = f"فشل الجلب: {str(exc)[:80]}"
        return result


# ---------------------- Metric engine -----------------------

def safe_divide(numerator, denominator):
    try:
        if pd.isna(numerator) or pd.isna(denominator):
            return np.nan

        if float(denominator) == 0:
            return np.nan

        return float(numerator) / float(denominator)

    except (TypeError, ValueError, ZeroDivisionError):
        return np.nan


def add_financial_metrics(row):
    r = row.copy()

    assets = r.get("total_assets_mn", np.nan)
    equity = r.get("total_equity_mn", np.nan)
    profit = r.get("net_profit_mn", np.nan)
    operating_income = r.get("operating_income_mn", np.nan)
    operating_expenses = r.get("operating_expenses_mn", np.nan)
    loans = r.get("gross_loans_mn", np.nan)
    npl = r.get("npl_mn", np.nan)
    allowance = r.get("loan_loss_allowance_mn", np.nan)
    deposits = r.get("customer_deposits_mn", np.nan)
    shares = r.get("shares_outstanding_mn", np.nan)
    eps = r.get("eps_egp", np.nan)

    if pd.isna(eps) and pd.notna(profit) and pd.notna(shares):
        eps = safe_divide(profit, shares)

    bvps = safe_divide(equity, shares)

    roe = safe_divide(profit, equity)
    roa = safe_divide(profit, assets)

    cost_to_income = safe_divide(
        operating_expenses,
        operating_income,
    )

    npl_ratio = safe_divide(npl, loans)
    coverage_ratio = safe_divide(allowance, npl)
    loan_deposit_ratio = safe_divide(loans, deposits)

    r["eps_calculated"] = eps
    r["bvps"] = bvps

    r["roe_pct"] = roe * 100 if pd.notna(roe) else np.nan
    r["roa_pct"] = roa * 100 if pd.notna(roa) else np.nan

    r["cost_to_income_pct"] = (
        cost_to_income * 100
        if pd.notna(cost_to_income)
        else np.nan
    )

    r["npl_ratio_pct"] = (
        npl_ratio * 100
        if pd.notna(npl_ratio)
        else np.nan
    )

    r["coverage_ratio_pct"] = (
        coverage_ratio * 100
        if pd.notna(coverage_ratio)
        else np.nan
    )

    r["loan_deposit_pct"] = (
        loan_deposit_ratio * 100
        if pd.notna(loan_deposit_ratio)
        else np.nan
    )

    dividend = r.get("dividend_per_share_egp", np.nan)

    r["dividend_yield_pct"] = (
        safe_divide(dividend, r.get("current_price", np.nan)) * 100
        if pd.notna(dividend)
        and pd.notna(r.get("current_price", np.nan))
        else np.nan
    )

    r["pe_ratio"] = (
        safe_divide(r.get("current_price", np.nan), eps)
        if pd.notna(eps) and eps > 0
        else np.nan
    )

    r["pb_ratio"] = (
        safe_divide(r.get("current_price", np.nan), bvps)
        if pd.notna(bvps) and bvps > 0
        else np.nan
    )

    return r


# ---------------------- Valuation engine --------------------

def calculate_valuation(
    row,
    cost_of_equity,
    terminal_growth,
    reference_pe,
    valuation_discount,
):
    """
    Preliminary bank valuation.

    Cost of equity and terminal growth are entered as percentages.
    P/B method uses a simplified justified P/B relationship.
    This is a screening model, not a complete bank DDM.
    """

    price = row.get("current_price", np.nan)
    eps = row.get("eps_calculated", np.nan)
    bvps = row.get("bvps", np.nan)
    roe_pct = row.get("roe_pct", np.nan)

    coe = cost_of_equity / 100
    growth = terminal_growth / 100
    discount = valuation_discount / 100

    methods = []
    fair_values = []

    # P/E method: user-defined reference multiple
    if pd.notna(eps) and eps > 0 and reference_pe > 0:
        pe_fair = float(eps) * float(reference_pe)

        if pe_fair > 0 and math.isfinite(pe_fair):
            methods.append("P/E")
            fair_values.append(pe_fair)

    # Justified P/B method
    roe = roe_pct / 100 if pd.notna(roe_pct) else np.nan

    if (
        pd.notna(bvps)
        and bvps > 0
        and pd.notna(roe)
        and coe > growth
        and roe > growth
    ):
        justified_pb = (roe - growth) / (coe - growth)

        # Avoid extreme valuations from unstable inputs.
        justified_pb = min(max(justified_pb, 0), 3.0)

        pb_fair = bvps * justified_pb

        if pb_fair > 0 and math.isfinite(pb_fair):
            methods.append("Justified P/B")
            fair_values.append(pb_fair)

    if fair_values:
        fair_value = float(np.median(fair_values))
        low_value = float(min(fair_values))
        high_value = float(max(fair_values))

        safe_buy_20 = fair_value * 0.80
        safe_buy_30 = fair_value * 0.70

        discounted_fair_value = fair_value * (1 - discount)

    else:
        fair_value = np.nan
        low_value = np.nan
        high_value = np.nan
        safe_buy_20 = np.nan
        safe_buy_30 = np.nan
        discounted_fair_value = np.nan

    if pd.notna(price) and price > 0 and pd.notna(fair_value):
        upside_pct = (fair_value / price - 1) * 100
        margin_of_safety_pct = (fair_value / price - 1) * 100
        price_vs_fair_pct = (price / fair_value - 1) * 100
    else:
        upside_pct = np.nan
        margin_of_safety_pct = np.nan
        price_vs_fair_pct = np.nan

    return {
        "valuation_methods": ", ".join(methods) if methods else "لا توجد طريقة كافية",
        "fair_value_egp": fair_value,
        "fair_value_low_egp": low_value,
        "fair_value_high_egp": high_value,
        "discounted_fair_value_egp": discounted_fair_value,
        "safe_buy_20_egp": safe_buy_20,
        "safe_buy_30_egp": safe_buy_30,
        "upside_pct": upside_pct,
        "margin_of_safety_pct": margin_of_safety_pct,
        "price_vs_fair_pct": price_vs_fair_pct,
    }


# ----------------------- Data quality -----------------------

def calculate_data_quality(row):
    available = 0
    total = len(QUALITY_FIELDS)

    for field in QUALITY_FIELDS:
        value = row.get(field, np.nan)

        if field in ["source_name", "source_date"]:
            if pd.notna(value) and str(value).strip():
                available += 1
        else:
            if pd.notna(value) and np.isfinite(value):
                available += 1

    score = (available / total) * 100 if total else 0

    source_name = str(row.get("source_name", "")).strip()
    source_date = str(row.get("source_date", "")).strip()

    if not source_name:
        score -= 10

    if not source_date:
        score -= 10

    # Financial fields must be plausible.
    if pd.notna(row.get("total_assets_mn", np.nan)):
        if row["total_assets_mn"] <= 0:
            score -= 20

    if pd.notna(row.get("total_equity_mn", np.nan)):
        if row["total_equity_mn"] <= 0:
            score -= 15

    if pd.notna(row.get("shares_outstanding_mn", np.nan)):
        if row["shares_outstanding_mn"] <= 0:
            score -= 20

    return round(max(0, min(100, score)), 1)


def calculate_preliminary_score(row):
    """
    Transparent screening score.
    It is not a recommendation and is not comparable to a
    complete audited institutional model.
    """
    score = 0.0
    evidence = 0

    roe = row.get("roe_pct", np.nan)
    roa = row.get("roa_pct", np.nan)
    cti = row.get("cost_to_income_pct", np.nan)
    npl = row.get("npl_ratio_pct", np.nan)
    coverage = row.get("coverage_ratio_pct", np.nan)
    pe = row.get("pe_ratio", np.nan)
    pb = row.get("pb_ratio", np.nan)

    # ROE: 20 points
    if pd.notna(roe):
        evidence += 1
        if roe >= 25:
            score += 20
        elif roe >= 18:
            score += 16
        elif roe >= 12:
            score += 12
        elif roe >= 7:
            score += 7
        elif roe > 0:
            score += 3

    # ROA: 10 points
    if pd.notna(roa):
        evidence += 1
        if roa >= 2:
            score += 10
        elif roa >= 1.5:
            score += 8
        elif roa >= 1:
            score += 6
        elif roa > 0:
            score += 3

    # Cost to income: 15 points; lower is better
    if pd.notna(cti) and cti >= 0:
        evidence += 1
        if cti <= 30:
            score += 15
        elif cti <= 40:
            score += 12
        elif cti <= 50:
            score += 9
        elif cti <= 60:
            score += 5

    # NPL ratio: 15 points; lower is better
    if pd.notna(npl) and npl >= 0:
        evidence += 1
        if npl <= 2:
            score += 15
        elif npl <= 4:
            score += 12
        elif npl <= 6:
            score += 8
        elif npl <= 10:
            score += 4

    # Coverage: 10 points
    if pd.notna(coverage) and coverage >= 0:
        evidence += 1
        if coverage >= 150:
            score += 10
        elif coverage >= 100:
            score += 8
        elif coverage >= 70:
            score += 5
        else:
            score += 2

    # Valuation: 20 points
    if pd.notna(pe) and pe > 0:
        evidence += 1
        if pe <= 5:
            score += 10
        elif pe <= 8:
            score += 8
        elif pe <= 12:
            score += 5
        elif pe <= 18:
            score += 2

    if pd.notna(pb) and pb > 0:
        evidence += 1
        if pb <= 0.8:
            score += 10
        elif pb <= 1.2:
            score += 8
        elif pb <= 2:
            score += 5
        elif pb <= 3:
            score += 2

    # Quality adjustment
    quality = row.get("data_quality_pct", 0)

    # Incomplete data should reduce confidence in the score.
    score = score * (0.50 + 0.50 * quality / 100)

    # Lack of core evidence caps the score.
    if evidence < 3:
        score = min(score, 40)

    return round(max(0, min(100, score)), 2)


# ----------------------- Sample template ---------------------

def template_csv_bytes():
    df = empty_financial_template()
    return df.to_csv(index=False).encode("utf-8-sig")


# ------------------------- Sidebar ---------------------------

with st.sidebar:
    st.header("⚙️ إعدادات التحليل")

    st.caption("إعدادات التقييم افتراضات للمحرك وليست حقائق سوقية.")

    cost_of_equity = st.slider(
        "تكلفة حقوق الملكية %",
        min_value=10.0,
        max_value=40.0,
        value=25.0,
        step=0.5,
    )

    terminal_growth = st.slider(
        "معدل النمو طويل الأجل %",
        min_value=0.0,
        max_value=12.0,
        value=8.0,
        step=0.5,
    )

    reference_pe = st.slider(
        "مضاعف الربحية المرجعي P/E",
        min_value=2.0,
        max_value=20.0,
        value=7.0,
        step=0.5,
    )

    valuation_discount = st.slider(
        "خصم تحفظي على القيمة العادلة %",
        min_value=0,
        max_value=40,
        value=20,
        step=5,
    )

    minimum_quality = st.slider(
        "حد جودة البيانات للترتيب %",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
    )

    basis_filter = st.selectbox(
        "أساس القوائم",
        ["Consolidated", "Standalone", "الكل"],
    )

    st.divider()

    st.caption(f"الإصدار {APP_VERSION}")
    st.caption("تحليل مالي فقط — لا توجد مؤشرات فنية.")


# ------------------------- Main tabs -------------------------

tab_dashboard, tab_import, tab_analysis, tab_methodology = st.tabs(
    [
        "📊 لوحة النتائج",
        "📥 البيانات المالية",
        "🏦 تحليل البنوك",
        "📘 المنهجية والمصادر",
    ]
)


# --------------------- Import data tab -----------------------

with tab_import:
    st.subheader("تحميل القوائم المالية")

    st.info(
        """
        ارفع ملف CSV أو Excel يحتوي على القوائم المالية للبنوك.
        يجب أن تكون القيم النقدية بوحدة **مليون جنيه مصري**،
        باستثناء ربحية السهم والتوزيعات للسهم الواحد.
        """
    )

    st.download_button(
        label="⬇️ تنزيل قالب البيانات المالية CSV",
        data=template_csv_bytes(),
        file_name="egx_banks_financial_template.csv",
        mime="text/csv",
    )

    uploaded_file = st.file_uploader(
        "ارفع ملف القوائم المالية",
        type=["csv", "xlsx"],
        help="يمكنك رفع ملف يحتوي على سنة واحدة أو عدة سنوات لكل بنك.",
    )

    if uploaded_file is not None:
        financial_df = load_financial_data(uploaded_file)

        if financial_df is not None:
            st.session_state["financial_df"] = financial_df

            st.success(
                f"تم تحميل {len(financial_df)} سجل مالي."
            )

            st.dataframe(
                financial_df,
                use_container_width=True,
                hide_index=True,
            )

    elif "financial_df" not in st.session_state:
        st.warning(
            "لم يتم تحميل بيانات مالية حتى الآن. "
            "يمكنك تنزيل القالب وملأه من التقارير الرسمية."
        )

    if "financial_df" in st.session_state:
        current_df = st.session_state["financial_df"]

        st.download_button(
            "⬇️ تنزيل البيانات المحملة بعد توحيد الأعمدة",
            data=current_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="egx_banks_loaded_data.csv",
            mime="text/csv",
        )


# ----------------------- Prepare dataset ---------------------

if "financial_df" in st.session_state:
    raw_df = st.session_state["financial_df"].copy()
else:
    raw_df = pd.DataFrame(
        columns=[
            "ticker",
            "bank_name",
            "period_end",
            "period_type",
            "basis",
            "source_name",
            "source_url",
            "source_date",
        ] + NUMERIC_FIELDS
    )


# ---------------------- Analysis pipeline --------------------

analysis_df = pd.DataFrame()

if not raw_df.empty and "ticker" in raw_df.columns:
    work = raw_df.copy()

    work["ticker"] = work["ticker"].apply(normalize_ticker)

    work = work[work["ticker"].astype(str).str.len() > 0].copy()

    if basis_filter != "الكل" and "basis" in work.columns:
        work = work[
            work["basis"].astype(str).str.lower()
            == basis_filter.lower()
        ].copy()

    if not work.empty:
        # Choose the latest period per bank.
        if "period_end" in work.columns:
            work["_period_sort"] = pd.to_datetime(
                work["period_end"],
                errors="coerce",
            )
        else:
            work["_period_sort"] = pd.NaT

        work = work.sort_values(
            ["ticker", "_period_sort"],
            ascending=[True, False],
            na_position="last",
        )

        latest_df = work.drop_duplicates(
            subset=["ticker"],
            keep="first",
        ).copy()

        latest_df = latest_df.drop(columns=["_period_sort"], errors="ignore")

        price_rows = []

        with st.spinner("جاري محاولة جلب أحدث أسعار متاحة..."):
            for ticker in latest_df["ticker"].dropna().unique():
                price_rows.append(
                    {
                        "ticker": ticker,
                        **fetch_market_price(ticker),
                    }
                )

        price_df = pd.DataFrame(price_rows)

        if not price_df.empty:
            latest_df = latest_df.merge(
                price_df,
                on="ticker",
                how="left",
            )
        else:
            latest_df["price"] = np.nan
            latest_df["price_date"] = ""
            latest_df["price_source"] = ""
            latest_df["price_status"] = "غير متاح"

        latest_df["current_price"] = latest_df["price"]

        # Keep a user-supplied price if Yahoo is unavailable.
        if "manual_price_egp" in latest_df.columns:
            manual_price = pd.to_numeric(
                latest_df["manual_price_egp"],
                errors="coerce",
            )

            latest_df["current_price"] = latest_df[
                "current_price"
            ].fillna(manual_price)

        metrics_rows = []

        for _, row in latest_df.iterrows():
            metrics_rows.append(add_financial_metrics(row))

        analysis_df = pd.DataFrame(metrics_rows)

        analysis_df["data_quality_pct"] = analysis_df.apply(
            calculate_data_quality,
            axis=1,
        )

        valuation_rows = []

        for _, row in analysis_df.iterrows():
            valuation_rows.append(
                calculate_valuation(
                    row,
                    cost_of_equity=cost_of_equity,
                    terminal_growth=terminal_growth,
                    reference_pe=reference_pe,
                    valuation_discount=valuation_discount,
                )
            )

        valuation_df = pd.DataFrame(valuation_rows)

        for col in valuation_df.columns:
            analysis_df[col] = valuation_df[col].values

        analysis_df["preliminary_score"] = analysis_df.apply(
            calculate_preliminary_score,
            axis=1,
        )

        analysis_df["ranking_eligible"] = (
            analysis_df["data_quality_pct"] >= minimum_quality
        )

        analysis_df["investment_screen"] = np.select(
            [
                analysis_df["fair_value_egp"].isna(),
                analysis_df["current_price"].isna(),
                analysis_df["current_price"]
                <= analysis_df["safe_buy_30_egp"],
                analysis_df["current_price"]
                <= analysis_df["safe_buy_20_egp"],
                analysis_df["current_price"]
                <= analysis_df["fair_value_egp"],
            ],
            [
                "لا توجد قيمة عادلة كافية",
                "السعر غير متاح",
                "داخل نطاق خصم 30%",
                "داخل نطاق خصم 20%",
                "أقل من القيمة العادلة",
            ],
            default="أعلى من القيمة العادلة",
        )

        # Do not label a stock as attractive if financial data quality
        # is too low.
        analysis_df.loc[
            analysis_df["data_quality_pct"] < minimum_quality,
            "investment_screen",
        ] = "جودة البيانات أقل من الحد المحدد"


# ------------------------- Dashboard -------------------------

with tab_dashboard:
    st.subheader("ملخص السوق المصرفي")

    if analysis_df.empty:
        st.info(
            "ابدأ من تبويب «البيانات المالية»، ونزّل القالب ثم ارفع "
            "القوائم المالية الرسمية حتى يظهر ترتيب البنوك."
        )
    else:
        eligible = analysis_df[
            analysis_df["ranking_eligible"]
        ].copy()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "البنوك المحللة",
            len(analysis_df),
        )

        col2.metric(
            "بنوك اجتازت حد الجودة",
            len(eligible),
        )

        col3.metric(
            "متوسط جودة البيانات",
            f"{analysis_df['data_quality_pct'].mean():.1f}%",
        )

        fair_count = int(
            analysis_df["fair_value_egp"].notna().sum()
        )

        col4.metric(
            "بنوك لها تقييم متاح",
            fair_count,
        )

        st.divider()

        st.markdown("### 🏆 أفضل البنوك وفق درجة الفحص الأولية")

        ranked = analysis_df[
            analysis_df["ranking_eligible"]
        ].sort_values(
            "preliminary_score",
            ascending=False,
        )

        if ranked.empty:
            st.warning(
                "لا توجد بنوك اجتازت حد جودة البيانات الحالي. "
                "راجع القوائم أو خفّض الحد بحذر."
            )
        else:
            display_columns = [
                "ticker",
                "bank_name",
                "current_price",
                "fair_value_egp",
                "safe_buy_20_egp",
                "roe_pct",
                "roa_pct",
                "pe_ratio",
                "pb_ratio",
                "data_quality_pct",
                "preliminary_score",
                "investment_screen",
            ]

            display_columns = [
                c for c in display_columns if c in ranked.columns
            ]

            display_df = ranked[display_columns].copy()

            display_df = display_df.rename(
                columns={
                    "ticker": "الرمز",
                    "bank_name": "البنك",
                    "current_price": "السعر",
                    "fair_value_egp": "القيمة العادلة",
                    "safe_buy_20_egp": "شراء بخصم 20%",
                    "roe_pct": "ROE %",
                    "roa_pct": "ROA %",
                    "pe_ratio": "P/E",
                    "pb_ratio": "P/B",
                    "data_quality_pct": "جودة البيانات %",
                    "preliminary_score": "درجة الفحص",
                    "investment_screen": "حالة التقييم",
                }
            )

            st.dataframe(
                display_df.style.format(
                    {
                        "السعر": "{:.2f}",
                        "القيمة العادلة": "{:.2f}",
                        "شراء بخصم 20%": "{:.2f}",
                        "ROE %": "{:.2f}",
                        "ROA %": "{:.2f}",
                        "P/E": "{:.2f}",
                        "P/B": "{:.2f}",
                        "جودة البيانات %": "{:.1f}",
                        "درجة الفحص": "{:.2f}",
                    },
                    na_rep="—",
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "⬇️ تنزيل ترتيب البنوك CSV",
                data=ranked.to_csv(index=False).encode("utf-8-sig"),
                file_name="egx_banks_ranking.csv",
                mime="text/csv",
            )

        st.caption(
            "الترتيب أداة فرز أولية، وليس توصية شراء أو بيع. "
            "النتيجة تعتمد على جودة البيانات وصحة القوائم."
        )


# ----------------------- Bank analysis -----------------------

with tab_analysis:
    st.subheader("التحليل المالي والتقييم")

    if analysis_df.empty:
        st.info("ارفع ملف القوائم المالية أولًا.")
    else:
        available_tickers = analysis_df["ticker"].dropna().unique().tolist()

        selected_ticker = st.selectbox(
            "اختر البنك",
            available_tickers,
            format_func=lambda x: f"{x} — {BANKS.get(x, x)}",
        )

        selected_rows = analysis_df[
            analysis_df["ticker"] == selected_ticker
        ]

        if not selected_rows.empty:
            row = selected_rows.iloc[0]

            st.markdown(
                f"## {row.get('bank_name', selected_ticker)}"
            )

            m1, m2, m3, m4 = st.columns(4)

            price = row.get("current_price", np.nan)
            fair = row.get("fair_value_egp", np.nan)
            safe20 = row.get("safe_buy_20_egp", np.nan)
            quality = row.get("data_quality_pct", 0)

            m1.metric(
                "السعر المتاح",
                f"{price:.2f} جنيه" if pd.notna(price) else "غير متاح",
            )

            m2.metric(
                "القيمة العادلة",
                f"{fair:.2f} جنيه" if pd.notna(fair) else "غير متاحة",
            )

            m3.metric(
                "شراء بخصم 20%",
                f"{safe20:.2f} جنيه" if pd.notna(safe20) else "غير متاح",
            )

            m4.metric(
                "جودة البيانات",
                f"{quality:.1f}%",
            )

            st.divider()

            left, right = st.columns(2)

            with left:
                st.markdown("### مؤشرات الربحية والكفاءة")

                profitability = {
                    "المؤشر": [
                        "العائد على حقوق الملكية ROE",
                        "العائد على الأصول ROA",
                        "التكلفة إلى الدخل",
                        "صافي القروض إلى الودائع",
                    ],
                    "القيمة": [
                        row.get("roe_pct", np.nan),
                        row.get("roa_pct", np.nan),
                        row.get("cost_to_income_pct", np.nan),
                        row.get("loan_deposit_pct", np.nan),
                    ],
                }

                st.dataframe(
                    pd.DataFrame(profitability).style.format(
                        {"القيمة": "{:.2f}%"},
                        na_rep="غير متاح",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            with right:
                st.markdown("### جودة الأصول والتقييم")

                risk_metrics = {
                    "المؤشر": [
                        "القروض غير المنتظمة NPL",
                        "تغطية القروض غير المنتظمة",
                        "ربحية السهم EPS",
                        "القيمة الدفترية للسهم BVPS",
                        "مضاعف الربحية P/E",
                        "مضاعف القيمة الدفترية P/B",
                    ],
                    "القيمة": [
                        row.get("npl_ratio_pct", np.nan),
                        row.get("coverage_ratio_pct", np.nan),
                        row.get("eps_calculated", np.nan),
                        row.get("bvps", np.nan),
                        row.get("pe_ratio", np.nan),
                        row.get("pb_ratio", np.nan),
                    ],
                }

                st.dataframe(
                    pd.DataFrame(risk_metrics).style.format(
                        {
                            "القيمة": "{:.2f}",
                        },
                        na_rep="غير متاح",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            st.divider()

            st.markdown("### القيمة العادلة ونطاقات الشراء")

            valuation_table = pd.DataFrame(
                [
                    {
                        "البند": "القيمة العادلة المقدرة",
                        "القيمة بالجنيه": row.get("fair_value_egp", np.nan),
                    },
                    {
                        "البند": "أقل تقدير من الطرق المتاحة",
                        "القيمة بالجنيه": row.get("fair_value_low_egp", np.nan),
                    },
                    {
                        "البند": "أعلى تقدير من الطرق المتاحة",
                        "القيمة بالجنيه": row.get("fair_value_high_egp", np.nan),
                    },
                    {
                        "البند": "القيمة بعد الخصم التحفظي",
                        "القيمة بالجنيه": row.get("discounted_fair_value_egp", np.nan),
                    },
                    {
                        "البند": "منطقة شراء بخصم 20%",
                        "القيمة بالجنيه": row.get("safe_buy_20_egp", np.nan),
                    },
                    {
                        "البند": "منطقة شراء بخصم 30%",
                        "القيمة بالجنيه": row.get("safe_buy_30_egp", np.nan),
                    },
                ]
            )

            st.dataframe(
                valuation_table.style.format(
                    {"القيمة بالجنيه": "{:.2f}"},
                    na_rep="غير متاح",
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### معلومات مصدر البيانات")

            source_info = pd.DataFrame(
                [
                    {
                        "البند": "مصدر القوائم",
                        "القيمة": row.get("source_name", ""),
                    },
                    {
                        "البند": "رابط المصدر",
                        "القيمة": row.get("source_url", ""),
                    },
                    {
                        "البند": "تاريخ المصدر",
                        "القيمة": row.get("source_date", ""),
                    },
                    {
                        "البند": "الفترة المالية",
                        "القيمة": row.get("period_end", ""),
                    },
                    {
                        "البند": "نوع القوائم",
                        "القيمة": row.get("basis", ""),
                    },
                    {
                        "البند": "تاريخ السعر",
                        "القيمة": row.get("price_date", ""),
                    },
                    {
                        "البند": "حالة السعر",
                        "القيمة": row.get("price_status", ""),
                    },
                    {
                        "البند": "طرق التقييم",
                        "القيمة": row.get("valuation_methods", ""),
                    },
                ]
            )

            st.dataframe(
                source_info,
                use_container_width=True,
                hide_index=True,
            )

            if quality < minimum_quality:
                st.error(
                    "جودة البيانات أقل من الحد المحدد؛ "
                    "لا تعتمد على القيمة العادلة قبل استكمال البيانات."
                )
            else:
                st.warning(
                    "هذه قيمة تقديرية وليست سعرًا مضمونًا. "
                    "راجع القوائم المدققة، وجودة الأرباح، ورأس المال، "
                    "والمخصصات، وأحدث إفصاحات البنك."
                )


# ---------------------- Methodology tab ----------------------

with tab_methodology:
    st.subheader("منهجية المحرك وحدود الاستخدام")

    st.markdown(
        """
        ### 1. نطاق المشروع

        المحرك مخصص لتحليل البنوك المصرية ماليًا فقط.
        لا يستخدم RSI أو MACD أو المتوسطات المتحركة أو أي مؤشرات فنية.

        ### 2. المؤشرات المالية

        - **ROE:** صافي الربح ÷ حقوق الملكية.
        - **ROA:** صافي الربح ÷ إجمالي الأصول.
        - **Cost-to-Income:** مصروفات التشغيل ÷ دخل التشغيل.
        - **NPL Ratio:** القروض غير المنتظمة ÷ إجمالي القروض.
        - **Coverage Ratio:** مخصصات خسائر القروض ÷ القروض غير المنتظمة.
        - **Loan-to-Deposit:** إجمالي القروض ÷ ودائع العملاء.
        - **EPS:** ربحية السهم.
        - **BVPS:** حقوق الملكية ÷ عدد الأسهم.

        ### 3. التقييم

        **طريقة P/E:**
        ربحية السهم × مضاعف الربحية المرجعي الذي يحدده المستخدم.

        **طريقة Justified P/B:**
        يتم استخدام علاقة مبسطة بين العائد على حقوق الملكية،
        وتكلفة حقوق الملكية، والنمو طويل الأجل.

        مضاعف القيمة الدفترية المبرر =
        (ROE - Growth) ÷ (Cost of Equity - Growth).

        ثم يضرب الناتج في القيمة الدفترية للسهم.

        النموذج المبسط لا يغني عن نموذج توزيعات نقدية خاص بالبنوك
        أو تحليل رأس المال الرقابي والمخاطر والسيولة.

        ### 4. جودة البيانات

        جودة البيانات تقيس اكتمال الحقول الأساسية ووجود معلومات المصدر
        والتاريخ. وهي لا تثبت أن الرقم صحيح أو مدقق.

        ### 5. قواعد إدخال البيانات

        - استخدم نفس العملة والوحدة لكل القوائم.
        - القيم النقدية بالمليون جنيه.
        - عدد الأسهم بالمليون سهم.
        - EPS والتوزيعات بالجنيه للسهم.
        - النسب مثل كفاية رأس المال وNIM تُدخل كنسب مئوية.
        - لا تخلط القوائم المجمعة والمستقلة في مقارنة واحدة.
        - استخدم أحدث فترة متاحة لكل بنك مع الاحتفاظ بتاريخها.
        - لا تدخل قيمة صفر بدلًا من البيانات غير المتاحة.
        - سجّل رابط المصدر وتاريخ الحصول على البيانات.

        ### 6. المصادر المقترحة

        - البورصة المصرية: الإفصاحات والبيانات الرسمية.
        - البنك المركزي المصري: التقارير المصرفية والإحصاءات.
        - علاقات المستثمرين بالمصرف: القوائم السنوية والمرحلية.
        - Yahoo Finance: مصدر مساعد للأسعار عند توافرها فقط.

        ### 7. تحذير مهم

        هذه النسخة هي أساس قابل للتطوير وليست نظامًا مؤسسيًا مكتملًا.
        درجات الفحص والقيم العادلة تعتمد على جودة المدخلات والافتراضات.
        لا تعتبر نتيجة المحرك وحدها توصية بالشراء أو البيع.
        """
    )

    st.markdown("#### روابط مصادر البيانات")

    st.markdown(
        "- البورصة المصرية: https://www.egx.com.eg/\n"
        "- البنك المركزي المصري: https://www.cbe.org.eg/\n"
        "- علاقات المستثمرين في CIB: https://www.cibeg.com/ar/investor-relations"
    )

    st.caption(
        f"آخر تشغيل للواجهة: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
