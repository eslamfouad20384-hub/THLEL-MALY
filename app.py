# -*- coding: utf-8 -*-
"""
EGX Banks Financial Intelligence PRO
Version 1.1 - Tuple Error Fixed

Automatic financial-data retrieval for Egyptian bank stocks.
No manual CSV/XLSX upload required.

IMPORTANT:
- Data availability depends on external providers.
- Official website scanning discovers links; it does not
  guarantee automatic extraction of financial-statement PDFs.
- Missing data is not fabricated.
- Valuations are preliminary estimates, not investment advice.
"""

import logging
import re
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
APP_VERSION = "1.1"

CACHE_TTL_SECONDS = 1800
REQUEST_TIMEOUT = 12
MAX_WORKERS = 5

DEFAULT_COST_OF_EQUITY = 0.24
DEFAULT_GROWTH_LOW = 0.05
DEFAULT_GROWTH_BASE = 0.12
DEFAULT_GROWTH_HIGH = 0.18

MARGIN_EXCELLENT = 0.30
MARGIN_STRONG = 0.20
MARGIN_ACCEPTABLE = 0.10

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

# These are candidate symbols, not a verified live EGX listing feed.
# Verify symbols against the official exchange listing directory.

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


# ============================================================
# GENERAL UTILITIES
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def safe_float(value):
    try:
        if value is None or isinstance(value, (dict, list, tuple)):
            return np.nan

        value = float(value)

        if not np.isfinite(value):
            return np.nan

        return value

    except (ValueError, TypeError, OverflowError):
        return np.nan


def first_valid(*values):
    for value in values:
        number = safe_float(value)

        if not pd.isna(number):
            return number

    return np.nan


def safe_divide(numerator, denominator):
    numerator = safe_float(numerator)
    denominator = safe_float(denominator)

    if (
        pd.isna(numerator)
        or pd.isna(denominator)
        or denominator == 0
    ):
        return np.nan

    return numerator / denominator


def clean_text(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def fmt_number(value, decimals=2):
    value = safe_float(value)

    if pd.isna(value):
        return "غير متاح"

    return f"{value:,.{decimals}f}"


def fmt_percent(value, decimals=1):
    value = safe_float(value)

    if pd.isna(value):
        return "غير متاح"

    return f"{value * 100:.{decimals}f}%"


def fmt_price(value):
    return fmt_number(value, 2)


def empty_statement():
    return pd.DataFrame()


def get_last_numeric_value(statement, keywords):
    """
    Retrieve the latest available numeric value matching a
    statement-row keyword.

    Labels and provider conventions may differ. Returned figures
    require verification against the original financial report.
    """
    if (
        statement is None
        or not isinstance(statement, pd.DataFrame)
        or statement.empty
    ):
        return np.nan

    try:
        columns = list(statement.columns)

        for keyword in keywords:
            for index in statement.index:
                label = str(index).lower()

                if keyword.lower() not in label:
                    continue

                row = statement.loc[index]

                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]

                for column in columns:
                    if column not in row.index:
                        continue

                    value = safe_float(row[column])

                    if not pd.isna(value):
                        return value

    except Exception:
        LOGGER.exception("Statement-row extraction failed")

    return np.nan


def safe_get_info(ticker):
    try:
        return ticker.info or {}
    except Exception as exc:
        LOGGER.warning("Ticker info unavailable: %s", exc)
        return {}


def safe_get_statement(ticker, attribute):
    try:
        result = getattr(ticker, attribute)

        if isinstance(result, pd.DataFrame):
            return result

    except Exception as exc:
        LOGGER.info("%s unavailable: %s", attribute, exc)

    return empty_statement()


# ============================================================
# OFFICIAL WEBSITE LINK DISCOVERY
# ============================================================

