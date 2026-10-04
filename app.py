# ============================================================
# EGX INSTITUTIONAL V5.2
# Financial + Valuation + Technical Stock Analyzer
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Any, Optional


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="EGX Institutional V5.2",
    page_icon="🏛️",
    layout="wide"
)


# ============================================================
# SETTINGS
# ============================================================

CACHE_TTL = 1800
MAX_WORKERS = 8

DEFAULT_WACC = 0.14
DEFAULT_TERMINAL_GROWTH = 0.04

# ============================================================
# EGX UNIVERSE
# ============================================================

RAW = '''
COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE
EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI
NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM
KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO
ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK
ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT
AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE
FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL
EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN
KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM
ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH
EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC
ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS
AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE
FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC
AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC
NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN MPCO ELSH MEPA ODIN
EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR
TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH
'''.split()

STOCKS = list(dict.fromkeys(x + ".CA" for x in RAW))


# ============================================================
# SECTORS
# ============================================================

BANKS = set(
    '''
    COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB
    UBEE
    '''.split()
)

RE = set(
    '''
    PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD
    DCRC ARCC RMDA IDRE RREI EGREF EHDR MENA MPRC
    '''.split()
)

HEALTH = set(
    '''
    BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH
    '''.split()
)

TECH = set(
    '''
    ETEL MTIE RAYA EFIH DGTZ GOUR
    '''.split()
)

ENERGY = set(
    '''
    AMOC SKPC EGAS TAQA MOIL GPIM EGAL ELSH MEPA
    '''.split()
)

CONSUMER = set(
    '''
    DOMT EAST JUFO SUGR POUL OLFI AJWA MICH UEGC ISMA
    FERC
    '''.split()
)

CONSTRUCTION = set(
    '''
    ORAS ENGC SVCE ARAB ELNA UPMS UNIT NCCW RACC PRCL AIDC
    '''.split()
)

FIN = set(
    '''
    EFIH BTFH VALU OFH CNFN MCQE ADCI ACAP FAIT AFDI UBEE
    FAITA AIFI AMIA AMII ATLC BINV DIFC
    '''.split()
)

INDUSTRIAL = set(
    x for x in RAW
    if x not in (
        BANKS |
        RE |
        HEALTH |
        TECH |
        ENERGY |
        CONSUMER |
        CONSTRUCTION |
        FIN
    )
)


def get_sector(symbol: str) -> str:

    s = symbol.upper().replace(".CA", "")

    if s in BANKS:
        return "Banks"

    if s in RE:
        return "Real Estate"

    if s in HEALTH:
        return "Healthcare"

    if s in TECH:
        return "Telecom & Technology"

    if s in ENERGY:
        return "Energy & Petrochemicals"

    if s in CONSUMER:
        return "Consumer"

    if s in CONSTRUCTION:
        return "Construction & Engineering"

    if s in FIN:
        return "Financial Services"

    return "Industrial & Materials"


# ============================================================
# SECTOR RULES
# ============================================================

SECTOR_RULES = {

    "Banks": [
        "ROE", "ROA", "NIM", "Cost/Income",
        "NPL", "NPL Coverage", "CAR",
        "Loan Growth", "Deposit Growth",
        "Net Income Growth", "P/B", "P/E",
        "Dividend Yield"
    ],

    "Real Estate": [
        "Revenue Growth", "EPS Growth",
        "EBITDA Margin", "Net Margin",
        "ROE", "Debt/Equity",
        "Net Debt/EBITDA",
        "Operating Cash Flow",
        "FCF Margin",
        "P/B", "P/E"
    ],

    "Healthcare": [
        "Revenue Growth", "EPS Growth",
        "Net Margin", "EBITDA Margin",
        "ROE", "ROA", "FCF Margin",
        "Debt/Equity", "Current Ratio",
        "P/E", "P/B"
    ],

    "Telecom & Technology": [
        "Revenue Growth", "EPS Growth",
        "EBITDA Margin", "Net Margin",
        "ROIC", "FCF Margin",
        "Net Debt/EBITDA", "ROE",
        "P/E", "EV/EBITDA",
        "Dividend Yield"
    ],

    "Energy & Petrochemicals": [
        "Revenue Growth", "EPS Growth",
        "EBITDA Margin", "Net Margin",
        "ROIC", "FCF Margin",
        "Debt/Equity", "Net Debt/EBITDA",
        "ROE", "P/E", "EV/EBITDA",
        "Dividend Yield"
    ],

    "Consumer": [
        "Revenue Growth", "EPS Growth",
        "Gross Margin", "EBITDA Margin",
        "Net Margin", "ROE", "ROIC",
        "FCF Margin", "Debt/Equity",
        "P/E", "Dividend Yield"
    ],

    "Construction & Engineering": [
        "Revenue Growth", "EBITDA Margin",
        "Net Margin", "ROE", "ROIC",
        "Operating Cash Flow",
        "FCF Margin", "Debt/Equity",
        "Net Debt/EBITDA", "P/E", "P/B"
    ],

    "Industrial & Materials": [
        "Revenue Growth", "EPS Growth",
        "Gross Margin", "EBITDA Margin",
        "Net Margin", "ROE", "ROIC",
        "FCF Margin", "Debt/Equity",
        "Net Debt/EBITDA", "P/E",
        "P/B", "Dividend Yield"
    ],

    "Financial Services": [
        "Revenue Growth", "Net Income Growth",
        "ROE", "ROA", "Net Margin",
        "Debt/Equity", "Current Ratio",
        "P/E", "P/B", "Dividend Yield"
    ],

    "General": [
        "Revenue Growth", "EPS Growth",
        "Net Margin", "ROE", "ROA",
        "ROIC", "FCF Margin",
        "Debt/Equity", "Current Ratio",
        "P/E", "P/B", "Dividend Yield"
    ]
}


# ============================================================
# FIXED WEIGHTS
# ============================================================

WEIGHTS = {
    sector_name: {
        metric: 1.0 / len(metrics)
        for metric in metrics
    }
    for sector_name, metrics in SECTOR_RULES.items()
}

WEIGHTS["Banks"] = {
    "ROE": .15,
    "ROA": .07,
    "NIM": .12,
    "Cost/Income": .10,
    "NPL": .10,
    "NPL Coverage": .07,
    "CAR": .10,
    "Loan Growth": .07,
    "Deposit Growth": .05,
    "Net Income Growth": .08,
    "P/B": .05,
    "P/E": .02,
    "Dividend Yield": .02
}


# ============================================================
# HELPERS
# ============================================================

def num(x):

    try:
        x = float(x)

        if np.isfinite(x):
            return x

        return np.nan

    except Exception:
        return np.nan


def safe_div(a, b):

    a = num(a)
    b = num(b)

    if pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan

    return a / b


def clean_series(s):

    if s is None:
        return None

    try:

        x = pd.to_numeric(s, errors="coerce").dropna()

        if x.empty:
            return None

        if hasattr(x.index, "to_datetime"):

            try:
                idx = pd.to_datetime(x.index)

                x.index = idx
                x = x.sort_index(ascending=False)

            except Exception:
                pass

        return x

    except Exception:
        return None


def latest(s):

    x = clean_series(s)

    if x is None or len(x) == 0:
        return np.nan

    return num(x.iloc[0])


def previous(s):

    x = clean_series(s)

    if x is None or len(x) < 2:
        return np.nan

    return num(x.iloc[1])


def growth(s):

    x = clean_series(s)

    if x is None or len(x) < 2:
        return np.nan

    latest_value = num(x.iloc[0])
    old_value = num(x.iloc[1])

    if pd.isna(latest_value) or pd.isna(old_value):
        return np.nan

    if old_value == 0:
        return np.nan

    return (latest_value / old_value - 1.0) * 100.0


def pct(x):

    x = num(x)

    if pd.isna(x):
        return np.nan

    return x * 100.0


def safe_mean(values):

    vals = []

    for x in values:

        x = num(x)

        if pd.notna(x):
            vals.append(x)

    if not vals:
        return np.nan

    return float(np.mean(vals))


def find(df, names):

    if df is None or df.empty:
        return None

    # Exact
    for name in names:

        if name in df.index:
            return pd.to_numeric(
                df.loc[name],
                errors="coerce"
            )

    # Case-insensitive / partial
    for idx in df.index:

        low = str(idx).lower().strip()

        for name in names:

            nlow = str(name).lower().strip()

            if nlow in low or low in nlow:

                return pd.to_numeric(
                    df.loc[idx],
                    errors="coerce"
                )

    return None


