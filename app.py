# -*- coding: utf-8 -*-
"""
EGX BANKS FINANCIAL INTELLIGENCE PRO
Automatic Data Engine - Financial Analysis Only

Features:
- Automatic market-data retrieval via Yahoo Finance / yfinance
- Automatic financial-statement retrieval when available
- Official bank website discovery
- Sector-specific banking metrics
- P/B, P/E and simplified residual-income valuation
- Margin-of-safety buy zones
- Data coverage and confidence assessment
- Arabic Streamlit dashboard
- No manual CSV/XLSX upload required

IMPORTANT:
Financial statement availability for EGX stocks varies by provider.
Unavailable values remain missing; they are never fabricated.
"""

import re
import time
import math
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "EGX Banks Financial Intelligence PRO"
APP_VERSION = "1.0.0"

REQUEST_TIMEOUT = 12
MAX_WORKERS = 5
CACHE_TTL_SECONDS = 1800

RISK_FREE_RATE = 0.18
COST_OF_EQUITY = 0.24

# These are scenario assumptions, not forecasts.
DEFAULT_GROWTH_BASE = 0.12
DEFAULT_GROWTH_LOW = 0.05
DEFAULT_GROWTH_HIGH = 0.18

MARGIN_EXCELLENT = 0.30
MARGIN_STRONG = 0.20
MARGIN_ACCEPTABLE = 0.10

MIN_DATA_CONFIDENCE = 35

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("EGX_BANKS")


# ============================================================
# BANK UNIVERSE
# ============================================================

# The symbols below are candidates, not a guarantee of current
# listing status or Yahoo availability. The app reports failures.
BANKS = [
    {
        "symbol": "COMI.CA",
        "name_ar": "البنك التجاري الدولي - مصر",
        "name_en": "Commercial International Bank Egypt",
        "website": "https://www.cibeg.com/",
    },
    {
        "symbol": "HDBK.CA",
        "name_ar": "بنك التعمير والإسكان",
        "name_en": "Housing and Development Bank",
        "website": "https://www.hdb-egy.com/",
    },
    {
        "symbol": "ADIB.CA",
        "name_ar": "مصرف أبوظبي الإسلامي - مصر",
        "name_en": "Abu Dhabi Islamic Bank Egypt",
        "website": "https://www.adib.eg/",
    },
    {
        "symbol": "CIEB.CA",
        "name_ar": "بنك كريدي أجريكول مصر",
        "name_en": "Credit Agricole Egypt",
        "website": "https://www.ca-egypt.com/",
    },
    {
        "symbol": "QNBA.CA",
        "name_ar": "بنك قطر الوطني الأهلي",
        "name_en": "QNB Alahli",
        "website": "https://www.qnbalahli.com/",
    },
    {
        "symbol": "FAIT.CA",
        "name_ar": "بنك فيصل الإسلامي المصري",
        "name_en": "Faisal Islamic Bank of Egypt",
        "website": "https://www.faisalbank.com.eg/",
    },
    {
        "symbol": "EXPA.CA",
        "name_ar": "البنك المصري لتنمية الصادرات",
        "name_en": "Export Development Bank of Egypt",
        "website": "https://www.ebank.com.eg/",
    },
    {
        "symbol": "EGBE.CA",
        "name_ar": "البنك المصري الخليجي",
        "name_en": "Egyptian Gulf Bank",
        "website": "https://www.eg-bank.com/",
    },
    {
        "symbol": "SAUD.CA",
        "name_ar": "البنك السعودي المصري",
        "name_en": "SAIB Bank",
        "website": "https://www.saib.com.eg/",
    },
    {
        "symbol": "CANA.CA",
        "name_ar": "بنك قناة السويس",
        "name_en": "Suez Canal Bank",
        "website": "https://www.scbank.com.eg/",
    },
]

# Explicitly add/remove candidates here only after checking the EGX
# listing directory. The list should not be treated as the full EGX
# universe or as an official live listing feed.


# ============================================================
# GENERAL UTILITIES
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def safe_float(value):
    """Convert a value to a finite float, otherwise NaN."""
    try:
        if value is None:
            return np.nan

        if isinstance(value, (list, tuple, dict)):
            return np.nan

        x = float(value)

        if not np.isfinite(x):
            return np.nan

        return x
    except (TypeError, ValueError, OverflowError):
        return np.nan


def first_valid(*values):
    for value in values:
        x = safe_float(value)
        if not pd.isna(x):
            return x
    return np.nan


def safe_divide(numerator, denominator):
    n = safe_float(numerator)
    d = safe_float(denominator)

    if pd.isna(n) or pd.isna(d) or d == 0:
        return np.nan

    return n / d