def discover_official_financial_pages(base_url):
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
                f"HTTP {response.status_code}"
            )
            return result

        result["website_status"] = "تم الوصول للموقع"

        if BeautifulSoup is None:
            result["website_status"] = (
                "تم الوصول؛ مكتبة BeautifulSoup غير متاحة"
            )
            return result

        soup = BeautifulSoup(response.text, "html.parser")

        base_domain = urlparse(base_url).netloc

        investor_terms = [
            "investor",
            "investor relations",
            "financial results",
            "financial information",
            "المستثمرين",
            "علاقات المستثمرين",
            "القوائم المالية",
        ]

        report_terms = [
            "annual report",
            "financial report",
            "financial statement",
            "quarterly report",
            "annual financial",
            "التقرير السنوي",
            "القوائم المالية",
            "النتائج المالية",
        ]

        investor_links = []
        report_links = []

        for anchor in soup.find_all("a", href=True):
            label = clean_text(anchor.get_text(" ", strip=True))
            url = urljoin(base_url, anchor["href"])

            if not url.startswith(("http://", "https://")):
                continue

            if urlparse(url).netloc != base_domain:
                continue

            combined = f"{label} {url}".lower()

            if any(term in combined for term in investor_terms):
                investor_links.append({
                    "text": label or "صفحة المستثمرين المحتملة",
                    "url": url,
                })

            if (
                any(term in combined for term in report_terms)
                or url.lower().split("?")[0].endswith(".pdf")
            ):
                report_links.append({
                    "text": label or "تقرير محتمل",
                    "url": url,
                })

        def deduplicate(items):
            seen = set()
            result_items = []

            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    result_items.append(item)

            return result_items

        result["investor_links"] = deduplicate(investor_links)[:15]
        result["report_links"] = deduplicate(report_links)[:25]

    except Exception as exc:
        result["website_status"] = (
            f"تعذر فحص الموقع: {type(exc).__name__}"
        )

    return result


# ============================================================
# AUTOMATIC DATA RETRIEVAL
# ============================================================