def first_valid(*values):

    for value in values:

        x = num(value)

        if pd.notna(x):
            return x

    return np.nan


def clip(x, low, high):

    x = num(x)

    if pd.isna(x):
        return np.nan

    return float(np.clip(x, low, high))


# ============================================================
# DATA SOURCE
# ============================================================

@dataclass
class SourceResult:

    source: str
    ok: bool
    data: Any = None
    error: str = ""


class DataSourceManager:

    def __init__(self, ticker):

        self.ticker = ticker

    def yahoo(self):

        ticker = yf.Ticker(self.ticker)

        info = {}

        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        try:
            financials = ticker.financials
        except Exception:
            financials = pd.DataFrame()

        try:
            balance = ticker.balance_sheet
        except Exception:
            balance = pd.DataFrame()

        try:
            cashflow = ticker.cashflow
        except Exception:
            cashflow = pd.DataFrame()

        try:
            quarterly_financials = ticker.quarterly_financials
        except Exception:
            quarterly_financials = pd.DataFrame()

        try:
            quarterly_balance = ticker.quarterly_balance_sheet
        except Exception:
            quarterly_balance = pd.DataFrame()

        try:
            quarterly_cashflow = ticker.quarterly_cashflow
        except Exception:
            quarterly_cashflow = pd.DataFrame()

        try:
            history = ticker.history(
                period="5y",
                interval="1d",
                auto_adjust=False
            )
        except Exception:
            history = pd.DataFrame()

        return SourceResult(
            "Yahoo Finance",
            True,
            {
                "ticker": ticker,
                "info": info,
                "financials": financials,
                "balance": balance,
                "cashflow": cashflow,
                "quarterly_financials": quarterly_financials,
                "quarterly_balance": quarterly_balance,
                "quarterly_cashflow": quarterly_cashflow,
                "history": history
            }
        )

    def load(self):

        try:

            result = self.yahoo()

            return result

        except Exception as e:

            return SourceResult(
                "Yahoo Finance",
                False,
                error=str(e)
            )


# ============================================================
# TTM
# ============================================================

def ttm_sum(series):

    x = clean_series(series)

    if x is None:
        return np.nan

    if len(x) < 4:
        return np.nan

    return float(x.iloc[:4].sum())


# ============================================================
# NORMALIZE FINANCIAL DATA
# ============================================================

def normalize_financials(data):

    info = data.get("info", {}) or {}

    financials = data.get(
        "financials",
        pd.DataFrame()
    )

    balance = data.get(
        "balance",
        pd.DataFrame()
    )

    cashflow = data.get(
        "cashflow",
        pd.DataFrame()
    )

    q_fin = data.get(
        "quarterly_financials",
        pd.DataFrame()
    )

    q_bal = data.get(
        "quarterly_balance",
        pd.DataFrame()
    )

    q_cf = data.get(
        "quarterly_cashflow",
        pd.DataFrame()
    )

    history = data.get(
        "history",
        pd.DataFrame()
    )

    # --------------------------------------------------------
    # CURRENT PRICE
    # --------------------------------------------------------

    price = np.nan

    if history is not None and not history.empty:

        try:

            h = history.copy()

            if "Close" in h.columns:

                close = pd.to_numeric(
                    h["Close"],
                    errors="coerce"
                ).dropna()

                if not close.empty:

                    price = num(close.iloc[-1])

        except Exception:
            pass

    if pd.isna(price):

        price = first_valid(
            info.get("currentPrice"),
            info.get("regularMarketPrice"),
            info.get("previousClose")
        )

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue_s = find(
        financials,
        [
            "Total Revenue",
            "Operating Revenue",
            "Revenue"
        ]
    )

    revenue = latest(revenue_s)
    revenue_growth = growth(revenue_s)

    # --------------------------------------------------------
    # NET INCOME
    # --------------------------------------------------------

    ni_s = find(
        financials,
        [
            "Net Income",
            "Net Income Common Stockholders",
            "Net Income Including Noncontrolling Interests"
        ]
    )

    net_income = latest(ni_s)
    net_income_growth = growth(ni_s)

    # --------------------------------------------------------
    # EBIT
    # --------------------------------------------------------

    ebit_s = find(
        financials,
        [
            "EBIT",
            "Operating Income",
            "Operating Income Or Loss"
        ]
    )

    ebit = latest(ebit_s)

    # --------------------------------------------------------
    # EBITDA
    # --------------------------------------------------------

    ebitda_s = find(
        financials,
        [
            "EBITDA",
            "Normalized EBITDA"
        ]
    )

    ebitda = latest(ebitda_s)

    # Fallback EBITDA
    if pd.isna(ebitda) and pd.notna(ebit):

        da_tmp = latest(
            find(
                cashflow,
                [
                    "Depreciation And Amortization",
                    "Depreciation",
                    "Depreciation And Amortization In Cash Flow"
                ]
            )
        )

        if pd.notna(da_tmp):

            ebitda = ebit + abs(da_tmp)

    # --------------------------------------------------------
    # GROSS PROFIT
    # --------------------------------------------------------

    gross_profit = latest(
        find(
            financials,
            [
                "Gross Profit"
            ]
        )
    )

    # --------------------------------------------------------
    # BALANCE SHEET
    # --------------------------------------------------------

    equity = latest(
        find(
            balance,
            [
                "Stockholders Equity",
                "Total Stockholder Equity",
                "Total Equity Gross Minority Interest"
            ]
        )
    )

    assets = latest(
        find(
            balance,
            [
                "Total Assets"
            ]
        )
    )

    debt = latest(
        find(
            balance,
            [
                "Total Debt",
                "Long Term Debt And Capital Lease Obligation",
                "Long Term Debt",
                "Current Debt"
            ]
        )
    )

    cash = latest(
        find(
            balance,
            [
                "Cash Cash Equivalents And Short Term Investments",
                "Cash And Cash Equivalents",
                "Cash Financial"
            ]
        )
    )

    current_assets = latest(
        find(
            balance,
            [
                "Current Assets",
                "Total Current Assets"
            ]
        )
    )

    current_liabilities = latest(
        find(
            balance,
            [
                "Current Liabilities",
                "Total Current Liabilities"
            ]
        )
    )

    working_capital = np.nan

    if (
        pd.notna(current_assets)
        and pd.notna(current_liabilities)
    ):

        working_capital = (
            current_assets -
            current_liabilities
        )

    retained_earnings = latest(
        find(
            balance,
            [
                "Retained Earnings",
                "Retained Earnings Common Stockholders",
                "Retained Earnings Accumulated Deficit"
            ]
        )
    )

    # --------------------------------------------------------
    # CASH FLOW
    # --------------------------------------------------------

    ocf_s = find(
        cashflow,
        [
            "Operating Cash Flow",
            "Total Cash From Operating Activities",
            "Cash Flow From Continuing Operating Activities"
        ]
    )

    ocf = latest(ocf_s)

    capex_s = find(
        cashflow,
        [
            "Capital Expenditure",
            "Capital Expenditures",
            "Capital Expenditure Reported"
        ]
    )

    capex = latest(capex_s)

    da = latest(
        find(
            cashflow,
            [
                "Depreciation And Amortization",
                "Depreciation",
                "Depreciation And Amortization In Cash Flow"
            ]
        )
    )

    # --------------------------------------------------------
    # FCF
    # --------------------------------------------------------

    fcf = np.nan

    if pd.notna(ocf) and pd.notna(capex):

        fcf = ocf - abs(capex)

    # Sometimes Yahoo reports capex as positive
    if pd.notna(ocf) and pd.notna(capex):

        alt_fcf = ocf + capex

        if pd.isna(fcf) or (
            pd.notna(alt_fcf)
            and alt_fcf > fcf
            and capex < 0
        ):
            fcf = alt_fcf

    # --------------------------------------------------------
    # SHARES
    # --------------------------------------------------------

    shares = first_valid(
        info.get("sharesOutstanding"),
        info.get("impliedSharesOutstanding")
    )

    if (
        pd.isna(shares)
        and pd.notna(info.get("marketCap"))
        and pd.notna(price)
        and price > 0
    ):

        shares = info.get("marketCap") / price

    # --------------------------------------------------------
    # EPS
    # --------------------------------------------------------

    eps = first_valid(
        info.get("trailingEps"),
        info.get("epsTrailingTwelveMonths")
    )

    if pd.isna(eps) and pd.notna(net_income) and pd.notna(shares):

        eps = safe_div(
            net_income,
            shares
        )

    eps_growth = np.nan

    eps_s = find(
        financials,
        [
            "Diluted EPS",
            "Basic EPS",
            "Diluted EPS From Continuing Operations"
        ]
    )

    eps_growth = growth(eps_s)

    # --------------------------------------------------------
    # MARKET CAP
    # --------------------------------------------------------

    market_cap = first_valid(
        info.get("marketCap")
    )

    if (
        pd.isna(market_cap)
        and pd.notna(shares)
        and pd.notna(price)
    ):

        market_cap = shares * price

    # --------------------------------------------------------
    # RATIOS
    # --------------------------------------------------------

    revenue_base = revenue

    net_margin = safe_div(
        net_income,
        revenue_base
    )

    gross_margin = safe_div(
        gross_profit,
        revenue_base
    )

    ebitda_margin = safe_div(
        ebitda,
        revenue_base
    )

    fcf_margin = safe_div(
        fcf,
        revenue_base
    )

    roe = safe_div(
        net_income,
        equity
    )

    roa = safe_div(
        net_income,
        assets
    )

    invested_capital = np.nan

    if pd.notna(equity) and pd.notna(debt):

        invested_capital = (
            equity +
            debt -
            (cash if pd.notna(cash) else 0)
        )

    roic = np.nan

    if (
        pd.notna(ebit)
        and pd.notna(invested_capital)
        and invested_capital > 0
    ):

        tax_rate = first_valid(
            info.get("effectiveTaxRate"),
            0.22
        )

        nopat = ebit * (
            1 - np.clip(tax_rate, 0, 0.40)
        )

        roic = safe_div(
            nopat,
            invested_capital
        )

    debt_equity = safe_div(
        debt,
        equity
    )

    net_debt = np.nan

    if pd.notna(debt):

        net_debt = debt - (
            cash if pd.notna(cash)
            else 0
        )

    net_debt_ebitda = safe_div(
        net_debt,
        ebitda
    )

    current_ratio = safe_div(
        current_assets,
        current_liabilities
    )

    bvps = safe_div(
        equity,
        shares
    )

    pe = safe_div(
        price,
        eps
    )

    pb = safe_div(
        price,
        bvps
    )

    ev = np.nan

    if pd.notna(market_cap):

        ev = market_cap + (
            debt if pd.notna(debt) else 0
        ) - (
            cash if pd.notna(cash) else 0
        )

    ev_ebitda = safe_div(
        ev,
        ebitda
    )

    dividend_yield = first_valid(
        pct(info.get("dividendYield"))
    )

    # Yahoo may already give percentage-like value
    if pd.notna(dividend_yield) and dividend_yield < 1:
        dividend_yield *= 100

    # --------------------------------------------------------
    # BANK METRICS
    # --------------------------------------------------------

    nim = first_valid(
        pct(info.get("netInterestMargin"))
    )

    cost_income = first_valid(
        pct(info.get("costIncomeRatio"))
    )

    npl = first_valid(
        pct(info.get("nonPerformingLoansRatio"))
    )

    npl_coverage = first_valid(
        pct(info.get("nplCoverageRatio"))
    )

    car = first_valid(
        pct(info.get("capitalAdequacyRatio"))
    )

    loan_growth = first_valid(
        pct(info.get("loanGrowth"))
    )

    deposit_growth = first_valid(
        pct(info.get("depositGrowth"))
    )

    return {

        "Price": price,
        "Market Cap": market_cap,
        "Shares": shares,

        "Revenue": revenue,
        "Revenue Growth": revenue_growth,

        "Net Income": net_income,
        "Net Income Growth": net_income_growth,

        "EPS": eps,
        "EPS Growth": eps_growth,

        "Equity": equity,
        "Assets": assets,
        "Debt": debt,
        "Cash": cash,

        "Current Assets": current_assets,
        "Current Liabilities": current_liabilities,
        "Working Capital": working_capital,
        "Retained Earnings": retained_earnings,

        "Operating Cash Flow": ocf,
        "CAPEX": capex,
        "D&A": da,
        "FCF": fcf,

        "EBIT": ebit,
        "EBITDA": ebitda,
        "Gross Profit": gross_profit,

        "Gross Margin": pct(gross_margin),
        "EBITDA Margin": pct(ebitda_margin),
        "Net Margin": pct(net_margin),
        "FCF Margin": pct(fcf_margin),

        "ROE": pct(roe),
        "ROA": pct(roa),
        "ROIC": pct(roic),

        "Debt/Equity": debt_equity,
        "Net Debt/EBITDA": net_debt_ebitda,
        "Current Ratio": current_ratio,

        "BVPS": bvps,

        "P/E": pe,
        "P/B": pb,
        "EV": ev,
        "EV/EBITDA": ev_ebitda,

        "Dividend Yield": dividend_yield,

        "NIM": nim,
        "Cost/Income": cost_income,
        "NPL": npl,
        "NPL Coverage": npl_coverage,
        "CAR": car,
        "Loan Growth": loan_growth,
        "Deposit Growth": deposit_growth
    }