def clean_text(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def fmt_number(value, decimals=2):
    x = safe_float(value)

    if pd.isna(x):
        return "غير متاح"

    return f"{x:,.{decimals}f}"


def fmt_percent(value, decimals=1):
    x = safe_float(value)

    if pd.isna(x):
        return "غير متاح"

    return f"{x * 100:.{decimals}f}%"


def fmt_price(value):
    x = safe_float(value)

    if pd.isna(x):
        return "غير متاح"

    return f"{x:,.2f}"


def get_last_numeric_value(df, row_candidates):
    """
    Search financial statement rows using case-insensitive
    keyword matching and return the latest available value.

    The provider's row labels and column dates are preserved
    for transparency.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return np.nan

    try:
        columns = list(df.columns)

        # Prefer the most recent period, if the columns are dates.
        try:
            columns = sorted(columns, reverse=True)
        except Exception:
            pass

        for keyword in row_candidates:
            for idx in df.index:
                label = str(idx).lower()

                if keyword.lower() in label:
                    row = df.loc[idx]

                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]

                    for col in columns:
                        if col not in row.index:
                            continue

                        value = safe_float(row[col])

                        if not pd.isna(value):
                            return value

        return np.nan
    except Exception:
        return np.nan


def safe_get_info(ticker):
    try:
        return ticker.info or {}
    except Exception:
        return {}


def safe_get_statement(ticker, statement_name):
    """
    yfinance changes and provider availability may affect
    statement retrieval. Return an empty frame on failure.
    """
    try:
        statement = getattr(ticker, statement_name)

        if isinstance(statement, pd.DataFrame):
            return statement

    except Exception as exc:
        LOGGER.info(
            "Statement retrieval failed for %s: %s",
            statement_name,
            exc,
        )

    return pd.DataFrame()


# ============================================================
# OFFICIAL WEBSITE DISCOVERY
# ============================================================

def discover_official_financial_pages(base_url):
    """
    Inspect the supplied official website for links whose text
    or URL suggests investor relations or financial reports.

    This is discovery only. It does not guarantee that PDFs can
    be parsed or that the documents contain machine-readable data.
    """
    result = {
        "website_status": "لم يتم الفحص",
        "investor_links": [],
        "report_links": [],
        "website_checked_at": now_utc(),
    }

    if not base_url:
        result["website_status"] = "لا يوجد رابط رسمي"
        return result

    try:
        response = requests.get(
            base_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code >= 400:
            result["website_status"] = (
                f"تعذر الوصول: HTTP {response.status_code}"
            )
            return result

        result["website_status"] = "تم الوصول للموقع"

        if BeautifulSoup is None:
            result["website_status"] = (
                "تم الوصول؛ مكتبة BeautifulSoup غير متاحة"
            )
            return result

        soup = BeautifulSoup(response.text, "html.parser")

        investor_links = []
        report_links = []

        investor_terms = [
            "investor",
            "investor relations",
            "financial information",
            "financial results",
            "financial statements",
            "المستثمرين",
            "علاقات المستثمرين",
            "القوائم المالية",
        ]

        report_terms = [
            "annual report",
            "financial statement",
            "financial report",
            "quarterly report",
            "annual financial",
            "التقرير السنوي",
            "القوائم المالية",
            "النتائج المالية",
        ]

        for anchor in soup.find_all("a", href=True):
            text = clean_text(anchor.get_text(" ", strip=True))
            href = urljoin(base_url, anchor["href"])
            combined = f"{text} {href}".lower()

            if not href.startswith(("http://", "https://")):
                continue

            if urlparse(href).netloc != urlparse(base_url).netloc:
                continue

            if any(term in combined for term in investor_terms):
                investor_links.append({
                    "text": text or "صفحة مرتبطة بالمستثمرين",
                    "url": href,
                })

            if (
                any(term in combined for term in report_terms)
                or href.lower().endswith(".pdf")
            ):
                report_links.append({
                    "text": text or "تقرير محتمل",
                    "url": href,
                })

        # Deduplicate while preserving order.
        def dedupe(items):
            seen = set()
            output = []

            for item in items:
                url = item["url"]

                if url not in seen:
                    seen.add(url)
                    output.append(item)

            return output

        result["investor_links"] = dedupe(investor_links)[:15]
        result["report_links"] = dedupe(report_links)[:25]

    except Exception as exc:
        result["website_status"] = (
            f"تعذر فحص الموقع: {type(exc).__name__}"
        )

    return result


# ============================================================
# AUTOMATIC MARKET AND FUNDAMENTAL DATA RETRIEVAL
# ============================================================

def retrieve_bank_data(bank):
    """
    Attempt automatic retrieval of:
    - Quote / market information
    - Financial statements
    - Balance sheet
    - Cash flow
    - Official website report links

    Missing data is preserved as NaN.
    """
    symbol = bank["symbol"]

    output = {
        **bank,
        "retrieved_at": now_utc(),
        "price_source": "Yahoo Finance / yfinance",
        "fundamental_source": "Yahoo Finance / yfinance",
        "data_status": "بدأ الجلب",
        "market_status": "غير متاح",
        "statement_status": "غير متاح",
        "website_status": "لم يتم الفحص",
        "price": np.nan,
        "previous_close": np.nan,
        "market_cap": np.nan,
        "shares_outstanding": np.nan,
        "currency": None,
        "trailing_pe": np.nan,
        "forward_pe": np.nan,
        "price_to_book": np.nan,
        "eps": np.nan,
        "book_value_per_share": np.nan,
        "dividend_yield": np.nan,
        "payout_ratio": np.nan,
        "roe": np.nan,
        "roa": np.nan,
        "net_income": np.nan,
        "total_revenue": np.nan,
        "total_assets": np.nan,
        "total_equity": np.nan,
        "interest_income": np.nan,
        "interest_expense": np.nan,
        "net_interest_income": np.nan,
        "gross_loans": np.nan,
        "customer_deposits": np.nan,
        "npl_ratio": np.nan,
        "capital_adequacy": np.nan,
        "source_notes": [],
        "investor_links": [],
        "report_links": [],
    }

    try:
        ticker = yf.Ticker(symbol)
        info = safe_get_info(ticker)

        # ----------------------------------------------------
        # Market data
        # ----------------------------------------------------
        price = first_valid(
            info.get("regularMarketPrice"),
            info.get("currentPrice"),
            info.get("navPrice"),
        )

        previous_close = first_valid(
            info.get("regularMarketPreviousClose"),
            info.get("previousClose"),
        )

        # If info has no current price, try recent daily history.
        if pd.isna(price):
            try:
                hist = ticker.history(
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                )

                if hist is not None and not hist.empty:
                    close_values = hist["Close"].dropna()

                    if not close_values.empty:
                        price = safe_float(close_values.iloc[-1])

                        output["source_notes"].append(
                            "السعر مأخوذ من آخر إغلاق متاح؛ "
                            "قد لا يكون سعرًا لحظيًا."
                        )
            except Exception as exc:
                LOGGER.info(
                    "History failed for %s: %s",
                    symbol,
                    exc,
                )

        output["price"] = price
        output["previous_close"] = previous_close
        output["market_cap"] = safe_float(info.get("marketCap"))
        output["shares_outstanding"] = safe_float(
            info.get("sharesOutstanding")
        )
        output["currency"] = info.get("currency")
        output["trailing_pe"] = safe_float(
            info.get("trailingPE")
        )
        output["forward_pe"] = safe_float(
            info.get("forwardPE")
        )
        output["price_to_book"] = safe_float(
            info.get("priceToBook")
        )
        output["eps"] = safe_float(info.get("trailingEps"))
        output["book_value_per_share"] = safe_float(
            info.get("bookValue")
        )
        output["dividend_yield"] = safe_float(
            info.get("dividendYield")
        )
        output["payout_ratio"] = safe_float(
            info.get("payoutRatio")
        )
        output["roe"] = safe_float(info.get("returnOnEquity"))
        output["roa"] = safe_float(info.get("returnOnAssets"))

        if not pd.isna(price):
            output["market_status"] = "تم جلب سعر"
        else:
            output["market_status"] = (
                "لم يتوفر سعر من المصدر"
            )

        # ----------------------------------------------------
        # Financial statements
        # ----------------------------------------------------
        financials = safe_get_statement(ticker, "financials")
        balance = safe_get_statement(ticker, "balance_sheet")
        cashflow = safe_get_statement(ticker, "cashflow")

        # Some yfinance versions expose quarterly statements.
        if financials.empty:
            financials = safe_get_statement(
                ticker,
                "quarterly_financials",
            )

        if balance.empty:
            balance = safe_get_statement(
                ticker,
                "quarterly_balance_sheet",
            )

        if cashflow.empty:
            cashflow = safe_get_statement(
                ticker,
                "quarterly_cashflow",
            )

        output["total_revenue"] = get_last_numeric_value(
            financials,
            [
                "total revenue",
                "operating revenue",
            ],
        )

        output["net_income"] = get_last_numeric_value(
            financials,
            [
                "net income",
                "net income common stockholders",
            ],
        )

        output["interest_income"] = get_last_numeric_value(
            financials,
            [
                "interest income",
            ],
        )

        output["interest_expense"] = get_last_numeric_value(
            financials,
            [
                "interest expense",
            ],
        )

        output["net_interest_income"] = get_last_numeric_value(
            financials,
            [
                "net interest income",
            ],
        )

        output["total_assets"] = get_last_numeric_value(
            balance,
            [
                "total assets",
            ],
        )

        output["total_equity"] = get_last_numeric_value(
            balance,
            [
                "stockholders equity",
                "total stockholder equity",
                "total equity gross minority interest",
                "total equity",
            ],
        )

        # Search for loans and deposits only if provider labels
        # are available. Definitions can differ across providers.
        output["gross_loans"] = get_last_numeric_value(
            balance,
            [
                "loans and advances",
                "loans receivable",
                "loans",
                "total loans",
            ],
        )

        output["customer_deposits"] = get_last_numeric_value(
            balance,
            [
                "customer deposits",
                "deposits from customers",
                "total deposits",
                "deposits",
            ],
        )

        has_statements = (
            not financials.empty
            or not balance.empty
            or not cashflow.empty
        )

        output["statement_status"] = (
            "تم استرجاع قوائم"
            if has_statements
            else "القوائم غير متاحة من المصدر"
        )

        if not has_statements:
            output["source_notes"].append(
                "لم تتوفر قوائم مالية منظمة من Yahoo Finance."
            )

        # If the provider has no statement-derived equity,
        # do not replace it silently with an estimate.
        if pd.isna(output["total_equity"]):
            output["source_notes"].append(
                "حقوق الملكية غير متاحة من القوائم المسترجعة."
            )

        # ----------------------------------------------------
        # Official website discovery
        # ----------------------------------------------------
        website_data = discover_official_financial_pages(
            bank.get("website")
        )

        output["website_status"] = website_data[
            "website_status"
        ]
        output["investor_links"] = website_data[
            "investor_links"
        ]
        output["report_links"] = website_data[
            "report_links"
        ]

        output["source_notes"].append(
            "فحص الموقع الرسمي يبحث عن روابط تقارير؛ "
            "ولا يعني أن الأرقام استخرجت من هذه التقارير."
        )

        output["data_status"] = "اكتمل الجلب الأولي"

    except Exception as exc:
        output["data_status"] = (
            f"تعذر الجلب: {type(exc).__name__}"
        )
        output["source_notes"].append(
            f"تفاصيل الخطأ: {clean_text(exc)[:180]}"
        )

    # --------------------------------------------------------
    # Derived metrics
    # --------------------------------------------------------
    output["calculated_bvps"] = np.nan
    output["calculated_roe"] = np.nan
    output["calculated_roa"] = np.nan

    shares = safe_float(output["shares_outstanding"])
    equity = safe_float(output["total_equity"])
    net_income = safe_float(output["net_income"])
    assets = safe_float(output["total_assets"])

    if not pd.isna(equity) and not pd.isna(shares) and shares > 0:
        output["calculated_bvps"] = equity / shares

    if not pd.isna(net_income) and not pd.isna(equity) and equity > 0:
        output["calculated_roe"] = net_income / equity

    if not pd.isna(net_income) and not pd.isna(assets) and assets > 0:
        output["calculated_roa"] = net_income / assets

    # Use provider values when available; calculated values are
    # fallback values and should be interpreted cautiously.
    output["roe_final"] = first_valid(
        output["roe"],
        output["calculated_roe"],
    )

    output["roa_final"] = first_valid(
        output["roa"],
        output["calculated_roa"],
    )

    output["bvps_final"] = first_valid(
        output["book_value_per_share"],
        output["calculated_bvps"],
    )

    return output


# ============================================================
# BANK-SPECIFIC VALUATION ENGINE
# ============================================================

def valuation_engine(row, cost_of_equity=COST_OF_EQUITY):
    """
    Bank valuation approach:
    1. P/B valuation anchored to book value per share.
    2. Residual-income-style estimate when BVPS and ROE are usable.
    3. P/E-based cross-check when EPS is positive.
    4. Conservative blend where enough inputs exist.

    This is an analytical estimate, not a guaranteed fair value.
    Banks require consistent units, reporting periods, and
    preferably audited financial statements.
    """
    price = safe_float(row.get("price"))
    bvps = safe_float(row.get("bvps_final"))
    eps = safe_float(row.get("eps"))
    roe = safe_float(row.get("roe_final"))
    pb = safe_float(row.get("price_to_book"))
    pe = safe_float(row.get("trailing_pe"))

    methods = []
    fair_values = []
    method_weights = []

    # --------------------------------------------------------
    # Method 1: P/B framework
    # --------------------------------------------------------
    # A bank's justified P/B depends on sustainable ROE and
    # required return. The formula is only used when the inputs
    # are sensible and comparable.
    if (
        not pd.isna(bvps)
        and bvps > 0
        and not pd.isna(roe)
        and 0 < cost_of_equity < 1
    ):
        sustainable_roe = min(max(roe, -0.20), 0.60)

        if sustainable_roe > 0:
            justified_pb = (
                sustainable_roe / cost_of_equity
            )

            # Guard against extreme values caused by noisy data.
            justified_pb = min(max(justified_pb, 0.35), 2.50)

            fair_pb = bvps * justified_pb

            if np.isfinite(fair_pb) and fair_pb > 0:
                fair_values.append(fair_pb)
                method_weights.append(0.50)
                methods.append("P/B مبرر حسب العائد على حقوق الملكية")

    # --------------------------------------------------------
    # Method 2: Simplified residual-income framework
    # --------------------------------------------------------
    # This is a one-stage approximation, not a full DCF.
    # It assumes sustainable ROE and stable long-run growth.
    growth = DEFAULT_GROWTH_BASE

    if (
        not pd.isna(bvps)
        and bvps > 0
        and not pd.isna(roe)
        and roe > growth
        and cost_of_equity > growth
    ):
        residual_income = (roe - cost_of_equity) * bvps

        residual_value = (
            bvps
            + residual_income / (cost_of_equity - growth)
        )

        if (
            np.isfinite(residual_value)
            and residual_value > 0
            and residual_value < bvps * 5
        ):
            fair_values.append(residual_value)
            method_weights.append(0.35)
            methods.append("نموذج دخل متبقٍ مبسط")

    # --------------------------------------------------------
    # Method 3: P/E cross-check
    # --------------------------------------------------------
    if not pd.isna(eps) and eps > 0:
        # The multiple is a broad screening assumption.
        # It is not a market-derived peer multiple.
        reference_pe = 7.0

        fair_pe = eps * reference_pe

        if np.isfinite(fair_pe) and fair_pe > 0:
            fair_values.append(fair_pe)
            method_weights.append(0.15)
            methods.append("مضاعف ربحية افتراضي للفحص")

    # --------------------------------------------------------
    # Combine methods
    # --------------------------------------------------------
    fair_value = np.nan
    fair_low = np.nan
    fair_high = np.nan

    if fair_values:
        weights = np.array(method_weights, dtype=float)
        values = np.array(fair_values, dtype=float)

        weights = weights / weights.sum()
        fair_value = float(np.sum(values * weights))

        # Range is dispersion between available model outputs.
        fair_low = float(np.min(values))
        fair_high = float(np.max(values))

    # Do not present the valuation as reliable if the inputs
    # are insufficient or the model dispersion is extreme.
    valuation_confidence = "منخفضة"

    if len(fair_values) >= 2:
        if fair_value > 0:
            dispersion = (
                (fair_high - fair_low) / fair_value
            )

            if dispersion <= 0.30:
                valuation_confidence = "متوسطة"
            elif dispersion <= 0.60:
                valuation_confidence = "منخفضة"
            else:
                valuation_confidence = "ضعيفة جدًا"

    elif len(fair_values) == 1:
        valuation_confidence = "منخفضة جدًا"

    # Margin-of-safety buy zones.
    buy_30 = fair_value * (1 - MARGIN_EXCELLENT) if not pd.isna(
        fair_value
    ) else np.nan

    buy_20 = fair_value * (1 - MARGIN_STRONG) if not pd.isna(
        fair_value
    ) else np.nan

    buy_10 = fair_value * (1 - MARGIN_ACCEPTABLE) if not pd.isna(
        fair_value
    ) else np.nan

    upside = np.nan

    if (
        not pd.isna(price)
        and price > 0
        and not pd.isna(fair_value)
    ):
        upside = fair_value / price - 1

    return {
        "fair_value": fair_value,
        "fair_value_low": fair_low,
        "fair_value_high": fair_high,
        "buy_zone_30": buy_30,
        "buy_zone_20": buy_20,
        "buy_zone_10": buy_10,
        "upside_to_fair_value": upside,
        "valuation_methods": "، ".join(methods) if methods else "غير كافٍ",
        "valuation_confidence": valuation_confidence,
    }


# ============================================================
# SCENARIO ENGINE
# ============================================================

def scenario_engine(row):
    """
    Three-year scenario estimates based on current available EPS
    or book value per share. Growth assumptions are user-adjustable
    in the UI and are not predictions.
    """
    eps = safe_float(row.get("eps"))
    bvps = safe_float(row.get("bvps_final"))

    g_low = DEFAULT_GROWTH_LOW
    g_base = DEFAULT_GROWTH_BASE
    g_high = DEFAULT_GROWTH_HIGH

    result = {
        "target_3y_conservative": np.nan,
        "target_3y_base": np.nan,
        "target_3y_optimistic": np.nan,
        "scenario_basis": "غير متاح",
    }

    # The scenario targets are indicative multiples of a growing
    # earnings/book-value proxy. They are not price predictions.
    if not pd.isna(eps) and eps > 0:
        base = eps * ((1 + g_base) ** 3) * 7.0
        low = eps * ((1 + g_low) ** 3) * 6.0
        high = eps * ((1 + g_high) ** 3) * 9.0

        result.update({
            "target_3y_conservative": low,
            "target_3y_base": base,
            "target_3y_optimistic": high,
            "scenario_basis": "ربحية السهم ومضاعفات افتراضية",
        })

    elif not pd.isna(bvps) and bvps > 0:
        # This is a book-value growth proxy, not an equity valuation.
        result.update({
            "target_3y_conservative": bvps * (1 + g_low) ** 3,
            "target_3y_base": bvps * (1 + g_base) ** 3,
            "target_3y_optimistic": bvps * (1 + g_high) ** 3,
            "scenario_basis": "نمو افتراضي للقيمة الدفترية فقط",
        })

    return result


# ============================================================
# DATA QUALITY AND SCORING
# ============================================================

def calculate_data_quality(row):
    """
    Completeness score based on availability of important inputs.
    It does not measure whether the source is audited or accurate.
    """
    checks = {
        "price": not pd.isna(safe_float(row.get("price"))),
        "EPS": not pd.isna(safe_float(row.get("eps"))),
        "BVPS": not pd.isna(safe_float(row.get("bvps_final"))),
        "ROE": not pd.isna(safe_float(row.get("roe_final"))),
        "ROA": not pd.isna(safe_float(row.get("roa_final"))),
        "Net income": not pd.isna(safe_float(row.get("net_income"))),
        "Total equity": not pd.isna(safe_float(row.get("total_equity"))),
        "Total assets": not pd.isna(safe_float(row.get("total_assets"))),
        "P/B": not pd.isna(safe_float(row.get("price_to_book"))),
        "P/E": not pd.isna(safe_float(row.get("trailing_pe"))),
    }

    score = 100 * sum(checks.values()) / len(checks)

    return round(score, 1), checks


def financial_score(row):
    """
    Transparent preliminary bank score.
    Missing metrics do not receive a zero score; the score is
    normalized over the available metrics and confidence is shown
    separately.
    """
    components = []

    roe = safe_float(row.get("roe_final"))
    roa = safe_float(row.get("roa_final"))
    eps = safe_float(row.get("eps"))
    bvps = safe_float(row.get("bvps_final"))
    net_income = safe_float(row.get("net_income"))
    equity = safe_float(row.get("total_equity"))
    assets = safe_float(row.get("total_assets"))
    price = safe_float(row.get("price"))
    fair_value = safe_float(row.get("fair_value"))

    # ROE: 25 points
    if not pd.isna(roe):
        if roe >= 0.25:
            s = 25
        elif roe >= 0.18:
            s = 21
        elif roe >= 0.12:
            s = 17
        elif roe >= 0.08:
            s = 12
        elif roe >= 0:
            s = 6
        else:
            s = 0

        components.append((s, 25))

    # ROA: 15 points
    if not pd.isna(roa):
        if roa >= 0.025:
            s = 15
        elif roa >= 0.018:
            s = 12
        elif roa >= 0.012:
            s = 9
        elif roa >= 0.005:
            s = 5
        elif roa >= 0:
            s = 2
        else:
            s = 0

        components.append((s, 15))

    # Earnings: 15 points
    if not pd.isna(eps):
        components.append((15 if eps > 0 else 0, 15))

    # Equity: 15 points
    if not pd.isna(equity):
        components.append((15 if equity > 0 else 0, 15))

    # Assets: 10 points
    if not pd.isna(assets):
        components.append((10 if assets > 0 else 0, 10))

    # Profitability: 10 points
    if not pd.isna(net_income):
        components.append((10 if net_income > 0 else 0, 10))

    # Valuation relative to the model estimate: 10 points
    if (
        not pd.isna(price)
        and price > 0
        and not pd.isna(fair_value)
        and fair_value > 0
    ):
        upside = fair_value / price - 1

        if upside >= 0.30:
            s = 10
        elif upside >= 0.15:
            s = 8
        elif upside >= 0:
            s = 6
        elif upside >= -0.15:
            s = 3
        else:
            s = 0

        components.append((s, 10))

    if not components:
        return np.nan

    available_max = sum(weight for _, weight in components)
    earned = sum(value for value, _ in components)

    return round(100 * earned / available_max, 1)


def score_label(score):
    if pd.isna(safe_float(score)):
        return "بيانات غير كافية"

    if score >= 80:
        return "قوي جدًا"
    if score >= 70:
        return "قوي"
    if score >= 55:
        return "متوسط"
    if score >= 40:
        return "ضعيف"
    return "ضعيف جدًا"


def analyze_bank_record(record, cost_of_equity):
    row = dict(record)

    valuation = valuation_engine(
        row,
        cost_of_equity=cost_of_equity,
    )
    row.update(valuation)

    scenarios = scenario_engine(row)
    row.update(scenarios)

    quality, quality_checks = calculate_data_quality(row)

    row["data_quality"] = quality
    row["quality_checks"] = quality_checks

    row["financial_score"] = financial_score(row)
    row["financial_grade"] = score_label(row["financial_score"])

    row["analysis_status"] = (
        "تحليل أولي"
        if quality >= MIN_DATA_CONFIDENCE
        else "بيانات غير كافية"
    )

    return row


# ============================================================
# LOAD / CACHE
# ============================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_all_banks_cached(bank_definitions, cost_of_equity):
    records = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(retrieve_bank_data, bank): bank
            for bank in bank_definitions
        }

        for future in as_completed(future_map):
            bank = future_map[future]

            try:
                records.append(future.result())
            except Exception as exc:
                LOGGER.exception(
                    "Unexpected retrieval error for %s",
                    bank["symbol"],
                )

                records.append({
                    **bank,
                    "retrieved_at": now_utc(),
                    "data_status": f"خطأ: {type(exc).__name__}",
                    "price": np.nan,
                    "source_notes": [clean_text(exc)],
                })

    analyzed = [
        analyze_bank_record(
            record,
            cost_of_equity=cost_of_equity,
        )
        for record in records
    ]

    df = pd.DataFrame(analyzed)

    if "financial_score" in df.columns:
        df = df.sort_values(
            by=["financial_score", "data_quality"],
            ascending=[False, False],
            na_position="last",
        )

    return df


# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: Arial, Tahoma, sans-serif;
    }

    .main-title {
        font-size: 30px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 6px;
    }

    .subtitle {
        font-size: 15px;
        text-align: center;
        opacity: 0.80;
        margin-bottom: 22px;
    }

    .info-box {
        border: 1px solid rgba(128,128,128,.30);
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0 18px 0;
    }

    .small-note {
        font-size: 12px;
        opacity: .78;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.22);
        padding: 12px;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🏦 EGX Banks Financial Intelligence PRO</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'محرك التحليل المالي للبنوك المصرية — جلب تلقائي للبيانات '
    'من المصادر المتاحة'
    '</div>',
    unsafe_allow_html=True,
)

with st.expander("⚙️ إعدادات التحليل", expanded=True):
    c1, c2, c3 = st.columns(3)

    with c1:
        cost_of_equity_pct = st.slider(
            "العائد المطلوب على حقوق الملكية %",
            min_value=12,
            max_value=35,
            value=24,
            step=1,
            help=(
                "افتراض تقييم قابل للتعديل؛ ليس سعر فائدة رسميًا "
                "ولا تقديرًا مضمونًا لتكلفة رأس المال."
            ),
        )

    with c2:
        min_quality = st.slider(
            "حد جودة البيانات للعرض المميز",
            min_value=0,
            max_value=100,
            value=35,
            step=5,
        )

    with c3:
        top_n = st.slider(
            "عدد البنوك في الجدول الرئيسي",
            min_value=5,
            max_value=max(5, len(BANKS)),
            value=min(10, len(BANKS)),
            step=1,
        )

    st.caption(
        "مصدر البيانات الأساسي: Yahoo Finance عند توفر البيانات. "
        "يتم فحص المواقع الرسمية بحثًا عن روابط التقارير، "
        "لكن وجود رابط لا يعني أن محتوى التقرير تم تحليله."
    )

cost_of_equity = cost_of_equity_pct / 100.0

c_load, c_refresh = st.columns([3, 1])

with c_load:
    st.info(
        "لا تحتاج إلى رفع ملفات. اضغط الزر لجلب البيانات "
        "المتاحة وتحليلها تلقائيًا."
    )

with c_refresh:
    refresh = st.button(
        "🔄 تحديث البيانات",
        use_container_width=True,
        type="primary",
    )

if refresh:
    load_all_banks_cached.clear()

if (
    "bank_analysis_df" not in st.session_state
    or refresh
    or st.button("▶️ تشغيل التحليل", use_container_width=True)
):
    with st.spinner(
        "جارٍ جلب بيانات البنوك وفحص المصادر وحساب التقييمات..."
    ):
        try:
            definitions = tuple(
                tuple(sorted(bank.items()))
                for bank in BANKS
            )

            # Convert the immutable representation back to dictionaries.
            bank_definitions = [
                dict(items)
                for items in definitions
            ]

            df = load_all_banks_cached(
                tuple(
                    tuple(sorted(bank.items()))
                    for bank in bank_definitions
                ),
                cost_of_equity,
            )

            # Depending on Streamlit cache serialization, normalize
            # the input if needed by the helper below.
            st.session_state["bank_analysis_df"] = df

        except Exception as exc:
            st.error(
                "تعذر إكمال التحليل. "
                f"نوع الخطأ: {type(exc).__name__}"
            )
            st.exception(exc)

df = st.session_state.get("bank_analysis_df")

if isinstance(df, pd.DataFrame) and not df.empty:

    # --------------------------------------------------------
    # Main KPIs
    # --------------------------------------------------------
    total_banks = len(df)

    price_count = (
        df["price"].notna().sum()
        if "price" in df.columns
        else 0
    )

    fair_count = (
        df["fair_value"].notna().sum()
        if "fair_value" in df.columns
        else 0
    )

    good_data_count = (
        (df["data_quality"] >= min_quality).sum()
        if "data_quality" in df.columns
        else 0
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("البنوك في القائمة", f"{total_banks}")
    m2.metric("أسعار متاحة", f"{price_count}")
    m3.metric("تقييمات مبدئية", f"{fair_count}")
    m4.metric("جودة بيانات مقبولة", f"{good_data_count}")

    st.markdown("## 🏆 ترتيب البنوك حسب التحليل المالي")

    st.caption(
        "الدرجة ترتيب أولي مبني على المؤشرات المتاحة فقط، "
        "ولا تعني أن البنك استثمار آمن أو أن بياناته مكتملة."
    )

    display_df = df.copy()

    display_df["السهم"] = display_df["symbol"]
    display_df["البنك"] = display_df["name_ar"]
    display_df["السعر"] = display_df["price"]
    display_df["القيمة العادلة"] = display_df["fair_value"]
    display_df["شراء بهامش 30%"] = display_df["buy_zone_30"]
    display_df["شراء بهامش 20%"] = display_df["buy_zone_20"]
    display_df["شراء بهامش 10%"] = display_df["buy_zone_10"]
    display_df["العائد على حقوق الملكية"] = display_df["roe_final"]
    display_df["العائد على الأصول"] = display_df["roa_final"]
    display_df["ربحية السهم"] = display_df["eps"]
    display_df["القيمة الدفترية للسهم"] = display_df["bvps_final"]
    display_df["مضاعف الربحية"] = display_df["trailing_pe"]
    display_df["مضاعف القيمة الدفترية"] = display_df["price_to_book"]
    display_df["درجة مالية"] = display_df["financial_score"]
    display_df["جودة البيانات"] = display_df["data_quality"]
    display_df["الثقة بالتقييم"] = display_df["valuation_confidence"]
    display_df["حالة البيانات"] = display_df["data_status"]

    main_columns = [
        "السهم",
        "البنك",
        "السعر",
        "القيمة العادلة",
        "شراء بهامش 30%",
        "شراء بهامش 20%",
        "شراء بهامش 10%",
        "العائد على حقوق الملكية",
        "العائد على الأصول",
        "ربحية السهم",
        "القيمة الدفترية للسهم",
        "مضاعف الربحية",
        "مضاعف القيمة الدفترية",
        "درجة مالية",
        "جودة البيانات",
        "الثقة بالتقييم",
        "حالة البيانات",
    ]

    main_columns = [
        col for col in main_columns
        if col in display_df.columns
    ]

    ranked_df = display_df.head(top_n)[main_columns]

    st.dataframe(
        ranked_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "السعر": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "القيمة العادلة": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "شراء بهامش 30%": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "شراء بهامش 20%": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "شراء بهامش 10%": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "العائد على حقوق الملكية": st.column_config.NumberColumn(
                format="%.1%%"
            ),
            "العائد على الأصول": st.column_config.NumberColumn(
                format="%.1%%"
            ),
            "درجة مالية": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
            "جودة البيانات": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        },
    )

    # --------------------------------------------------------
    # Valuation interpretation
    # --------------------------------------------------------
    st.markdown("## 💰 قراءة فرص التقييم")

    valuation_view = df.copy()

    if "price" in valuation_view.columns:
        valuation_view = valuation_view[
            valuation_view["price"].notna()
        ]

    if "fair_value" in valuation_view.columns:
        valuation_view = valuation_view[
            valuation_view["fair_value"].notna()
        ]

    if not valuation_view.empty:
        valuation_view["فرق القيمة العادلة %"] = (
            valuation_view["fair_value"]
            / valuation_view["price"]
            - 1
        )

        valuation_view["منطقة التقييم"] = np.select(
            [
                valuation_view["price"]
                <= valuation_view["buy_zone_30"],

                valuation_view["price"]
                <= valuation_view["buy_zone_20"],

                valuation_view["price"]
                <= valuation_view["buy_zone_10"],

                valuation_view["price"]
                < valuation_view["fair_value"],
            ],
            [
                "خصم 30% أو أكثر عن القيمة المقدرة",
                "خصم 20%-30%",
                "خصم 10%-20%",
                "أقل من القيمة المقدرة بخصم محدود",
            ],
            default="السعر عند القيمة المقدرة أو أعلى",
        )

        st.dataframe(
            valuation_view[
                [
                    "symbol",
                    "name_ar",
                    "price",
                    "fair_value",
                    "fair_value_low",
                    "fair_value_high",
                    "buy_zone_30",
                    "buy_zone_20",
                    "buy_zone_10",
                    "upside_to_fair_value",
                    "valuation_confidence",
                    "منطقة التقييم",
                ]
            ].rename(
                columns={
                    "symbol": "السهم",
                    "name_ar": "البنك",
                    "price": "السعر",
                    "fair_value": "القيمة العادلة",
                    "fair_value_low": "أقل تقدير",
                    "fair_value_high": "أعلى تقدير",
                    "buy_zone_30": "شراء بخصم 30%",
                    "buy_zone_20": "شراء بخصم 20%",
                    "buy_zone_10": "شراء بخصم 10%",
                    "upside_to_fair_value": "الفرق عن القيمة العادلة",
                    "valuation_confidence": "الثقة بالتقييم",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning(
            "لا توجد تقييمات كافية لعرضها. "
            "قد تكون البيانات المالية غير متاحة من المصدر."
        )

    # --------------------------------------------------------
    # Three-year scenarios
    # --------------------------------------------------------
    st.markdown("## 📈 السيناريوهات الافتراضية لثلاث سنوات")

    scenario_df = df[
        [
            "symbol",
            "name_ar",
            "target_3y_conservative",
            "target_3y_base",
            "target_3y_optimistic",
            "scenario_basis",
        ]
    ].copy()

    scenario_df = scenario_df.rename(
        columns={
            "symbol": "السهم",
            "name_ar": "البنك",
            "target_3y_conservative": "سيناريو متحفظ",
            "target_3y_base": "سيناريو أساسي",
            "target_3y_optimistic": "سيناريو متفائل",
            "scenario_basis": "أساس السيناريو",
        }
    )

    st.dataframe(
        scenario_df,
        use_container_width=True,
        hide_index=True,
    )

    st.warning(
        "سيناريوهات السنوات الثلاث مبنية على معدلات نمو ومضاعفات "
        "افتراضية، وليست توقعات مؤكدة أو أسعارًا مستهدفة موثقة."
    )

    # --------------------------------------------------------
    # Individual bank profile
    # --------------------------------------------------------
    st.markdown("## 🔎 ملف البنك التفصيلي")

    options = df["symbol"].astype(str).tolist()

    selected_symbol = st.selectbox(
        "اختر البنك",
        options,
        format_func=lambda x: (
            f"{x} — "
            + str(
                df.loc[
                    df["symbol"] == x,
                    "name_ar",
                ].iloc[0]
            )
        ),
    )

    selected_rows = df[df["symbol"] == selected_symbol]

    if not selected_rows.empty:
        row = selected_rows.iloc[0]

        st.markdown(f"### {row.get('name_ar', selected_symbol)}")

        a1, a2, a3, a4 = st.columns(4)

        a1.metric("السعر", fmt_price(row.get("price")))
        a2.metric(
            "القيمة العادلة التقديرية",
            fmt_price(row.get("fair_value")),
        )
        a3.metric(
            "القيمة الدفترية للسهم",
            fmt_price(row.get("bvps_final")),
        )
        a4.metric(
            "درجة التحليل",
            fmt_number(row.get("financial_score"), 1),
        )

        st.markdown("#### المؤشرات المالية")

        detail_metrics = [
            ("العائد على حقوق الملكية", "roe_final", "percent"),
            ("العائد على الأصول", "roa_final", "percent"),
            ("ربحية السهم", "eps", "number"),
            ("مضاعف الربحية", "trailing_pe", "number"),
            ("مضاعف القيمة الدفترية", "price_to_book", "number"),
            ("القيمة الدفترية للسهم", "bvps_final", "number"),
            ("صافي الدخل", "net_income", "number"),
            ("إجمالي الأصول", "total_assets", "number"),
            ("حقوق الملكية", "total_equity", "number"),
            ("إجمالي الإيرادات", "total_revenue", "number"),
            ("عائد التوزيعات", "dividend_yield", "percent"),
            ("نسبة التوزيعات", "payout_ratio", "percent"),
        ]

        metric_rows = []

        for label, key, kind in detail_metrics:
            value = row.get(key)

            if kind == "percent":
                shown = fmt_percent(value)
            else:
                shown = fmt_number(value)

            metric_rows.append({
                "المؤشر": label,
                "القيمة": shown,
            })

        st.dataframe(
            pd.DataFrame(metric_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### جودة البيانات والثقة")

        st.write(
            f"جودة البيانات: "
            f"{fmt_number(row.get('data_quality'), 1)} / 100"
        )

        st.write(
            f"الثقة بالتقييم: "
            f"{row.get('valuation_confidence', 'غير متاح')}"
        )

        st.write(
            f"حالة القوائم المالية: "
            f"{row.get('statement_status', 'غير متاح')}"
        )

        st.write(
            f"حالة الموقع الرسمي: "
            f"{row.get('website_status', 'غير متاح')}"
        )

        st.write(
            f"وقت آخر محاولة جلب: "
            f"{row.get('retrieved_at', 'غير متاح')}"
        )

        st.write(
            f"مصدر السعر: "
            f"{row.get('price_source', 'غير متاح')}"
        )

        st.write(
            f"مصدر البيانات المالية: "
            f"{row.get('fundamental_source', 'غير متاح')}"
        )

        notes = row.get("source_notes", [])

        if isinstance(notes, list) and notes:
            st.markdown("#### ملاحظات على البيانات")

            for note in notes:
                st.write(f"- {note}")

        # Official site and discovered reports
        st.markdown("#### روابط الموقع الرسمي والتقارير المحتملة")

        website = row.get("website")

        if website:
            st.markdown(
                f"[فتح الموقع الرسمي للبنك]({website})"
            )

        investor_links = row.get("investor_links", [])
        report_links = row.get("report_links", [])

        if isinstance(investor_links, list) and investor_links:
            st.markdown("**صفحات محتملة لعلاقات المستثمرين:**")

            for item in investor_links:
                st.markdown(
                    f"- [{item['text']}]({item['url']})"
                )

        if isinstance(report_links, list) and report_links:
            st.markdown("**تقارير أو ملفات محتملة:**")

            for item in report_links:
                st.markdown(
                    f"- [{item['text']}]({item['url']})"
                )

        if not investor_links and not report_links:
            st.info(
                "لم يتم العثور على روابط تقارير مناسبة أثناء الفحص. "
                "هذا لا يعني أن البنك لا ينشر تقارير مالية."
            )

    # --------------------------------------------------------
    # Data quality view
    # --------------------------------------------------------
    st.markdown("## 🧪 مراقبة جودة البيانات")

    quality_view = df[
        [
            "symbol",
            "name_ar",
            "market_status",
            "statement_status",
            "website_status",
            "data_quality",
            "analysis_status",
            "retrieved_at",
        ]
    ].copy()

    quality_view = quality_view.rename(
        columns={
            "symbol": "السهم",
            "name_ar": "البنك",
            "market_status": "حالة السعر",
            "statement_status": "حالة القوائم",
            "website_status": "حالة الموقع",
            "data_quality": "جودة البيانات",
            "analysis_status": "حالة التحليل",
            "retrieved_at": "وقت الجلب",
        }
    )

    st.dataframe(
        quality_view,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Download generated analysis
    # --------------------------------------------------------
    st.markdown("## 📥 تصدير نتائج التحليل")

    export_columns = [
        "symbol",
        "name_ar",
        "price",
        "eps",
        "bvps_final",
        "roe_final",
        "roa_final",
        "trailing_pe",
        "price_to_book",
        "net_income",
        "total_assets",
        "total_equity",
        "fair_value",
        "fair_value_low",
        "fair_value_high",
        "buy_zone_30",
        "buy_zone_20",
        "buy_zone_10",
        "upside_to_fair_value",
        "financial_score",
        "data_quality",
        "valuation_confidence",
        "market_status",
        "statement_status",
        "website_status",
        "retrieved_at",
    ]

    export_columns = [
        c for c in export_columns
        if c in df.columns
    ]

    export_df = df[export_columns].copy()

    export_csv = export_df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")

    st.download_button(
        "⬇️ تحميل نتائج التحليل CSV",
        data=export_csv,
        file_name="EGX_Banks_Financial_Analysis.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("عرض البيانات الخام التي تم جلبها"):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

else:
    st.info(
        "اضغط «تشغيل التحليل» لبدء جلب البيانات تلقائيًا. "
        "قد يستغرق الجلب بعض الوقت حسب استجابة المصادر."
    )

st.divider()

st.caption(
    f"{APP_NAME} v{APP_VERSION} | آخر وقت عرض: {now_utc()}"
)

st.caption(
    "تنبيه استثماري: النتائج لأغراض التحليل الأولي فقط، "
    "وليست توصية شراء أو بيع. يجب التحقق من القوائم المالية "
    "الأصلية، وفترة التقرير، والعملة، ووحدة القياس، وعدد الأسهم "
    "قبل اتخاذ قرار استثماري."
)