def retrieve_bank_data(bank):
    """
    IMPORTANT FIX:
    bank must be a dictionary. The cache function below converts
    tuple-based bank definitions back into dictionaries before
    submitting this function to the thread pool.
    """
    if not isinstance(bank, dict):
        bank = dict(bank)

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
        # Market information
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

        if pd.isna(price):
            try:
                history = ticker.history(
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                )

                if history is not None and not history.empty:
                    close_values = history["Close"].dropna()

                    if not close_values.empty:
                        price = safe_float(close_values.iloc[-1])

                        output["source_notes"].append(
                            "السعر مأخوذ من آخر إغلاق متاح، "
                            "وقد لا يكون سعرًا لحظيًا."
                        )

            except Exception as exc:
                LOGGER.warning(
                    "History failed for %s: %s",
                    symbol,
                    exc,
                )

        output.update({
            "price": price,
            "previous_close": previous_close,
            "market_cap": safe_float(info.get("marketCap")),
            "shares_outstanding": safe_float(
                info.get("sharesOutstanding")
            ),
            "currency": info.get("currency"),
            "trailing_pe": safe_float(info.get("trailingPE")),
            "forward_pe": safe_float(info.get("forwardPE")),
            "price_to_book": safe_float(info.get("priceToBook")),
            "eps": safe_float(info.get("trailingEps")),
            "book_value_per_share": safe_float(
                info.get("bookValue")
            ),
            "dividend_yield": safe_float(
                info.get("dividendYield")
            ),
            "payout_ratio": safe_float(
                info.get("payoutRatio")
            ),
            "roe": safe_float(info.get("returnOnEquity")),
            "roa": safe_float(info.get("returnOnAssets")),
        })

        output["market_status"] = (
            "تم جلب سعر"
            if not pd.isna(price)
            else "لم يتوفر سعر من المصدر"
        )

        # ----------------------------------------------------
        # Financial statements
        # ----------------------------------------------------

        financials = safe_get_statement(ticker, "financials")
        balance = safe_get_statement(ticker, "balance_sheet")
        cashflow = safe_get_statement(ticker, "cashflow")

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
            ["total revenue", "operating revenue"],
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
            ["interest income"],
        )

        output["interest_expense"] = get_last_numeric_value(
            financials,
            ["interest expense"],
        )

        output["net_interest_income"] = get_last_numeric_value(
            financials,
            ["net interest income"],
        )

        output["total_assets"] = get_last_numeric_value(
            balance,
            ["total assets"],
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

        output["gross_loans"] = get_last_numeric_value(
            balance,
            [
                "loans and advances",
                "loans receivable",
                "total loans",
                "loans",
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

        # ----------------------------------------------------
        # Official website discovery
        # ----------------------------------------------------

        website_data = discover_official_financial_pages(
            bank.get("website")
        )

        output["website_status"] = website_data["website_status"]
        output["investor_links"] = website_data["investor_links"]
        output["report_links"] = website_data["report_links"]

        output["source_notes"].append(
            "فحص الموقع الرسمي يكتشف روابط محتملة فقط؛ "
            "لا يعني أن الأرقام استخرجت من ملفات PDF."
        )

        output["data_status"] = "اكتمل الجلب الأولي"

    except Exception as exc:
        LOGGER.exception("Data retrieval failed for %s", symbol)

        output["data_status"] = (
            f"تعذر الجلب: {type(exc).__name__}"
        )

        output["source_notes"].append(
            f"خطأ الجلب: {clean_text(exc)[:180]}"
        )

    # --------------------------------------------------------
    # Derived financial metrics
    # --------------------------------------------------------

    shares = safe_float(output["shares_outstanding"])
    equity = safe_float(output["total_equity"])
    net_income = safe_float(output["net_income"])
    assets = safe_float(output["total_assets"])

    output["calculated_bvps"] = np.nan
    output["calculated_roe"] = np.nan
    output["calculated_roa"] = np.nan

    if (
        not pd.isna(equity)
        and not pd.isna(shares)
        and shares > 0
    ):
        output["calculated_bvps"] = equity / shares

    if (
        not pd.isna(net_income)
        and not pd.isna(equity)
        and equity > 0
    ):
        output["calculated_roe"] = net_income / equity

    if (
        not pd.isna(net_income)
        and not pd.isna(assets)
        and assets > 0
    ):
        output["calculated_roa"] = net_income / assets

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
# BANK VALUATION ENGINE
# ============================================================

def valuation_engine(row, cost_of_equity):
    price = safe_float(row.get("price"))
    bvps = safe_float(row.get("bvps_final"))
    eps = safe_float(row.get("eps"))
    roe = safe_float(row.get("roe_final"))

    fair_values = []
    weights = []
    methods = []

    # Method 1: Justified P/B approximation
    if (
        not pd.isna(bvps)
        and bvps > 0
        and not pd.isna(roe)
        and cost_of_equity > 0
    ):
        if roe > 0:
            justified_pb = roe / cost_of_equity
            justified_pb = min(max(justified_pb, 0.35), 2.50)

            fair_pb = bvps * justified_pb

            if np.isfinite(fair_pb) and fair_pb > 0:
                fair_values.append(fair_pb)
                weights.append(0.50)
                methods.append("P/B مبرر")

    # Method 2: Simplified residual-income estimate
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
            weights.append(0.35)
            methods.append("دخل متبقٍ مبسط")

    # Method 3: P/E cross-check.
    # 7x is a screening assumption, not a verified peer multiple.
    if not pd.isna(eps) and eps > 0:
        fair_pe = eps * 7.0

        if np.isfinite(fair_pe) and fair_pe > 0:
            fair_values.append(fair_pe)
            weights.append(0.15)
            methods.append("مضاعف ربحية افتراضي")

    fair_value = np.nan
    fair_low = np.nan
    fair_high = np.nan
    confidence = "غير كافية"

    if fair_values:
        values = np.array(fair_values, dtype=float)
        weight_array = np.array(weights, dtype=float)
        weight_array = weight_array / weight_array.sum()

        fair_value = float(np.sum(values * weight_array))
        fair_low = float(np.min(values))
        fair_high = float(np.max(values))

        if len(fair_values) >= 2 and fair_value > 0:
            dispersion = (
                (fair_high - fair_low) / fair_value
            )

            if dispersion <= 0.30:
                confidence = "متوسطة"
            elif dispersion <= 0.60:
                confidence = "منخفضة"
            else:
                confidence = "ضعيفة جدًا"

        elif len(fair_values) == 1:
            confidence = "منخفضة جدًا"

    buy_30 = (
        fair_value * (1 - MARGIN_EXCELLENT)
        if not pd.isna(fair_value)
        else np.nan
    )

    buy_20 = (
        fair_value * (1 - MARGIN_STRONG)
        if not pd.isna(fair_value)
        else np.nan
    )

    buy_10 = (
        fair_value * (1 - MARGIN_ACCEPTABLE)
        if not pd.isna(fair_value)
        else np.nan
    )

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
        "valuation_confidence": confidence,
    }


# ============================================================
# THREE-YEAR SCENARIOS
# ============================================================

def scenario_engine(row):
    eps = safe_float(row.get("eps"))
    bvps = safe_float(row.get("bvps_final"))

    result = {
        "target_3y_conservative": np.nan,
        "target_3y_base": np.nan,
        "target_3y_optimistic": np.nan,
        "scenario_basis": "غير متاح",
    }

    if not pd.isna(eps) and eps > 0:
        result.update({
            "target_3y_conservative": (
                eps * (1 + DEFAULT_GROWTH_LOW) ** 3 * 6.0
            ),
            "target_3y_base": (
                eps * (1 + DEFAULT_GROWTH_BASE) ** 3 * 7.0
            ),
            "target_3y_optimistic": (
                eps * (1 + DEFAULT_GROWTH_HIGH) ** 3 * 9.0
            ),
            "scenario_basis": (
                "ربحية السهم ومضاعفات افتراضية"
            ),
        })

    elif not pd.isna(bvps) and bvps > 0:
        result.update({
            "target_3y_conservative": (
                bvps * (1 + DEFAULT_GROWTH_LOW) ** 3
            ),
            "target_3y_base": (
                bvps * (1 + DEFAULT_GROWTH_BASE) ** 3
            ),
            "target_3y_optimistic": (
                bvps * (1 + DEFAULT_GROWTH_HIGH) ** 3
            ),
            "scenario_basis": (
                "نمو افتراضي للقيمة الدفترية، وليس سعرًا مستهدفًا"
            ),
        })

    return result


# ============================================================
# DATA QUALITY
# ============================================================

def calculate_data_quality(row):
    checks = {
        "price": not pd.isna(safe_float(row.get("price"))),
        "EPS": not pd.isna(safe_float(row.get("eps"))),
        "BVPS": not pd.isna(safe_float(row.get("bvps_final"))),
        "ROE": not pd.isna(safe_float(row.get("roe_final"))),
        "ROA": not pd.isna(safe_float(row.get("roa_final"))),
        "net income": not pd.isna(safe_float(row.get("net_income"))),
        "equity": not pd.isna(safe_float(row.get("total_equity"))),
        "assets": not pd.isna(safe_float(row.get("total_assets"))),
        "P/B": not pd.isna(safe_float(row.get("price_to_book"))),
        "P/E": not pd.isna(safe_float(row.get("trailing_pe"))),
    }

    score = 100 * sum(checks.values()) / len(checks)

    return round(score, 1), checks


# ============================================================
# FINANCIAL SCORING
# ============================================================

def financial_score(row):
    components = []

    roe = safe_float(row.get("roe_final"))
    roa = safe_float(row.get("roa_final"))
    eps = safe_float(row.get("eps"))
    equity = safe_float(row.get("total_equity"))
    assets = safe_float(row.get("total_assets"))
    net_income = safe_float(row.get("net_income"))
    price = safe_float(row.get("price"))
    fair_value = safe_float(row.get("fair_value"))

    # ROE: maximum 25
    if not pd.isna(roe):
        if roe >= 0.25:
            score = 25
        elif roe >= 0.18:
            score = 21
        elif roe >= 0.12:
            score = 17
        elif roe >= 0.08:
            score = 12
        elif roe >= 0:
            score = 6
        else:
            score = 0

        components.append((score, 25))

    # ROA: maximum 15
    if not pd.isna(roa):
        if roa >= 0.025:
            score = 15
        elif roa >= 0.018:
            score = 12
        elif roa >= 0.012:
            score = 9
        elif roa >= 0.005:
            score = 5
        elif roa >= 0:
            score = 2
        else:
            score = 0

        components.append((score, 15))

    if not pd.isna(eps):
        components.append((15 if eps > 0 else 0, 15))

    if not pd.isna(equity):
        components.append((15 if equity > 0 else 0, 15))

    if not pd.isna(assets):
        components.append((10 if assets > 0 else 0, 10))

    if not pd.isna(net_income):
        components.append((10 if net_income > 0 else 0, 10))

    if (
        not pd.isna(price)
        and price > 0
        and not pd.isna(fair_value)
        and fair_value > 0
    ):
        upside = fair_value / price - 1

        if upside >= 0.30:
            score = 10
        elif upside >= 0.15:
            score = 8
        elif upside >= 0:
            score = 6
        elif upside >= -0.15:
            score = 3
        else:
            score = 0

        components.append((score, 10))

    if not components:
        return np.nan

    maximum = sum(weight for _, weight in components)
    earned = sum(value for value, _ in components)

    return round(100 * earned / maximum, 1)


def score_label(score):
    score = safe_float(score)

    if pd.isna(score):
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

    row.update(
        valuation_engine(row, cost_of_equity)
    )

    row.update(
        scenario_engine(row)
    )

    quality, checks = calculate_data_quality(row)

    row["data_quality"] = quality
    row["quality_checks"] = checks

    row["financial_score"] = financial_score(row)
    row["financial_grade"] = score_label(
        row["financial_score"]
    )

    row["analysis_status"] = (
        "تحليل أولي"
        if quality >= 35
        else "بيانات غير كافية"
    )

    return row


# ============================================================
# DATA LOADER - TUPLE ERROR FIXED
# ============================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_all_banks_cached(bank_definitions, cost_of_equity):
    """
    Accept either dictionaries or tuples of (key, value) pairs.

    FIX:
    Convert each bank definition back to a dictionary before
    calling retrieve_bank_data. This fixes:
    TypeError: tuple indices must be integers or slices, not str
    """

    banks = []

    for item in bank_definitions:
        if isinstance(item, dict):
            bank = dict(item)
        else:
            bank = dict(item)

        banks.append(bank)

    records = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(retrieve_bank_data, bank): bank
            for bank in banks
        }

        for future in as_completed(future_map):
            bank = future_map[future]

            try:
                result = future.result()

                if isinstance(result, dict):
                    records.append(result)
                else:
                    records.append({
                        **bank,
                        "retrieved_at": now_utc(),
                        "data_status": "صيغة نتيجة غير متوقعة",
                        "price": np.nan,
                        "source_notes": [
                            "دالة الجلب لم تُرجع قاموسًا."
                        ],
                    })

            except Exception as exc:
                LOGGER.exception(
                    "Retrieval failed for %s",
                    bank.get("symbol", "UNKNOWN"),
                )

                records.append({
                    **bank,
                    "retrieved_at": now_utc(),
                    "data_status": (
                        f"تعذر الجلب: {type(exc).__name__}"
                    ),
                    "price": np.nan,
                    "source_notes": [
                        f"خطأ: {clean_text(exc)[:180]}"
                    ],
                })

    analyzed = []

    for record in records:
        try:
            analyzed.append(
                analyze_bank_record(
                    record,
                    cost_of_equity,
                )
            )

        except Exception as exc:
            LOGGER.exception(
                "Analysis failed for %s",
                record.get("symbol", "UNKNOWN"),
            )

            failed_record = dict(record)
            failed_record["analysis_status"] = (
                f"تعذر التحليل: {type(exc).__name__}"
            )

            notes = failed_record.get("source_notes", [])

            if not isinstance(notes, list):
                notes = [str(notes)]

            notes.append(
                f"خطأ التحليل: {clean_text(exc)[:180]}"
            )

            failed_record["source_notes"] = notes
            analyzed.append(failed_record)

    df = pd.DataFrame(analyzed)

    if not df.empty and "financial_score" in df.columns:
        df = df.sort_values(
            by=["financial_score", "data_quality"],
            ascending=[False, False],
            na_position="last",
        ).reset_index(drop=True)

    return df


# ============================================================
# STREAMLIT PAGE CONFIGURATION
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
        font-size: 29px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 8px;
    }

    .subtitle {
        text-align: center;
        opacity: .80;
        margin-bottom: 22px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">'
    '🏦 EGX Banks Financial Intelligence PRO'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'محرك التحليل المالي للبنوك المصرية — جلب تلقائي للبيانات'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR / SETTINGS
# ============================================================

with st.expander("⚙️ إعدادات التحليل", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        cost_of_equity_pct = st.slider(
            "العائد المطلوب على حقوق الملكية %",
            min_value=12,
            max_value=35,
            value=24,
            step=1,
            help="افتراض قابل للتعديل لأغراض التقييم.",
        )

    with col2:
        top_n = st.slider(
            "عدد البنوك المعروضة",
            min_value=5,
            max_value=len(BANKS),
            value=min(10, len(BANKS)),
            step=1,
        )

    st.caption(
        "المصدر الأساسي للبيانات المنظمة هو Yahoo Finance. "
        "يتم فحص المواقع الرسمية للبحث عن روابط التقارير، "
        "لكن استخراج كل بيانات PDF ليس مضمونًا في هذه النسخة."
    )

cost_of_equity = cost_of_equity_pct / 100.0


# ============================================================
# REFRESH / RUN
# ============================================================

col_info, col_refresh, col_run = st.columns([3, 1, 1])

with col_info:
    st.info(
        "لا تحتاج إلى رفع أي ملفات. اضغط تشغيل التحليل "
        "لجلب البيانات المتاحة تلقائيًا."
    )

with col_refresh:
    refresh_clicked = st.button(
        "🔄 تحديث البيانات",
        use_container_width=True,
    )

with col_run:
    run_clicked = st.button(
        "▶️ تشغيل التحليل",
        type="primary",
        use_container_width=True,
    )

if refresh_clicked:
    load_all_banks_cached.clear()
    st.session_state.pop("bank_analysis_df", None)

if refresh_clicked or run_clicked or "bank_analysis_df" not in st.session_state:
    with st.spinner(
        "جارٍ جلب البيانات المالية وفحص المصادر..."
    ):
        try:
            # Cache arguments are immutable tuples, but the loader
            # converts them back to dictionaries before data retrieval.
            bank_definitions = tuple(
                tuple(sorted(bank.items()))
                for bank in BANKS
            )

            df = load_all_banks_cached(
                bank_definitions,
                cost_of_equity,
            )

            st.session_state["bank_analysis_df"] = df

        except Exception as exc:
            LOGGER.exception("Application-level analysis failed")

            st.error(
                "تعذر إكمال التحليل. "
                f"نوع الخطأ: {type(exc).__name__}"
            )

            st.exception(exc)


# ============================================================
# DISPLAY RESULTS
# ============================================================

df = st.session_state.get("bank_analysis_df")

if isinstance(df, pd.DataFrame) and not df.empty:

    # --------------------------------------------------------
    # KPI cards
    # --------------------------------------------------------

    total_banks = len(df)

    prices_available = (
        df["price"].notna().sum()
        if "price" in df.columns
        else 0
    )

    valuations_available = (
        df["fair_value"].notna().sum()
        if "fair_value" in df.columns
        else 0
    )

    statements_available = (
        df["statement_status"].eq("تم استرجاع قوائم").sum()
        if "statement_status" in df.columns
        else 0
    )

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("البنوك في القائمة", str(total_banks))
    k2.metric("أسعار متاحة", str(prices_available))
    k3.metric("تقييمات مبدئية", str(valuations_available))
    k4.metric("قوائم مسترجعة", str(statements_available))

    # --------------------------------------------------------
    # Main ranking
    # --------------------------------------------------------

    st.markdown("## 🏆 ترتيب البنوك حسب التحليل المالي")

    st.caption(
        "الترتيب أولي ويعتمد على البيانات المتاحة لكل بنك. "
        "لا تعتبر الدرجة توصية شراء أو مقياسًا مكتملًا للمخاطر."
    )

    main_mapping = {
        "symbol": "السهم",
        "name_ar": "البنك",
        "price": "السعر",
        "fair_value": "القيمة العادلة",
        "buy_zone_30": "شراء بخصم 30%",
        "buy_zone_20": "شراء بخصم 20%",
        "buy_zone_10": "شراء بخصم 10%",
        "roe_final": "العائد على حقوق الملكية",
        "roa_final": "العائد على الأصول",
        "eps": "ربحية السهم",
        "bvps_final": "القيمة الدفترية للسهم",
        "trailing_pe": "مضاعف الربحية",
        "price_to_book": "مضاعف القيمة الدفترية",
        "financial_score": "الدرجة المالية",
        "data_quality": "جودة البيانات",
        "valuation_confidence": "الثقة بالتقييم",
        "statement_status": "حالة القوائم",
        "data_status": "حالة الجلب",
    }

    available_mapping = {
        key: label
        for key, label in main_mapping.items()
        if key in df.columns
    }

    main_df = (
        df.head(top_n)[list(available_mapping.keys())]
        .rename(columns=available_mapping)
    )

    st.dataframe(
        main_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "السعر": st.column_config.NumberColumn(format="%.2f"),
            "القيمة العادلة": st.column_config.NumberColumn(format="%.2f"),
            "شراء بخصم 30%": st.column_config.NumberColumn(format="%.2f"),
            "شراء بخصم 20%": st.column_config.NumberColumn(format="%.2f"),
            "شراء بخصم 10%": st.column_config.NumberColumn(format="%.2f"),
            "العائد على حقوق الملكية": st.column_config.NumberColumn(format="%.1%%"),
            "العائد على الأصول": st.column_config.NumberColumn(format="%.1%%"),
            "الدرجة المالية": st.column_config.ProgressColumn(
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
    # Valuation table
    # --------------------------------------------------------

    st.markdown("## 💰 القيمة العادلة ونطاقات الشراء")

    valuation_df = df.copy()

    if "price" in valuation_df.columns:
        valuation_df = valuation_df[
            valuation_df["price"].notna()
        ]

    if "fair_value" in valuation_df.columns:
        valuation_df = valuation_df[
            valuation_df["fair_value"].notna()
        ]

    if not valuation_df.empty:
        valuation_df["فرق القيمة العادلة"] = (
            valuation_df["fair_value"]
            / valuation_df["price"]
            - 1
        )

        valuation_df["منطقة السعر"] = np.select(
            [
                valuation_df["price"] <= valuation_df["buy_zone_30"],
                valuation_df["price"] <= valuation_df["buy_zone_20"],
                valuation_df["price"] <= valuation_df["buy_zone_10"],
                valuation_df["price"] < valuation_df["fair_value"],
            ],
            [
                "خصم 30% أو أكثر",
                "خصم 20%-30%",
                "خصم 10%-20%",
                "أقل من القيمة العادلة بخصم محدود",
            ],
            default="عند القيمة العادلة أو أعلى",
        )

        valuation_mapping = {
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
            "منطقة السعر": "منطقة السعر",
        }

        valuation_mapping = {
            key: value
            for key, value in valuation_mapping.items()
            if key in valuation_df.columns
        }

        st.dataframe(
            valuation_df[list(valuation_mapping.keys())].rename(
                columns=valuation_mapping
            ),
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.warning(
            "لا توجد تقييمات كافية. تحقق من توافر السعر "
            "والقيمة الدفترية وربحية السهم."
        )

    # --------------------------------------------------------
    # Three-year scenarios
    # --------------------------------------------------------

    st.markdown("## 📈 سيناريوهات افتراضية لثلاث سنوات")

    scenario_columns = [
        "symbol",
        "name_ar",
        "target_3y_conservative",
        "target_3y_base",
        "target_3y_optimistic",
        "scenario_basis",
    ]

    scenario_columns = [
        col for col in scenario_columns
        if col in df.columns
    ]

    scenario_df = df[scenario_columns].rename(
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
        "هذه السيناريوهات ناتجة عن افتراضات نمو ومضاعفات ثابتة؛ "
        "ليست توقعات مؤكدة. إذا كان الأساس هو القيمة الدفترية "
        "فهي لا تمثل سعرًا مستهدفًا."
    )

    # --------------------------------------------------------
    # Individual bank detail
    # --------------------------------------------------------

    st.markdown("## 🔎 التحليل التفصيلي للبنك")

    symbol_options = df["symbol"].astype(str).tolist()

    selected_symbol = st.selectbox(
        "اختر البنك",
        symbol_options,
        format_func=lambda symbol: (
            f"{symbol} — "
            + str(
                df.loc[
                    df["symbol"] == symbol,
                    "name_ar",
                ].iloc[0]
            )
        ),
    )

    selected_rows = df[df["symbol"] == selected_symbol]

    if not selected_rows.empty:
        row = selected_rows.iloc[0].to_dict()

        st.subheader(
            f"{row.get('name_ar', selected_symbol)} "
            f"({selected_symbol})"
        )

        d1, d2, d3, d4 = st.columns(4)

        d1.metric("السعر", fmt_price(row.get("price")))
        d2.metric("القيمة العادلة", fmt_price(row.get("fair_value")))
        d3.metric(
            "القيمة الدفترية للسهم",
            fmt_price(row.get("bvps_final")),
        )
        d4.metric(
            "الدرجة المالية",
            fmt_number(row.get("financial_score"), 1),
        )

        detail_items = [
            ("العائد على حقوق الملكية", "roe_final", "percent"),
            ("العائد على الأصول", "roa_final", "percent"),
            ("ربحية السهم", "eps", "number"),
            ("مضاعف الربحية", "trailing_pe", "number"),
            ("مضاعف القيمة الدفترية", "price_to_book", "number"),
            ("صافي الدخل", "net_income", "number"),
            ("إجمالي الأصول", "total_assets", "number"),
            ("حقوق الملكية", "total_equity", "number"),
            ("الإيرادات", "total_revenue", "number"),
            ("عائد التوزيعات", "dividend_yield", "percent"),
            ("نسبة التوزيعات", "payout_ratio", "percent"),
            ("القيمة العادلة - الحد الأدنى", "fair_value_low", "number"),
            ("القيمة العادلة - الحد الأعلى", "fair_value_high", "number"),
            ("شراء بخصم 30%", "buy_zone_30", "number"),
            ("شراء بخصم 20%", "buy_zone_20", "number"),
            ("شراء بخصم 10%", "buy_zone_10", "number"),
        ]

        detail_rows = []

        for label, key, kind in detail_items:
            value = row.get(key)

            if kind == "percent":
                formatted = fmt_percent(value)
            else:
                formatted = fmt_number(value)

            detail_rows.append({
                "المؤشر": label,
                "القيمة": formatted,
            })

        st.dataframe(
            pd.DataFrame(detail_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### جودة البيانات والمصادر")

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
            f"حالة السعر: "
            f"{row.get('market_status', 'غير متاح')}"
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
            st.markdown("### ملاحظات")

            for note in notes:
                st.write(f"- {note}")

        st.markdown("### الموقع الرسمي وروابط التقارير")

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
            st.markdown("**تقارير وملفات محتملة:**")

            for item in report_links:
                st.markdown(
                    f"- [{item['text']}]({item['url']})"
                )

        if not investor_links and not report_links:
            st.info(
                "لم يتم العثور على روابط تقارير مناسبة أثناء الفحص. "
                "قد تكون التقارير موجودة في صفحات لم يتم اكتشافها."
            )

    # --------------------------------------------------------
    # Data-quality monitoring
    # --------------------------------------------------------

    st.markdown("## 🧪 مراقبة جودة البيانات")

    quality_columns = [
        "symbol",
        "name_ar",
        "market_status",
        "statement_status",
        "website_status",
        "data_quality",
        "analysis_status",
        "retrieved_at",
    ]

    quality_columns = [
        col for col in quality_columns
        if col in df.columns
    ]

    quality_df = df[quality_columns].rename(
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
        quality_df,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # CSV export
    # --------------------------------------------------------

    st.markdown("## 📥 تصدير النتائج")

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
        col for col in export_columns
        if col in df.columns
    ]

    export_df = df[export_columns].copy()

    csv_data = export_df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")

    st.download_button(
        "⬇️ تحميل نتائج التحليل CSV",
        data=csv_data,
        file_name="EGX_Banks_Financial_Analysis.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("عرض جميع البيانات الخام"):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

else:
    st.info(
        "لم تظهر نتائج حتى الآن. اضغط تشغيل التحليل، "
        "ثم تحقق من رسائل الخطأ إن تعذر الوصول للمصادر."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"{APP_NAME} v{APP_VERSION} | {now_utc()}"
)

st.caption(
    "التحليل لأغراض المعلومات الأولية فقط، وليس توصية استثمارية. "
    "تحقق من القوائم المالية الأصلية وتواريخها وعملتها ووحداتها "
    "قبل اتخاذ أي قرار."
    )