# ============================================================
# FCFF ENGINE
# ============================================================

def calculate_fcff(m):

    ebit = num(m.get("EBIT"))
    da = num(m.get("D&A"))
    capex = num(m.get("CAPEX"))
    ocf = num(m.get("Operating Cash Flow"))
    fcf = num(m.get("FCF"))
    wc = num(m.get("Working Capital"))

    debt = num(m.get("Debt"))
    cash = num(m.get("Cash"))

    tax_rate = 0.22

    if pd.notna(ebit):

        nopat = ebit * (
            1 - np.clip(
                tax_rate,
                0.00,
                0.40
            )
        )

    else:

        nopat = np.nan

    # --------------------------------------------------------
    # METHOD 1: TRUE FCFF
    # --------------------------------------------------------

    if (
        pd.notna(nopat)
        and pd.notna(da)
        and pd.notna(capex)
    ):

        fcff = (
            nopat +
            abs(da) -
            abs(capex)
        )

        if pd.notna(fcff) and fcff > 0:

            return {
                "fcff": float(fcff),
                "method": "True FCFF",
                "quality": "High"
            }

    # --------------------------------------------------------
    # METHOD 2: NOPAT + D&A - CAPEX
    # --------------------------------------------------------

    if (
        pd.notna(nopat)
        and pd.notna(da)
        and pd.notna(capex)
    ):

        fcff = (
            nopat +
            abs(da) -
            abs(capex)
        )

        if pd.notna(fcff) and fcff > 0:

            return {
                "fcff": float(fcff),
                "method": "FCFF Proxy",
                "quality": "Medium"
            }

    # --------------------------------------------------------
    # METHOD 3: FCF
    # --------------------------------------------------------

    if pd.notna(fcf) and fcf > 0:

        return {
            "fcff": float(fcf),
            "method": "FCF Proxy",
            "quality": "Medium"
        }

    # --------------------------------------------------------
    # METHOD 4: OCF AFTER CAPEX
    # --------------------------------------------------------

    if pd.notna(ocf) and ocf > 0:

        if pd.notna(capex):

            proxy = ocf - abs(capex)

            if proxy > 0:

                return {
                    "fcff": float(proxy),
                    "method": "OCF-CAPEX Proxy",
                    "quality": "Medium-Low"
                }

        # OCF haircut if CAPEX unavailable
        proxy = ocf * 0.65

        return {
            "fcff": float(proxy),
            "method": "OCF Haircut Proxy",
            "quality": "Low"
        }

    # --------------------------------------------------------
    # METHOD 5: NET INCOME FALLBACK
    # --------------------------------------------------------

    ni = num(m.get("Net Income"))

    if pd.notna(ni) and ni > 0:

        proxy = ni * 0.65

        return {
            "fcff": float(proxy),
            "method": "Net Income Proxy",
            "quality": "Very Low"
        }

    return {
        "fcff": np.nan,
        "method": "Unavailable",
        "quality": "None"
    }


# ============================================================
# SCENARIO ASSUMPTIONS
# ============================================================

def scenario_assumptions(m):

    revenue_growth = num(
        m.get("Revenue Growth")
    )

    ebitda_margin = num(
        m.get("EBITDA Margin")
    )

    fcf_margin = num(
        m.get("FCF Margin")
    )

    # -----------------------------
    # Growth
    # -----------------------------

    if pd.isna(revenue_growth):

        base_growth = 0.08

    else:

        base_growth = (
            revenue_growth / 100.0
        )

        base_growth = np.clip(
            base_growth,
            -0.05,
            0.20
        )

    conservative_growth = np.clip(
        base_growth - 0.04,
        -0.08,
        0.15
    )

    base_growth = np.clip(
        base_growth,
        -0.03,
        0.18
    )

    optimistic_growth = np.clip(
        base_growth + 0.04,
        0.00,
        0.25
    )

    # -----------------------------
    # FCF Margin
    # -----------------------------

    if pd.notna(fcf_margin):

        base_margin = np.clip(
            fcf_margin / 100.0,
            0.02,
            0.35
        )

    elif pd.notna(ebitda_margin):

        base_margin = np.clip(
            (
                ebitda_margin / 100.0
            ) * 0.45,
            0.02,
            0.30
        )

    else:

        base_margin = 0.08

    conservative_margin = max(
        0.02,
        base_margin * 0.75
    )

    optimistic_margin = min(
        0.40,
        base_margin * 1.20
    )

    return {

        "Conservative": {
            "growth": conservative_growth,
            "margin": conservative_margin,
            "wacc": 0.16,
            "terminal": 0.035
        },

        "Base": {
            "growth": base_growth,
            "margin": base_margin,
            "wacc": 0.14,
            "terminal": 0.04
        },

        "Optimistic": {
            "growth": optimistic_growth,
            "margin": optimistic_margin,
            "wacc": 0.125,
            "terminal": 0.045
        }
    }


# ============================================================
# DCF SCENARIO
# ============================================================

def dcf_scenario(
    m,
    scenario,
    years=5
):

    fcff_data = calculate_fcff(m)

    base_fcff = num(
        fcff_data.get("fcff")
    )

    shares = num(
        m.get("Shares")
    )

    debt = num(
        m.get("Debt")
    )

    cash = num(
        m.get("Cash")
    )

    revenue = num(
        m.get("Revenue")
    )

    if (
        pd.isna(base_fcff)
        or base_fcff <= 0
        or pd.isna(shares)
        or shares <= 0
    ):

        return {
            "value": np.nan,
            "enterprise": np.nan,
            "fcff": base_fcff,
            "method": fcff_data.get("method"),
            "quality": fcff_data.get("quality")
        }

    assumptions = scenario_assumptions(m)

    a = assumptions[scenario]

    growth_rate = a["growth"]
    margin = a["margin"]
    wacc = a["wacc"]
    terminal_growth = a["terminal"]

    # --------------------------------------------------------
    # Use actual FCFF as anchor.
    # Then allow scenario-specific growth.
    # --------------------------------------------------------

    cur_fcff = base_fcff

    pv = 0.0

    growth_fade = []

    for i in range(1, years + 1):

        fade = (i - 1) / max(
            years - 1,
            1
        )

        # Fade growth toward terminal growth
        g = (
            growth_rate * (1 - fade * 0.55)
            + terminal_growth * (fade * 0.55)
        )

        g = np.clip(
            g,
            -0.10,
            0.25
        )

        growth_fade.append(g)

        cur_fcff *= (
            1 + g
        )

        pv += (
            cur_fcff /
            ((1 + wacc) ** i)
        )

    # --------------------------------------------------------
    # Terminal value
    # --------------------------------------------------------

    if wacc <= terminal_growth:

        return {
            "value": np.nan,
            "enterprise": np.nan,
            "fcff": base_fcff,
            "method": fcff_data.get("method"),
            "quality": fcff_data.get("quality")
        }

    terminal_fcff = (
        cur_fcff *
        (1 + terminal_growth)
    )

    terminal_value = (
        terminal_fcff /
        (wacc - terminal_growth)
    )

    pv_terminal = (
        terminal_value /
        ((1 + wacc) ** years)
    )

    enterprise_value = (
        pv +
        pv_terminal
    )

    equity_value = (
        enterprise_value -
        (debt if pd.notna(debt) else 0) +
        (cash if pd.notna(cash) else 0)
    )

    fair_value = safe_div(
        equity_value,
        shares
    )

    return {

        "value": fair_value,

        "enterprise": enterprise_value,

        "fcff": base_fcff,

        "method": fcff_data.get(
            "method"
        ),

        "quality": fcff_data.get(
            "quality"
        ),

        "growth": growth_rate,

        "margin": margin,

        "wacc": wacc,

        "terminal": terminal_growth
    }


# ============================================================
# RELATIVE VALUATION
# ============================================================

SECTOR_MULTIPLES = {

    "Banks": {
        "PE": 10.0,
        "PB": 1.35,
        "EVEBITDA": np.nan
    },

    "Financial Services": {
        "PE": 11.0,
        "PB": 1.50,
        "EVEBITDA": 10.0
    },

    "Real Estate": {
        "PE": 12.0,
        "PB": 1.50,
        "EVEBITDA": 9.0
    },

    "Healthcare": {
        "PE": 15.0,
        "PB": 2.00,
        "EVEBITDA": 12.0
    },

    "Telecom & Technology": {
        "PE": 14.0,
        "PB": 2.00,
        "EVEBITDA": 9.0
    },

    "Energy & Petrochemicals": {
        "PE": 9.0,
        "PB": 1.30,
        "EVEBITDA": 6.5
    },

    "Consumer": {
        "PE": 13.0,
        "PB": 1.70,
        "EVEBITDA": 9.0
    },

    "Construction & Engineering": {
        "PE": 11.0,
        "PB": 1.50,
        "EVEBITDA": 8.0
    },

    "Industrial & Materials": {
        "PE": 11.0,
        "PB": 1.50,
        "EVEBITDA": 8.0
    }
}


def relative_valuation(m, sector):

    price = num(
        m.get("Price")
    )

    eps = num(
        m.get("EPS")
    )

    bvps = num(
        m.get("BVPS")
    )

    ebitda = num(
        m.get("EBITDA")
    )

    debt = num(
        m.get("Debt")
    )

    cash = num(
        m.get("Cash")
    )

    shares = num(
        m.get("Shares")
    )

    revenue = num(
        m.get("Revenue")
    )

    market_cap = num(
        m.get("Market Cap")
    )

    ref = SECTOR_MULTIPLES.get(
        sector,
        SECTOR_MULTIPLES["Industrial & Materials"]
    )

    # --------------------------------------------------------
    # P/E
    # --------------------------------------------------------

    pe_fair = np.nan

    if pd.notna(eps) and eps > 0:

        pe_fair = (
            eps *
            ref["PE"]
        )

    # --------------------------------------------------------
    # P/B
    # --------------------------------------------------------

    pb_fair = np.nan

    if pd.notna(bvps) and bvps > 0:

        pb_fair = (
            bvps *
            ref["PB"]
        )

    # --------------------------------------------------------
    # EV / EBITDA
    # --------------------------------------------------------

    ev_ebitda_fair = np.nan

    if (
        pd.notna(ebitda)
        and ebitda > 0
        and pd.notna(shares)
        and shares > 0
        and pd.notna(ref["EVEBITDA"])
    ):

        target_ev = (
            ebitda *
            ref["EVEBITDA"]
        )

        equity_value = (
            target_ev -
            (debt if pd.notna(debt) else 0) +
            (cash if pd.notna(cash) else 0)
        )

        ev_ebitda_fair = safe_div(
            equity_value,
            shares
        )

    # --------------------------------------------------------
    # Different scenarios
    # --------------------------------------------------------

    # Conservative
    conservative_values = []

    if pd.notna(pe_fair):
        conservative_values.append(
            pe_fair * 0.85
        )

    if pd.notna(pb_fair):
        conservative_values.append(
            pb_fair * 0.90
        )

    if pd.notna(ev_ebitda_fair):
        conservative_values.append(
            ev_ebitda_fair * 0.85
        )

    relative_conservative = (
        np.nanmedian(conservative_values)
        if conservative_values
        else np.nan
    )

    # Base
    base_values = [
        x for x in [
            pe_fair,
            pb_fair,
            ev_ebitda_fair
        ]
        if pd.notna(x) and x > 0
    ]

    relative_base = (
        np.nanmedian(base_values)
        if base_values
        else np.nan
    )

    # Optimistic
    optimistic_values = []

    if pd.notna(pe_fair):
        optimistic_values.append(
            pe_fair * 1.15
        )

    if pd.notna(pb_fair):
        optimistic_values.append(
            pb_fair * 1.10
        )

    if pd.notna(ev_ebitda_fair):
        optimistic_values.append(
            ev_ebitda_fair * 1.15
        )

    relative_optimistic = (
        np.nanmedian(optimistic_values)
        if optimistic_values
        else np.nan
    )

    return {

        "P/E FV": pe_fair,
        "P/B FV": pb_fair,
        "EV/EBITDA FV": ev_ebitda_fair,

        "Relative Conservative":
            relative_conservative,

        "Relative Base":
            relative_base,

        "Relative Optimistic":
            relative_optimistic,

        "PE Reference":
            ref["PE"],

        "PB Reference":
            ref["PB"],

        "EV/EBITDA Reference":
            ref["EVEBITDA"]
    }


# ============================================================
# FINAL VALUATION
# ============================================================

def valuation_engine(m, sector):

    price = num(
        m.get("Price")
    )

    dcf_c = dcf_scenario(
        m,
        "Conservative"
    )

    dcf_b = dcf_scenario(
        m,
        "Base"
    )

    dcf_o = dcf_scenario(
        m,
        "Optimistic"
    )

    rel = relative_valuation(
        m,
        sector
    )

    is_bank = sector == "Banks"

    # --------------------------------------------------------
    # Bank valuation
    # --------------------------------------------------------

    if is_bank:

        dcf_weight = 0.15
        relative_weight = 0.85

    else:

        dcf_weight = 0.65
        relative_weight = 0.35

    def blend(dcf_value, relative_value):

        d = num(dcf_value)
        r = num(relative_value)

        if pd.notna(d) and pd.notna(r):

            return (
                d * dcf_weight +
                r * relative_weight
            )

        if pd.notna(d):
            return d

        if pd.notna(r):
            return r

        return np.nan

    fair_conservative = blend(
        dcf_c.get("value"),
        rel.get("Relative Conservative")
    )

    fair_base = blend(
        dcf_b.get("value"),
        rel.get("Relative Base")
    )

    fair_optimistic = blend(
        dcf_o.get("value"),
        rel.get("Relative Optimistic")
    )

    # --------------------------------------------------------
    # Safety correction:
    # scenarios MUST remain ordered
    # --------------------------------------------------------

    scenario_values = [
        fair_conservative,
        fair_base,
        fair_optimistic
    ]

    valid = [
        x for x in scenario_values
        if pd.notna(x) and x > 0
    ]

    if len(valid) == 3:

        # Preserve ordering
        fair_conservative = min(
            fair_conservative,
            fair_base
        )

        fair_optimistic = max(
            fair_optimistic,
            fair_base
        )

    # If only base exists, create scenario bands.
    # This is NOT used when actual DCF scenario values exist.
    if pd.isna(fair_conservative) and pd.notna(fair_base):

        fair_conservative = fair_base * 0.80

    if pd.isna(fair_optimistic) and pd.notna(fair_base):

        fair_optimistic = fair_base * 1.20

    # --------------------------------------------------------
    # Buy prices
    # --------------------------------------------------------

    buy_20 = (
        fair_base * 0.80
        if pd.notna(fair_base)
        else np.nan
    )

    buy_30 = (
        fair_base * 0.70
        if pd.notna(fair_base)
        else np.nan
    )

    upside_base = np.nan

    if (
        pd.notna(fair_base)
        and pd.notna(price)
        and price > 0
    ):

        upside_base = (
            fair_base / price - 1
        ) * 100

    upside_conservative = np.nan

    if (
        pd.notna(fair_conservative)
        and pd.notna(price)
        and price > 0
    ):

        upside_conservative = (
            fair_conservative / price - 1
        ) * 100

    upside_optimistic = np.nan

    if (
        pd.notna(fair_optimistic)
        and pd.notna(price)
        and price > 0
    ):

        upside_optimistic = (
            fair_optimistic / price - 1
        ) * 100

    return {

        # DCF
        "DCF Conservative":
            dcf_c.get("value"),

        "DCF Base":
            dcf_b.get("value"),

        "DCF Optimistic":
            dcf_o.get("value"),

        # Relative
        "Relative Conservative":
            rel.get("Relative Conservative"),

        "Relative Base":
            rel.get("Relative Base"),

        "Relative Optimistic":
            rel.get("Relative Optimistic"),

        # Final
        "Fair Conservative":
            fair_conservative,

        "Fair Value":
            fair_base,

        "Fair Base":
            fair_base,

        "Fair Optimistic":
            fair_optimistic,

        # Buy
        "Buy 20% MOS":
            buy_20,

        "Strong Buy 30% MOS":
            buy_30,

        # Upside
        "Upside Conservative %":
            upside_conservative,

        "Upside %":
            upside_base,

        "Upside Optimistic %":
            upside_optimistic,

        # Method
        "FCFF Method":
            dcf_b.get("method"),

        "FCFF Quality":
            dcf_b.get("quality"),

        # Weights
        "DCF Weight":
            dcf_weight,

        "Relative Weight":
            relative_weight
    }


# ============================================================
# PIOTROSKI STYLE SCREEN
# ============================================================

def piotroski_style(m):

    score = 0

    checks = 0

    tests = []

    def test(name, condition):

        nonlocal score, checks

        if condition is None:
            return

        checks += 1

        if condition:
            score += 1
            tests.append(
                (name, 1)
            )
        else:
            tests.append(
                (name, 0)
            )

    ni = num(m.get("Net Income"))
    ocf = num(m.get("Operating Cash Flow"))
    roe = num(m.get("ROE"))
    fcf = num(m.get("FCF"))
    net_margin = num(m.get("Net Margin"))
    debt_equity = num(m.get("Debt/Equity"))
    revenue_growth = num(m.get("Revenue Growth"))
    ni_growth = num(m.get("Net Income Growth"))
    eps_growth = num(m.get("EPS Growth"))

    test(
        "Positive Net Income",
        ni > 0 if pd.notna(ni) else None
    )

    test(
        "Positive Operating Cash Flow",
        ocf > 0 if pd.notna(ocf) else None
    )

    test(
        "Positive ROE",
        roe > 0 if pd.notna(roe) else None
    )

    test(
        "Positive FCF",
        fcf > 0 if pd.notna(fcf) else None
    )

    test(
        "Positive Net Margin",
        net_margin > 0 if pd.notna(net_margin) else None
    )

    test(
        "Controlled Leverage",
        debt_equity < 1.5
        if pd.notna(debt_equity)
        else None
    )

    test(
        "Revenue Growth",
        revenue_growth > 0
        if pd.notna(revenue_growth)
        else None
    )

    test(
        "Net Income Growth",
        ni_growth > 0
        if pd.notna(ni_growth)
        else None
    )

    test(
        "EPS Growth",
        eps_growth > 0
        if pd.notna(eps_growth)
        else None
    )

    return {
        "score": score,
        "max": checks,
        "tests": tests
    }


# ============================================================
# BENEISH PROXY
# ============================================================

def beneish_proxy(m):

    revenue_growth = num(
        m.get("Revenue Growth")
    )

    net_margin = num(
        m.get("Net Margin")
    )

    fcf_margin = num(
        m.get("FCF Margin")
    )

    debt_equity = num(
        m.get("Debt/Equity")
    )

    risk = 0

    if pd.notna(revenue_growth) and revenue_growth < -20:
        risk += 1

    if pd.notna(net_margin) and net_margin < 0:
        risk += 1

    if pd.notna(fcf_margin) and fcf_margin < -5:
        risk += 1

    if pd.notna(debt_equity) and debt_equity > 2.5:
        risk += 1

    return {
        "risk": risk,
        "label": (
            "Low"
            if risk <= 1
            else "Medium"
            if risk == 2
            else "High"
        )
    }


# ============================================================
# ALTMAN
# ============================================================

def altman_z(m):

    assets = num(
        m.get("Assets")
    )

    working_capital = num(
        m.get("Working Capital")
    )

    retained_earnings = num(
        m.get("Retained Earnings")
    )

    ebit = num(
        m.get("EBIT")
    )

    market_cap = num(
        m.get("Market Cap")
    )

    debt = num(
        m.get("Debt")
    )

    revenue = num(
        m.get("Revenue")
    )

    if (
        pd.isna(assets)
        or assets <= 0
    ):
        return np.nan

    if (
        pd.isna(debt)
        or debt <= 0
    ):
        return np.nan

    wc_a = safe_div(
        working_capital,
        assets
    )

    re_a = safe_div(
        retained_earnings,
        assets
    )

    ebit_a = safe_div(
        ebit,
        assets
    )

    mve_debt = safe_div(
        market_cap,
        debt
    )

    sales_a = safe_div(
        revenue,
        assets
    )

    if any(
        pd.isna(x)
        for x in [
            wc_a,
            re_a,
            ebit_a,
            mve_debt,
            sales_a
        ]
    ):
        return np.nan

    return (
        1.2 * wc_a +
        1.4 * re_a +
        3.3 * ebit_a +
        0.6 * mve_debt +
        1.0 * sales_a
    )


# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def technical_analysis(history):

    if (
        history is None
        or history.empty
        or "Close" not in history.columns
    ):

        return {}

    df = history.copy()

    close = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    volume = pd.to_numeric(
        df["Volume"],
        errors="coerce"
    )

    close = close.dropna()

    if len(close) < 30:
        return {}

    ema20 = close.ewm(
        span=20,
        adjust=False
    ).mean()

    ema50 = close.ewm(
        span=50,
        adjust=False
    ).mean()

    ema200 = close.ewm(
        span=200,
        adjust=False
    ).mean()

    # RSI
    delta = close.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.rolling(
        14
    ).mean()

    avg_loss = loss.rolling(
        14
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan
    )

    rsi = 100 - (
        100 / (1 + rs)
    )

    # MACD
    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    # ATR
    if all(
        x in df.columns
        for x in ["High", "Low"]
    ):

        high = pd.to_numeric(
            df["High"],
            errors="coerce"
        )

        low = pd.to_numeric(
            df["Low"],
            errors="coerce"
        )

        prev_close = close.shift(1)

        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs()
            ],
            axis=1
        ).max(axis=1)

        atr = tr.rolling(14).mean()

    else:

        atr = pd.Series(
            index=close.index,
            dtype=float
        )

    price = num(close.iloc[-1])

    e20 = num(ema20.iloc[-1])
    e50 = num(ema50.iloc[-1])
    e200 = num(ema200.iloc[-1])

    rsi_now = num(rsi.iloc[-1])

    macd_now = num(macd.iloc[-1])
    signal_now = num(signal.iloc[-1])

    atr_now = num(atr.iloc[-1])

    volume_ratio = np.nan

    if volume is not None:

        vol20 = volume.rolling(
            20
        ).mean()

        if (
            len(vol20)
            and pd.notna(vol20.iloc[-1])
            and vol20.iloc[-1] != 0
        ):

            volume_ratio = (
                volume.iloc[-1] /
                vol20.iloc[-1]
            )

    support = num(
        close.tail(60).min()
    )

    resistance = num(
        close.tail(60).max()
    )

    score = 0

    if pd.notna(price) and pd.notna(e20):
        score += 1 if price > e20 else 0

    if pd.notna(e20) and pd.notna(e50):
        score += 1 if e20 > e50 else 0

    if pd.notna(e50) and pd.notna(e200):
        score += 1 if e50 > e200 else 0

    if pd.notna(rsi_now):
        score += 1 if 50 <= rsi_now <= 75 else 0

    if (
        pd.notna(macd_now)
        and pd.notna(signal_now)
    ):
        score += 1 if macd_now > signal_now else 0

    trend = "Neutral"

    if score >= 4:
        trend = "Strong Uptrend"
    elif score >= 3:
        trend = "Uptrend"
    elif score <= 1:
        trend = "Weak"
    else:
        trend = "Neutral"

    return {

        "Technical Score":
            score,

        "Trend":
            trend,

        "Price":
            price,

        "EMA20":
            e20,

        "EMA50":
            e50,

        "EMA200":
            e200,

        "RSI":
            rsi_now,

        "MACD":
            macd_now,

        "MACD Signal":
            signal_now,

        "ATR":
            atr_now,

        "Volume Ratio":
            volume_ratio,

        "Support":
            support,

        "Resistance":
            resistance
    }


# ============================================================
# STOCK QUALITY SCORE
# ============================================================

def metric_score(metric, value):

    value = num(value)

    if pd.isna(value):
        return np.nan

    # Higher is better
    higher = {

        "Revenue Growth":
            (0, 10, 25),

        "EPS Growth":
            (0, 10, 25),

        "Net Income Growth":
            (0, 10, 25),

        "ROE":
            (5, 12, 20),

        "ROA":
            (2, 5, 10),

        "ROIC":
            (5, 10, 18),

        "Gross Margin":
            (20, 35, 50),

        "EBITDA Margin":
            (10, 20, 30),

        "Net Margin":
            (5, 10, 20),

        "FCF Margin":
            (3, 8, 15),

        "Dividend Yield":
            (2, 5, 8),

        "NIM":
            (2, 4, 6),

        "CAR":
            (10, 13, 18),

        "Loan Growth":
            (3, 8, 15),

        "Deposit Growth":
            (3, 8, 15)
    }

    # Lower is better
    lower = {

        "Debt/Equity":
            (2.0, 1.0, 0.5),

        "Net Debt/EBITDA":
            (4.0, 2.0, 1.0),

        "P/E":
            (20, 12, 8),

        "P/B":
            (3, 2, 1.2),

        "EV/EBITDA":
            (15, 10, 7),

        "NPL":
            (8, 4, 2),

        "Cost/Income":
            (70, 55, 40)
    }

    if metric in higher:

        a, b, c = higher[metric]

        if value <= a:
            return 30

        if value <= b:
            return 55

        if value <= c:
            return 80

        return 100

    if metric in lower:

        a, b, c = lower[metric]

        if value >= a:
            return 25

        if value >= b:
            return 55

        if value >= c:
            return 80

        return 100

    # General neutral metric
    return 60


def financial_score(m, sector):

    rules = SECTOR_RULES.get(
        sector,
        SECTOR_RULES["General"]
    )

    weights = WEIGHTS.get(
        sector,
        WEIGHTS["General"]
    )

    total = 0.0
    weight_total = 0.0

    details = {}

    for metric in rules:

        value = m.get(metric)

        score = metric_score(
            metric,
            value
        )

        if pd.notna(score):

            w = weights.get(
                metric,
                1.0 / len(rules)
            )

            total += (
                score *
                w
            )

            weight_total += w

            details[metric] = score

    if weight_total == 0:

        return np.nan, 0, details

    final = (
        total /
        weight_total
    )

    coverage = (
        len(details) /
        len(rules)
    ) * 100

    return final, coverage, details


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

@st.cache_data(
    ttl=CACHE_TTL,
    show_spinner=False
)
def analyze_one(symbol):

    source = DataSourceManager(
        symbol
    )

    result = source.load()

    if not result.ok:

        return {
            "Ticker": symbol,
            "Error": result.error
        }

    data = result.data

    sector = get_sector(
        symbol
    )

    m = normalize_financials(
        data
    )

    valuation = valuation_engine(
        m,
        sector
    )

    tech = technical_analysis(
        data.get(
            "history",
            pd.DataFrame()
        )
    )

    financial, coverage, details = financial_score(
        m,
        sector
    )

    pio = piotroski_style(
        m
    )

    beneish = beneish_proxy(
        m
    )

    altman = altman_z(
        m
    )

    # --------------------------------------------------------
    # Quality components
    # --------------------------------------------------------

    forensic_components = []

    if pio["max"] > 0:

        forensic_components.append(
            pio["score"] /
            pio["max"] *
            100
        )

    if beneish["label"] == "Low":
        forensic_components.append(90)

    elif beneish["label"] == "Medium":
        forensic_components.append(60)

    else:
        forensic_components.append(30)

    if pd.notna(
        m.get("ROIC")
    ):

        forensic_components.append(
            clip(
                m["ROIC"] * 4,
                0,
                100
            )
        )

    forensic_score = safe_mean(
        forensic_components
    )

    technical_score = num(
        tech.get("Technical Score")
    )

    valuation_score = np.nan

    fair_value = num(
        valuation.get("Fair Value")
    )

    price = num(
        m.get("Price")
    )

    if (
        pd.notna(fair_value)
        and pd.notna(price)
        and price > 0
    ):

        upside = (
            fair_value /
            price -
            1
        )

        valuation_score = np.clip(
            50 +
            upside * 100,
            0,
            100
        )

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    components = []

    if pd.notna(financial):
        components.append(
            financial * 0.45
        )

    if pd.notna(technical_score):
        components.append(
            technical_score /
            5 *
            100 *
            0.20
        )

    if pd.notna(forensic_score):
        components.append(
            forensic_score * 0.15
        )

    if pd.notna(valuation_score):
        components.append(
            valuation_score * 0.20
        )

    final_score = (
        sum(components)
        if components
        else np.nan
    )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    last_date = None

    history = data.get(
        "history",
        pd.DataFrame()
    )

    if (
        history is not None
        and not history.empty
    ):

        try:
            last_date = str(
                history.index[-1].date()
            )
        except Exception:
            last_date = None

    return {

        "Ticker":
            symbol.replace(".CA", ""),

        "Sector":
            sector,

        "Price":
            price,

        "Last Date":
            last_date,

        "Final Score":
            final_score,

        "Financial Score":
            financial,

        "Financial Coverage %":
            coverage,

        "Technical Score":
            technical_score,

        "Forensic Score":
            forensic_score,

        "Valuation Score":
            valuation_score,

        "Piotroski Style":
            pio["score"],

        "Piotroski Max":
            pio["max"],

        "Beneish Proxy":
            beneish["label"],

        "Altman Z":
            altman,

        **m,

        **valuation,

        **tech
    }


# ============================================================
# BATCH
# ============================================================

@st.cache_data(
    ttl=CACHE_TTL,
    show_spinner=False
)
def analyze_many(symbols):

    symbols = tuple(symbols)

    results = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                analyze_one,
                s
            ): s
            for s in symbols
        }

        for future in as_completed(
            futures
        ):

            symbol = futures[
                future
            ]

            try:

                result = future.result()

                if result:
                    results.append(result)

            except Exception as e:

                results.append(
                    {
                        "Ticker":
                            symbol.replace(
                                ".CA",
                                ""
                            ),
                        "Error":
                            str(e)
                    }
                )

    return results


# ============================================================
# UI
# ============================================================

st.title(
    "🏛️ EGX Institutional V5.2"
)

st.caption(
    "Financial + DCF + Relative Valuation + Technical Analysis"
)

st.info(
    "النسخة دي بتفصل بين Conservative / Base / Optimistic "
    "وتحسب كل سيناريو بشكل مستقل، مع إظهار طريقة وجودة FCFF."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Settings"
    )

    selected = st.text_input(
        "Ticker",
        value="ALCN"
    ).strip().upper()

    if selected and not selected.endswith(".CA"):

        selected_yf = (
            selected +
            ".CA"
        )

    else:

        selected_yf = selected

    run_single = st.button(
        "🔎 تحليل السهم",
        use_container_width=True
    )

    st.divider()

    run_all = st.checkbox(
        "تحليل EGX Universe",
        value=False
    )

    limit = st.number_input(
        "عدد الأسهم",
        min_value=5,
        max_value=len(STOCKS),
        value=50,
        step=5
    )

    if run_all:

        universe = STOCKS[:int(limit)]

    else:

        universe = [selected_yf]


# ============================================================
# SINGLE STOCK
# ============================================================

if run_single or not run_all:

    with st.spinner(
        f"جاري تحليل {selected_yf}..."
    ):

        result = analyze_one(
            selected_yf
        )

    if result.get("Error"):

        st.error(
            result["Error"]
        )

    else:

        ticker_name = result.get(
            "Ticker",
            selected
        )

        sector = result.get(
            "Sector",
            ""
        )

        price = num(
            result.get("Price")
        )

        st.subheader(
            f"📊 {ticker_name}"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "السعر الحالي",
            f"{price:.2f}"
            if pd.notna(price)
            else "-"
        )

        c2.metric(
            "القطاع",
            sector
        )

        c3.metric(
            "Final Score",
            f"{result.get('Final Score', np.nan):.1f}"
            if pd.notna(
                num(result.get("Final Score"))
            )
            else "-"
        )

        c4.metric(
            "Financial Coverage",
            f"{result.get('Financial Coverage %', np.nan):.1f}%"
            if pd.notna(
                num(
                    result.get(
                        "Financial Coverage %"
                    )
                )
            )
            else "-"
        )

        st.divider()

        # ====================================================
        # VALUATION
        # ====================================================

        st.subheader(
            "💰 Valuation"
        )

        v1, v2, v3 = st.columns(3)

        fair_c = num(
            result.get(
                "Fair Conservative"
            )
        )

        fair_b = num(
            result.get(
                "Fair Base"
            )
        )

        fair_o = num(
            result.get(
                "Fair Optimistic"
            )
        )

        v1.metric(
            "🔴 Fair Conservative",
            f"{fair_c:.2f}"
            if pd.notna(fair_c)
            else "-"
        )

        v2.metric(
            "🟡 Fair Base",
            f"{fair_b:.2f}"
            if pd.notna(fair_b)
            else "-"
        )

        v3.metric(
            "🟢 Fair Optimistic",
            f"{fair_o:.2f}"
            if pd.notna(fair_o)
            else "-"
        )

        # ----------------------------------------------------
        # Explicit scenario table
        # ----------------------------------------------------

        valuation_table = pd.DataFrame(
            [
                {
                    "Scenario": "Conservative",
                    "DCF": result.get(
                        "DCF Conservative"
                    ),
                    "Relative": result.get(
                        "Relative Conservative"
                    ),
                    "Fair Value": result.get(
                        "Fair Conservative"
                    ),
                    "Upside %": result.get(
                        "Upside Conservative %"
                    )
                },
                {
                    "Scenario": "Base",
                    "DCF": result.get(
                        "DCF Base"
                    ),
                    "Relative": result.get(
                        "Relative Base"
                    ),
                    "Fair Value": result.get(
                        "Fair Base"
                    ),
                    "Upside %": result.get(
                        "Upside %"
                    )
                },
                {
                    "Scenario": "Optimistic",
                    "DCF": result.get(
                        "DCF Optimistic"
                    ),
                    "Relative": result.get(
                        "Relative Optimistic"
                    ),
                    "Fair Value": result.get(
                        "Fair Optimistic"
                    ),
                    "Upside %": result.get(
                        "Upside Optimistic %"
                    )
                }
            ]
        )

        st.dataframe(
            valuation_table.style.format(
                {
                    "DCF": "{:.2f}",
                    "Relative": "{:.2f}",
                    "Fair Value": "{:.2f}",
                    "Upside %": "{:.1f}%"
                },
                na_rep="-"
            ),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # BUY PRICE
        # ----------------------------------------------------

        b1, b2, b3 = st.columns(3)

        buy20 = num(
            result.get(
                "Buy 20% MOS"
            )
        )

        buy30 = num(
            result.get(
                "Strong Buy 30% MOS"
            )
        )

        b1.metric(
            "Fair Base",
            f"{fair_b:.2f}"
            if pd.notna(fair_b)
            else "-"
        )

        b2.metric(
            "Buy Price -20%",
            f"{buy20:.2f}"
            if pd.notna(buy20)
            else "-"
        )

        b3.metric(
            "Strong Buy -30%",
            f"{buy30:.2f}"
            if pd.notna(buy30)
            else "-"
        )

        # ----------------------------------------------------
        # DCF DIAGNOSTICS
        # ----------------------------------------------------

        st.subheader(
            "🧮 DCF Diagnostics"
        )

        d1, d2, d3, d4 = st.columns(4)

        d1.metric(
            "FCFF Method",
            str(
                result.get(
                    "FCFF Method",
                    "-"
                )
            )
        )

        d2.metric(
            "FCFF Quality",
            str(
                result.get(
                    "FCFF Quality",
                    "-"
                )
            )
        )

        d3.metric(
            "DCF Weight",
            f"{num(result.get('DCF Weight')) * 100:.0f}%"
            if pd.notna(
                num(
                    result.get(
                        "DCF Weight"
                    )
                )
            )
            else "-"
        )

        d4.metric(
            "Relative Weight",
            f"{num(result.get('Relative Weight')) * 100:.0f}%"
            if pd.notna(
                num(
                    result.get(
                        "Relative Weight"
                    )
                )
            )
            else "-"
        )

        if (
            pd.isna(fair_c)
            and pd.isna(fair_b)
            and pd.isna(fair_o)
        ):

            st.warning(
                "لم تتوفر بيانات كافية لبناء Fair Value "
                "موثوق لهذا السهم."
            )

        # ====================================================
        # RELATIVE VALUATION
        # ====================================================

        st.subheader(
            "📐 Relative Valuation"
        )

        rv = pd.DataFrame(
            [
                {
                    "Method": "P/E",
                    "Fair Value": result.get(
                        "P/E FV"
                    ),
                    "Reference Multiple": result.get(
                        "PE Reference"
                    )
                },
                {
                    "Method": "P/B",
                    "Fair Value": result.get(
                        "P/B FV"
                    ),
                    "Reference Multiple": result.get(
                        "PB Reference"
                    )
                },
                {
                    "Method": "EV/EBITDA",
                    "Fair Value": result.get(
                        "EV/EBITDA FV"
                    ),
                    "Reference Multiple": result.get(
                        "EV/EBITDA Reference"
                    )
                }
            ]
        )

        st.dataframe(
            rv.style.format(
                {
                    "Fair Value": "{:.2f}",
                    "Reference Multiple": "{:.2f}"
                },
                na_rep="-"
            ),
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # FINANCIAL
        # ====================================================

        st.subheader(
            "📊 Financial Snapshot"
        )

        financial_data = {

            "Revenue":
                result.get("Revenue"),

            "Revenue Growth %":
                result.get("Revenue Growth"),

            "Net Income":
                result.get("Net Income"),

            "Net Income Growth %":
                result.get("Net Income Growth"),

            "EPS":
                result.get("EPS"),

            "EPS Growth %":
                result.get("EPS Growth"),

            "EBITDA":
                result.get("EBITDA"),

            "EBITDA Margin %":
                result.get("EBITDA Margin"),

            "Net Margin %":
                result.get("Net Margin"),

            "FCF":
                result.get("FCF"),

            "FCF Margin %":
                result.get("FCF Margin"),

            "ROE %":
                result.get("ROE"),

            "ROA %":
                result.get("ROA"),

            "ROIC %":
                result.get("ROIC"),

            "Debt/Equity":
                result.get("Debt/Equity"),

            "Net Debt/EBITDA":
                result.get("Net Debt/EBITDA"),

            "P/E":
                result.get("P/E"),

            "P/B":
                result.get("P/B"),

            "Dividend Yield %":
                result.get("Dividend Yield")
        }

        fin_df = pd.DataFrame(
            list(
                financial_data.items()
            ),
            columns=[
                "Metric",
                "Value"
            ]
        )

        st.dataframe(
            fin_df.style.format(
                {
                    "Value": "{:.2f}"
                },
                na_rep="-"
            ),
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # TECHNICAL
        # ====================================================

        st.subheader(
            "📈 Technical"
        )

        t1, t2, t3, t4 = st.columns(4)

        t1.metric(
            "Trend",
            str(
                result.get(
                    "Trend",
                    "-"
                )
            )
        )

        t2.metric(
            "RSI",
            f"{num(result.get('RSI')):.1f}"
            if pd.notna(
                num(result.get("RSI"))
            )
            else "-"
        )

        t3.metric(
            "Technical Score",
            f"{num(result.get('Technical Score')):.0f}/5"
            if pd.notna(
                num(
                    result.get(
                        "Technical Score"
                    )
                )
            )
            else "-"
        )

        t4.metric(
            "Volume Ratio",
            f"{num(result.get('Volume Ratio')):.2f}x"
            if pd.notna(
                num(
                    result.get(
                        "Volume Ratio"
                    )
                )
            )
            else "-"
        )

        tech_df = pd.DataFrame(
            [
                {
                    "Metric": "EMA20",
                    "Value": result.get(
                        "EMA20"
                    )
                },
                {
                    "Metric": "EMA50",
                    "Value": result.get(
                        "EMA50"
                    )
                },
                {
                    "Metric": "EMA200",
                    "Value": result.get(
                        "EMA200"
                    )
                },
                {
                    "Metric": "Support",
                    "Value": result.get(
                        "Support"
                    )
                },
                {
                    "Metric": "Resistance",
                    "Value": result.get(
                        "Resistance"
                    )
                },
                {
                    "Metric": "ATR",
                    "Value": result.get(
                        "ATR"
                    )
                }
            ]
        )

        st.dataframe(
            tech_df.style.format(
                {
                    "Value": "{:.2f}"
                },
                na_rep="-"
            ),
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # FORENSIC
        # ====================================================

        st.subheader(
            "🔬 Quality / Forensic"
        )

        f1, f2, f3 = st.columns(3)

        f1.metric(
            "Piotroski-style",
            f"{result.get('Piotroski Style', 0)}/"
            f"{result.get('Piotroski Max', 0)}"
        )

        f2.metric(
            "Beneish Proxy",
            str(
                result.get(
                    "Beneish Proxy",
                    "-"
                )
            )
        )

        f3.metric(
            "Altman Z",
            f"{num(result.get('Altman Z')):.2f}"
            if pd.notna(
                num(
                    result.get(
                        "Altman Z"
                    )
                )
            )
            else "-"
        )

        st.caption(
            "Piotroski هنا screening-style وليس تطبيقًا أكاديميًا حرفيًا للـ F-Score، "
            "وBeneish Proxy مؤشر فرز وليس M-Score كامل."
        )


# ============================================================
# UNIVERSE
# ============================================================

if run_all:

    st.divider()

    st.header(
        "🏆 EGX Universe Ranking"
    )

    with st.spinner(
        "جاري تحليل الأسهم..."
    ):

        results = analyze_many(
            universe
        )

    if results:

        df = pd.DataFrame(
            results
        )

        if "Error" in df.columns:

            df = df[
                df["Error"].isna()
                if df["Error"].notna().any()
                else df.index == df.index
            ]

        if not df.empty:

            columns = [
                "Ticker",
                "Sector",
                "Price",
                "Final Score",
                "Financial Score",
                "Technical Score",
                "Fair Conservative",
                "Fair Base",
                "Fair Optimistic",
                "Buy 20% MOS",
                "Strong Buy 30% MOS",
                "Upside %",
                "ROE",
                "Revenue Growth",
                "EPS Growth",
                "P/E",
                "P/B",
                "FCFF Method",
                "FCFF Quality"
            ]

            available = [
                c for c in columns
                if c in df.columns
            ]

            ranking = df[
                available
            ].copy()

            if "Final Score" in ranking.columns:

                ranking = ranking.sort_values(
                    "Final Score",
                    ascending=False,
                    na_position="last"
                )

            st.dataframe(
                ranking.style.format(
                    {
                        "Price": "{:.2f}",
                        "Final Score": "{:.1f}",
                        "Financial Score": "{:.1f}",
                        "Technical Score": "{:.0f}",
                        "Fair Conservative": "{:.2f}",
                        "Fair Base": "{:.2f}",
                        "Fair Optimistic": "{:.2f}",
                        "Buy 20% MOS": "{:.2f}",
                        "Strong Buy 30% MOS": "{:.2f}",
                        "Upside %": "{:.1f}%",
                        "ROE": "{:.1f}",
                        "Revenue Growth": "{:.1f}%",
                        "EPS Growth": "{:.1f}%",
                        "P/E": "{:.2f}",
                        "P/B": "{:.2f}"
                    },
                    na_rep="-"
                ),
                use_container_width=True,
                hide_index=True
            )

            st.success(
                f"تم تحليل {len(ranking)} سهم."
            )

        else:

            st.warning(
                "لم يتم الحصول على بيانات كافية."
            )

    else:

        st.warning(
            "لم يتم إرجاع نتائج."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EGX Institutional V5.2 — valuation scenarios are calculated independently. "
    "Fair Value is an analytical estimate, not a guaranteed target."
)
