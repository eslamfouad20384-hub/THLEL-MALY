import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Any

# ============================================================
# EGX INSTITUTIONAL V5.1
# ============================================================
# Financial Intelligence
# Realistic FCFF DCF
# Relative Valuation
# Conservative / Base / Optimistic Scenarios
# Forensic Quality
# Dividend Analysis
# V9 Technical
# Backtest / WFO / Monte Carlo
# Stability
# Final Investment Score
# ============================================================

st.set_page_config(
    page_title="EGX Institutional V5.1",
    page_icon="🏛️",
    layout="wide"
)

# ============================================================
# UNIVERSE
# ============================================================

RAW = '''COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN MPCO ELSH MEPA ODIN EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH'''.split()

STOCKS = list(dict.fromkeys(x + ".CA" for x in RAW))

# ============================================================
# SECTORS
# ============================================================

BANKS = set(
    'COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB'.split()
)

RE = set(
    'PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD DCRC ARCC '
    'RMDA IDRE RREI EGREF EHDR MENA MPRC'.split()
)

HEALTH = set(
    'BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH'.split()
)

TECH = set(
    'ETEL MTIE RAYA EFIH UBEE DGTZ GOUR'.split()
)

ENERGY = set(
    'AMOC SKPC EGAS TAQA MOIL GPIM EGAL ELSH MEPA'.split()
)

CONSUMER = set(
    'DOMT EAST JUFO SUGR POUL OLFI AJWA MICH UEGC ISMA GOUR FERC'.split()
)

CONSTRUCTION = set(
    'ORAS ENGC SVCE ARAB ELNA UPMS UNIT NCCW RACC PRCL AIDC'.split()
)

FIN = set(
    'EFIH BTFH VALU OFH CNFN MCQE ADCI ACAP FAIT AFDI UBEE FAITA '
    'AIFI AMIA AMII ATLC BINV DIFC'.split()
)

INDUSTRIAL = set(
    x for x in RAW
    if x not in (
        BANKS
        | RE
        | HEALTH
        | TECH
        | ENERGY
        | CONSUMER
        | CONSTRUCTION
        | FIN
    )
)

SECTOR_RULES = {
    "Banks": [
        "ROE", "ROA", "NIM", "Cost/Income", "NPL", "NPL Coverage",
        "CAR", "Loan Growth", "Deposit Growth", "Net Income Growth",
        "P/B", "P/E", "Dividend Yield"
    ],

    "Real Estate": [
        "Revenue Growth", "EPS Growth", "EBITDA Margin",
        "Net Margin", "ROE", "Debt/Equity", "Net Debt/EBITDA",
        "Operating Cash Flow", "FCF Margin", "P/B", "P/E"
    ],

    "Healthcare": [
        "Revenue Growth", "EPS Growth", "Net Margin",
        "EBITDA Margin", "ROE", "ROA", "FCF Margin",
        "Debt/Equity", "Current Ratio", "P/E", "P/B"
    ],

    "Telecom & Technology": [
        "Revenue Growth", "EPS Growth", "EBITDA Margin",
        "Net Margin", "ROIC", "FCF Margin", "Net Debt/EBITDA",
        "ROE", "P/E", "EV/EBITDA", "Dividend Yield"
    ],

    "Energy & Petrochemicals": [
        "Revenue Growth", "EPS Growth", "EBITDA Margin",
        "Net Margin", "ROIC", "FCF Margin", "Debt/Equity",
        "Net Debt/EBITDA", "ROE", "P/E", "EV/EBITDA",
        "Dividend Yield"
    ],

    "Consumer": [
        "Revenue Growth", "EPS Growth", "Gross Margin",
        "EBITDA Margin", "Net Margin", "ROE", "ROIC",
        "FCF Margin", "Debt/Equity", "P/E", "Dividend Yield"
    ],

    "Construction & Engineering": [
        "Revenue Growth", "EBITDA Margin", "Net Margin",
        "ROE", "ROIC", "Operating Cash Flow", "FCF Margin",
        "Debt/Equity", "Net Debt/EBITDA", "P/E", "P/B"
    ],

    "Industrial & Materials": [
        "Revenue Growth", "EPS Growth", "Gross Margin",
        "EBITDA Margin", "Net Margin", "ROE", "ROIC",
        "FCF Margin", "Debt/Equity", "Net Debt/EBITDA",
        "P/E", "P/B", "Dividend Yield"
    ],

    "Financial Services": [
        "Revenue Growth", "Net Income Growth", "ROE", "ROA",
        "Net Margin", "Debt/Equity", "Current Ratio",
        "P/E", "P/B", "Dividend Yield"
    ],

    "General": [
        "Revenue Growth", "EPS Growth", "Net Margin",
        "ROE", "ROA", "ROIC", "FCF Margin",
        "Debt/Equity", "Current Ratio", "P/E", "P/B",
        "Dividend Yield"
    ]
}

# IMPORTANT:
# Fixed syntax + explicit construction.
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
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan


def pct(x):
    x = num(x)
    return np.nan if pd.isna(x) else x * 100.0


def safe_mean(values):
    vals = [
        num(v)
        for v in values
        if pd.notna(num(v))
    ]
    return float(np.mean(vals)) if vals else np.nan


def safe_median(values):
    vals = [
        num(v)
        for v in values
        if pd.notna(num(v))
    ]
    return float(np.median(vals)) if vals else np.nan


def clean_series(s):
    if s is None:
        return None

    try:
        s = pd.to_numeric(s, errors="coerce").dropna()

        if len(s) == 0:
            return None

        # yfinance financial statements are normally newest -> oldest.
        # We explicitly sort dates when possible.
        try:
            s = s.sort_index(ascending=False)
        except Exception:
            pass

        return s
    except Exception:
        return None


def latest(s):
    s = clean_series(s)

    if s is None or len(s) == 0:
        return np.nan

    return num(s.iloc[0])


def previous(s):
    s = clean_series(s)

    if s is None or len(s) < 2:
        return np.nan

    return num(s.iloc[1])


def growth(s):
    s = clean_series(s)

    if s is None or len(s) < 2:
        return np.nan

    newest = num(s.iloc[0])
    old = num(s.iloc[1])

    if pd.isna(newest) or pd.isna(old) or old == 0:
        return np.nan

    return (newest / old - 1.0) * 100.0


def find(df, names):
    if df is None or df.empty:
        return None

    for name in names:
        if name in df.index:
            return pd.to_numeric(
                df.loc[name],
                errors="coerce"
            )

    for idx in df.index:
        low = str(idx).lower()

        for name in names:
            n = str(name).lower()

            if n in low or low in n:
                return pd.to_numeric(
                    df.loc[idx],
                    errors="coerce"
                )

    return None


def find_value(df, names, default=np.nan):
    s = find(df, names)
    x = latest(s)

    return default if pd.isna(x) else x


def get_latest_close(hist):
    if hist is None or hist.empty:
        return np.nan

    try:
        if "Close" not in hist.columns:
            return np.nan

        close = pd.to_numeric(
            hist["Close"],
            errors="coerce"
        ).dropna()

        if close.empty:
            return np.nan

        return num(close.iloc[-1])
    except Exception:
        return np.nan


def get_last_date(hist):
    if hist is None or hist.empty:
        return "—"

    try:
        return pd.Timestamp(
            hist.index[-1]
        ).strftime("%Y-%m-%d")
    except Exception:
        return "—"


# ============================================================
# SECTOR
# ============================================================

def sector(sym, info):
    s = sym.replace(".CA", "")

    groups = [
        (BANKS, "Banks"),
        (RE, "Real Estate"),
        (HEALTH, "Healthcare"),
        (TECH, "Telecom & Technology"),
        (ENERGY, "Energy & Petrochemicals"),
        (CONSUMER, "Consumer"),
        (CONSTRUCTION, "Construction & Engineering"),
        (FIN, "Financial Services"),
        (INDUSTRIAL, "Industrial & Materials")
    ]

    for group, name in groups:
        if s in group:
            return name

    text = (
        str(info.get("sector", ""))
        + " "
        + str(info.get("industry", ""))
    ).lower()

    if "bank" in text:
        return "Banks"

    if "real estate" in text:
        return "Real Estate"

    if any(
        x in text
        for x in ["health", "medical", "pharma"]
    ):
        return "Healthcare"

    if any(
        x in text
        for x in ["telecom", "software", "technology", "internet"]
    ):
        return "Telecom & Technology"

    if any(
        x in text
        for x in ["oil", "gas", "energy", "petro"]
    ):
        return "Energy & Petrochemicals"

    if any(
        x in text
        for x in ["consumer", "food", "beverage", "retail"]
    ):
        return "Consumer"

    if "construction" in text or "engineering" in text:
        return "Construction & Engineering"

    if any(
        x in text
        for x in ["financial", "insurance", "investment"]
    ):
        return "Financial Services"

    return "General"


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

        t = yf.Ticker(self.ticker)

        info = {}
        financials = pd.DataFrame()
        balance = pd.DataFrame()
        cashflow = pd.DataFrame()
        quarterly_financials = pd.DataFrame()
        quarterly_balance = pd.DataFrame()
        quarterly_cashflow = pd.DataFrame()

        errors = []

        try:
            info = t.info or {}
        except Exception as e:
            errors.append(f"info: {e}")

        try:
            financials = t.financials
        except Exception as e:
            errors.append(f"financials: {e}")

        try:
            balance = t.balance_sheet
        except Exception as e:
            errors.append(f"balance: {e}")

        try:
            cashflow = t.cashflow
        except Exception as e:
            errors.append(f"cashflow: {e}")

        try:
            quarterly_financials = t.quarterly_financials
        except Exception as e:
            errors.append(f"quarterly_financials: {e}")

        try:
            quarterly_balance = t.quarterly_balance_sheet
        except Exception as e:
            errors.append(f"quarterly_balance: {e}")

        try:
            quarterly_cashflow = t.quarterly_cashflow
        except Exception as e:
            errors.append(f"quarterly_cashflow: {e}")

        # We don't fail the whole stock if one Yahoo endpoint fails.
        ok = bool(
            info
            or not financials.empty
            or not balance.empty
            or not cashflow.empty
        )

        return SourceResult(
            source="Yahoo Finance",
            ok=ok,
            data={
                "ticker": t,
                "info": info,
                "financials": financials,
                "balance": balance,
                "cashflow": cashflow,
                "quarterly_financials": quarterly_financials,
                "quarterly_balance": quarterly_balance,
                "quarterly_cashflow": quarterly_cashflow,
                "source_errors": errors
            },
            error=" | ".join(errors)
        )

    def load(self):

        try:
            return self.yahoo()

        except Exception as e:
            return SourceResult(
                source="Yahoo Finance",
                ok=False,
                error=str(e)
            )


# ============================================================
# TTM HELPERS
# ============================================================

def ttm_sum(df, names):
    s = find(df, names)

    if s is None:
        return np.nan

    s = clean_series(s)

    if s is None or len(s) == 0:
        return np.nan

    # For quarterly statements, first four quarters.
    vals = list(s.iloc[:4])

    if len(vals) < 4:
        return np.nan

    return num(np.sum(vals))


def ttm_eps(df):
    s = find(
        df,
        [
            "Diluted EPS",
            "Basic EPS"
        ]
    )

    if s is None:
        return np.nan

    s = clean_series(s)

    if s is None or len(s) < 4:
        return np.nan

    return num(np.sum(s.iloc[:4]))


# ============================================================
# FINANCIAL NORMALIZATION
# ============================================================

def normalize_financials(raw):

    info = raw.get("info", {}) or {}

    inc = raw.get(
        "financials",
        pd.DataFrame()
    )

    bal = raw.get(
        "balance",
        pd.DataFrame()
    )

    cf = raw.get(
        "cashflow",
        pd.DataFrame()
    )

    qinc = raw.get(
        "quarterly_financials",
        pd.DataFrame()
    )

    qbal = raw.get(
        "quarterly_balance",
        pd.DataFrame()
    )

    qcf = raw.get(
        "quarterly_cashflow",
        pd.DataFrame()
    )

    # --------------------------------------------------------
    # Annual values
    # --------------------------------------------------------

    R = latest(
        find(
            inc,
            [
                "Total Revenue",
                "Operating Revenue",
                "Revenue"
            ]
        )
    )

    NI = latest(
        find(
            inc,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ]
        )
    )

    EQ = latest(
        find(
            bal,
            [
                "Stockholders Equity",
                "Total Equity Gross Minority Interest",
                "Common Stock Equity",
                "Total Equity"
            ]
        )
    )

    AS = latest(
        find(
            bal,
            [
                "Total Assets"
            ]
        )
    )

    D = latest(
        find(
            bal,
            [
                "Total Debt",
                "Long Term Debt",
                "Current Debt"
            ]
        )
    )

    C = latest(
        find(
            bal,
            [
                "Cash Cash Equivalents And Short Term Investments",
                "Cash And Cash Equivalents",
                "Cash Financial"
            ]
        )
    )

    OCF = latest(
        find(
            cf,
            [
                "Operating Cash Flow",
                "Total Cash From Operating Activities"
            ]
        )
    )

    CAPEX = latest(
        find(
            cf,
            [
                "Capital Expenditure",
                "Capital Expenditures"
            ]
        )
    )

    EBIT = latest(
        find(
            inc,
            [
                "EBIT",
                "Operating Income"
            ]
        )
    )

    EBITDA = latest(
        find(
            inc,
            [
                "EBITDA",
                "Normalized EBITDA"
            ]
        )
    )

    GROSS = latest(
        find(
            inc,
            [
                "Gross Profit"
            ]
        )
    )

    D_AND_A = latest(
        find(
            cf,
            [
                "Depreciation And Amortization",
                "Depreciation",
                "Depreciation & Amortization"
            ]
        )
    )

    TAX_EXPENSE = latest(
        find(
            inc,
            [
                "Tax Provision",
                "Tax Provision Expense",
                "Income Tax Expense"
            ]
        )
    )

    PRETAX = latest(
        find(
            inc,
            [
                "Pretax Income",
                "Pretax Income"
            ]
        )
    )

    WORKING_CAPITAL = latest(
        find(
            bal,
            [
                "Working Capital"
            ]
        )
    )

    RETAINED_EARNINGS = latest(
        find(
            bal,
            [
                "Retained Earnings",
                "Retained Earnings Accumulated Deficit"
            ]
        )
    )

    # --------------------------------------------------------
    # Prior year balance sheet values
    # --------------------------------------------------------

    previous_working_capital = previous(
        find(
            bal,
            [
                "Working Capital"
            ]
        )
    )

    # --------------------------------------------------------
    # FCF
    # --------------------------------------------------------

    if (
        pd.notna(OCF)
        and pd.notna(CAPEX)
    ):
        if CAPEX < 0:
            FCF = OCF + CAPEX
        else:
            FCF = OCF - CAPEX
    else:
        FCF = np.nan

    # --------------------------------------------------------
    # TTM override when available
    # --------------------------------------------------------

    TTM_R = ttm_sum(
        qinc,
        [
            "Total Revenue",
            "Operating Revenue",
            "Revenue"
        ]
    )

    TTM_NI = ttm_sum(
        qinc,
        [
            "Net Income",
            "Net Income Common Stockholders"
        ]
    )

    TTM_OCF = ttm_sum(
        qcf,
        [
            "Operating Cash Flow",
            "Total Cash From Operating Activities"
        ]
    )

    TTM_CAPEX = ttm_sum(
        qcf,
        [
            "Capital Expenditure",
            "Capital Expenditures"
        ]
    )

    TTM_EBIT = ttm_sum(
        qinc,
        [
            "EBIT",
            "Operating Income"
        ]
    )

    TTM_EBITDA = ttm_sum(
        qinc,
        [
            "EBITDA",
            "Normalized EBITDA"
        ]
    )

    TTM_GROSS = ttm_sum(
        qinc,
        [
            "Gross Profit"
        ]
    )

    TTM_EPS = ttm_eps(qinc)

    # Use TTM where available.
    if pd.notna(TTM_R):
        R = TTM_R

    if pd.notna(TTM_NI):
        NI = TTM_NI

    if pd.notna(TTM_OCF):
        OCF = TTM_OCF

    if pd.notna(TTM_CAPEX):
        CAPEX = TTM_CAPEX

    if pd.notna(TTM_EBIT):
        EBIT = TTM_EBIT

    if pd.notna(TTM_EBITDA):
        EBITDA = TTM_EBITDA

    if pd.notna(TTM_GROSS):
        GROSS = TTM_GROSS

    # --------------------------------------------------------
    # Shares
    # --------------------------------------------------------

    shares = num(
        info.get("sharesOutstanding")
    )

    # Fallback from market cap / latest market price.
    market_cap = num(
        info.get("marketCap")
    )

    info_price = num(
        info.get("currentPrice")
    )

    if (
        pd.isna(shares)
        and pd.notna(market_cap)
        and pd.notna(info_price)
        and info_price > 0
    ):
        shares = market_cap / info_price

    EPS = (
        TTM_EPS
        if pd.notna(TTM_EPS)
        else latest(
            find(
                inc,
                [
                    "Diluted EPS",
                    "Basic EPS"
                ]
            )
        )
    )

    # --------------------------------------------------------
    # Growth
    # --------------------------------------------------------

    revenue_growth = growth(
        find(
            inc,
            [
                "Total Revenue",
                "Operating Revenue",
                "Revenue"
            ]
        )
    )

    ni_growth = growth(
        find(
            inc,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ]
        )
    )

    eps_growth = growth(
        find(
            inc,
            [
                "Diluted EPS",
                "Basic EPS"
            ]
        )
    )

    # --------------------------------------------------------
    # Tax Rate
    # --------------------------------------------------------

    tax_rate = np.nan

    if (
        pd.notna(TAX_EXPENSE)
        and pd.notna(PRETAX)
        and PRETAX > 0
    ):
        tax_rate = np.clip(
            TAX_EXPENSE / PRETAX,
            0,
            .40
        )

    if pd.isna(tax_rate):
        tax_rate = num(
            info.get("effectiveTaxRate")
        )

    if pd.notna(tax_rate):
        if tax_rate > 1:
            tax_rate /= 100.0

        tax_rate = np.clip(
            tax_rate,
            0,
            .40
        )

    # --------------------------------------------------------
    # Price
    # IMPORTANT:
    # historical price is replaced later after history load.
    # --------------------------------------------------------

    price = info_price

    # --------------------------------------------------------
    # Ratios
    # --------------------------------------------------------

    net_debt = (
        D - C
        if pd.notna(D) and pd.notna(C)
        else np.nan
    )

    invested_capital = np.nan

    if (
        pd.notna(EQ)
        and pd.notna(D)
    ):
        invested_capital = (
            EQ + D
            - (C if pd.notna(C) else 0)
        )

    metrics = {
        "Revenue": R,
        "Net Income": NI,
        "Equity": EQ,
        "Assets": AS,
        "Debt": D,
        "Cash": C,
        "Operating Cash Flow": OCF,
        "Capex": CAPEX,
        "FCF": FCF,
        "EBIT": EBIT,
        "EBITDA": EBITDA,
        "Gross Profit": GROSS,
        "D&A": D_AND_A,
        "Working Capital": WORKING_CAPITAL,
        "Previous Working Capital": previous_working_capital,
        "Retained Earnings": RETAINED_EARNINGS,
        "Shares": shares,
        "Market Cap": market_cap,
        "Price": price,
        "EPS": EPS,
        "Tax Rate": tax_rate,
        "Revenue Growth": revenue_growth,
        "Net Income Growth": ni_growth,
        "EPS Growth": eps_growth
    }

    metrics.update(
        {
            "Gross Margin":
                GROSS / R * 100
                if pd.notna(GROSS)
                and pd.notna(R)
                and R
                else np.nan,

            "EBITDA Margin":
                EBITDA / R * 100
                if pd.notna(EBITDA)
                and pd.notna(R)
                and R
                else np.nan,

            "Net Margin":
                NI / R * 100
                if pd.notna(NI)
                and pd.notna(R)
                and R
                else np.nan,

            "ROE":
                NI / EQ * 100
                if pd.notna(NI)
                and pd.notna(EQ)
                and EQ
                else pct(
                    info.get("returnOnEquity")
                ),

            "ROA":
                NI / AS * 100
                if pd.notna(NI)
                and pd.notna(AS)
                and AS
                else pct(
                    info.get("returnOnAssets")
                ),

            "ROIC":
                EBIT / invested_capital * 100
                if pd.notna(EBIT)
                and pd.notna(invested_capital)
                and invested_capital > 0
                else np.nan,

            "FCF Margin":
                FCF / R * 100
                if pd.notna(FCF)
                and pd.notna(R)
                and R
                else np.nan,

            "Debt/Equity":
                D / EQ
                if pd.notna(D)
                and pd.notna(EQ)
                and EQ
                else (
                    num(info.get("debtToEquity")) / 100
                    if pd.notna(
                        num(info.get("debtToEquity"))
                    )
                    else np.nan
                ),

            "Net Debt/EBITDA":
                net_debt / EBITDA
                if pd.notna(net_debt)
                and pd.notna(EBITDA)
                and EBITDA > 0
                else np.nan,

            "Current Ratio":
                num(info.get("currentRatio")),

            "P/E":
                num(info.get("trailingPE")),

            "P/B":
                num(info.get("priceToBook")),

            "EV/EBITDA":
                num(info.get("enterpriseToEbitda")),

            "Dividend Yield":
                pct(info.get("dividendYield"))
        }
    )

    return (
        metrics,
        inc,
        bal,
        cf,
        info
    )


# ============================================================
# FORENSIC
# ============================================================

def piotroski(m, inc, bal, cf):

    points = 0
    tests = []

    NI = num(m.get("Net Income"))
    OCF = num(m.get("Operating Cash Flow"))
    ROE = num(m.get("ROE"))
    FCF = num(m.get("FCF"))
    margin = num(m.get("Net Margin"))
    de = num(m.get("Debt/Equity"))
    rev_g = num(m.get("Revenue Growth"))
    ni_g = num(m.get("Net Income Growth"))
    eps_g = num(m.get("EPS Growth"))

    checks = [
        ("صافي الربح موجب", NI > 0),
        ("التدفق التشغيلي موجب", OCF > 0),
        ("ROE موجب", ROE > 0),
        ("FCF موجب", FCF > 0),
        ("هامش صافي موجب", margin > 0),
        (
            "الدين/حقوق الملكية تحت السيطرة",
            de < 1.5
        ),
        (
            "نمو الإيرادات موجب",
            rev_g > 0
        ),
        (
            "نمو صافي الربح موجب",
            ni_g > 0
        ),
        (
            "نمو EPS موجب",
            eps_g > 0
        )
    ]

    for name, condition in checks:
        value = int(bool(condition))
        points += value
        tests.append(
            (name, value)
        )

    return min(points, 9), tests


def beneish(m):

    components = {
        "DSRI": np.nan,
        "GMI": np.nan,
        "AQI": np.nan,
        "SGI": np.nan,
        "DEPI": np.nan,
        "SGAI": np.nan,
        "LVGI": np.nan,
        "TATA": np.nan
    }

    risk = 0
    available = 0

    revenue_growth = num(
        m.get("Revenue Growth")
    )

    net_margin = num(
        m.get("Net Margin")
    )

    debt_equity = num(
        m.get("Debt/Equity")
    )

    fcf_margin = num(
        m.get("FCF Margin")
    )

    if pd.notna(revenue_growth):
        available += 1
        if revenue_growth > 80:
            risk += 1

    if pd.notna(net_margin):
        available += 1
        if net_margin < 0:
            risk += 1

    if pd.notna(debt_equity):
        available += 1
        if debt_equity > 2:
            risk += 1

    if pd.notna(fcf_margin):
        available += 1
        if fcf_margin < 0:
            risk += 1

    return {
        "risk_flags": risk,
        "available": available,
        "components": components,
        "status":
            "مبدئي — لا تتوفر كل مكونات Beneish"
            if available < 4
            else "Screening"
    }


def altman(m, sec):

    assets = num(m.get("Assets"))
    wc = num(m.get("Working Capital"))
    retained = num(m.get("Retained Earnings"))
    ebit = num(m.get("EBIT"))
    market_cap = num(m.get("Market Cap"))
    debt = num(m.get("Debt"))
    revenue = num(m.get("Revenue"))

    if (
        sec == "Banks"
        or sec == "Financial Services"
    ):
        return {
            "score": np.nan,
            "status": "Altman Z غير مناسب مباشرة للقطاع المالي"
        }

    A = (
        wc / assets
        if pd.notna(wc)
        and pd.notna(assets)
        and assets
        else np.nan
    )

    B = (
        retained / assets
        if pd.notna(retained)
        and pd.notna(assets)
        and assets
        else np.nan
    )

    C = (
        ebit / assets
        if pd.notna(ebit)
        and pd.notna(assets)
        and assets
        else np.nan
    )

    D = (
        market_cap / debt
        if pd.notna(market_cap)
        and pd.notna(debt)
        and debt > 0
        else np.nan
    )

    E = (
        revenue / assets
        if pd.notna(revenue)
        and pd.notna(assets)
        and assets
        else np.nan
    )

    if any(
        pd.isna(x)
        for x in [A, B, C, D, E]
    ):
        return {
            "score": np.nan,
            "status": "بيانات غير كافية"
        }

    z = (
        1.2 * A
        + 1.4 * B
        + 3.3 * C
        + .6 * D
        + 1.0 * E
    )

    status = (
        "منطقة خطر مرتفعة"
        if z < 1.8
        else
        "منطقة مراقبة"
        if z < 3
        else
        "منطقة سليمة"
    )

    return {
        "score": z,
        "status": status
    }


def earnings_quality(m):

    ocf = num(
        m.get("Operating Cash Flow")
    )

    ni = num(
        m.get("Net Income")
    )

    fcf = num(
        m.get("FCF")
    )

    roe = num(
        m.get("ROE")
    )

    accrual = (
        (ocf - ni) / abs(ni)
        if pd.notna(ocf)
        and pd.notna(ni)
        and ni
        else np.nan
    )

    score = 50.0

    if pd.notna(accrual):
        score += np.clip(
            -accrual * 25,
            -25,
            25
        )

    if (
        pd.notna(fcf)
        and pd.notna(ni)
    ):
        score += (
            15
            if fcf > ni
            else -15
        )

    if pd.notna(roe):
        score += np.clip(
            roe - 10,
            -20,
            20
        )

    return (
        float(np.clip(score, 0, 100)),
        accrual
    )


def roic_quality(m):

    roic = num(m.get("ROIC"))
    fcfm = num(m.get("FCF Margin"))
    growthv = num(m.get("Revenue Growth"))

    components = []

    if pd.notna(roic):
        components.append(
            np.clip(
                roic * 2.5,
                0,
                100
            )
        )

    if pd.notna(fcfm):
        components.append(
            np.clip(
                fcfm * 2,
                0,
                100
            )
        )

    if pd.notna(growthv):
        components.append(
            np.clip(
                50 + growthv,
                0,
                100
            )
        )

    return safe_mean(components)


# ============================================================
# DIVIDENDS
# ============================================================

def dividend_engine(t, price):

    try:

        s = pd.to_numeric(
            t.dividends,
            errors="coerce"
        ).dropna()

        s = s[s > 0]

        if s.empty:
            return {
                "yield": np.nan,
                "last": np.nan,
                "count3y": 0,
                "sustainability": np.nan
            }

        now = pd.Timestamp.now()

        try:
            if getattr(
                s.index,
                "tz",
                None
            ) is not None:
                now = pd.Timestamp.now(
                    tz=s.index.tz
                )
        except Exception:
            pass

        d12 = s[
            s.index >= now - pd.Timedelta(days=365)
        ]

        d3 = s[
            s.index >= now - pd.Timedelta(days=1095)
        ]

        total = float(
            d12.sum()
        )

        y = (
            total / price * 100
            if pd.notna(price)
            and price
            else np.nan
        )

        sustainability = (
            np.clip(
                100 - abs(y - 4) * 8,
                0,
                100
            )
            if pd.notna(y)
            else np.nan
        )

        return {
            "yield": y,
            "last": float(s.iloc[-1]),
            "date": s.index[-1].strftime("%Y-%m-%d"),
            "count3y": len(d3),
            "sustainability": sustainability
        }

    except Exception:
        return {
            "yield": np.nan,
            "last": np.nan,
            "count3y": 0,
            "sustainability": np.nan
        }


# ============================================================
# VALUATION V2
# ============================================================

def get_actual_price(m, history):

    hist_price = get_latest_close(history)

    if pd.notna(hist_price) and hist_price > 0:
        return hist_price

    info_price = num(
        m.get("Price")
    )

    return info_price


def fcff_base(m):

    EBIT = num(m.get("EBIT"))
    tax_rate = num(m.get("Tax Rate"))
    D_A = num(m.get("D&A"))
    CAPEX = num(m.get("Capex"))
    WC = num(m.get("Working Capital"))
    PREV_WC = num(
        m.get("Previous Working Capital")
    )

    if pd.isna(EBIT):
        return np.nan

    if pd.isna(tax_rate):
        tax_rate = .22

    tax_rate = np.clip(
        tax_rate,
        0,
        .40
    )

    nopat = EBIT * (1 - tax_rate)

    if pd.isna(D_A):
        D_A = 0

    if pd.isna(CAPEX):
        return np.nan

    # Yahoo can report Capex as negative or positive.
    capex_abs = abs(CAPEX)

    if (
        pd.notna(WC)
        and pd.notna(PREV_WC)
    ):
        delta_wc = WC - PREV_WC
    else:
        delta_wc = 0

    fcff = (
        nopat
        + D_A
        - capex_abs
        - delta_wc
    )

    return num(fcff)


def scenario_growths(
    m,
    scenario="base"
):

    revenue_growth = num(
        m.get("Revenue Growth")
    )

    fcf_margin = num(
        m.get("FCF Margin")
    )

    if pd.isna(revenue_growth):
        revenue_growth = 8.0

    # More realistic normalized starting growth.
    revenue_growth = np.clip(
        revenue_growth,
        -10,
        30
    )

    if scenario == "conservative":

        first = max(
            3.0,
            min(
                12.0,
                revenue_growth * .55
            )
        )

        terminal = 3.0

    elif scenario == "optimistic":

        first = np.clip(
            revenue_growth * 1.05,
            5,
            25
        )

        terminal = 4.0

    else:

        first = np.clip(
            revenue_growth * .75,
            4,
            18
        )

        terminal = 3.5

    growths = []

    for i in range(5):

        fade = i / 4.0

        g = (
            first
            + (terminal - first) * fade
        )

        growths.append(
            g / 100.0
        )

    return growths, terminal / 100.0


def fcff_dcf(
    m,
    scenario="base",
    years=5
):

    fcff = fcff_base(m)

    shares = num(
        m.get("Shares")
    )

    debt = num(
        m.get("Debt")
    )

    cash = num(
        m.get("Cash")
    )

    if (
        pd.isna(fcff)
        or fcff <= 0
        or pd.isna(shares)
        or shares <= 0
    ):
        return {
            "value": np.nan,
            "enterprise": np.nan,
            "status": "FCFF غير متاح"
        }

    if pd.isna(debt):
        debt = 0

    if pd.isna(cash):
        cash = 0

    if scenario == "conservative":

        wacc = .16

    elif scenario == "optimistic":

        wacc = .125

    else:

        wacc = .14

    growths, tg = scenario_growths(
        m,
        scenario
    )

    # Terminal growth must stay below WACC.
    tg = min(
        tg,
        wacc - .02
    )

    pv = 0.0
    current = fcff

    for year, growth_rate in enumerate(
        growths,
        start=1
    ):

        current *= (
            1 + growth_rate
        )

        pv += (
            current
            / ((1 + wacc) ** year)
        )

    terminal = (
        current
        * (1 + tg)
        / (wacc - tg)
    )

    terminal_pv = (
        terminal
        / ((1 + wacc) ** years)
    )

    enterprise = (
        pv
        + terminal_pv
    )

    equity_value = (
        enterprise
        - debt
        + cash
    )

    per_share = (
        equity_value / shares
    )

    return {
        "value": per_share,
        "enterprise": enterprise,
        "equity_value": equity_value,
        "fcff": fcff,
        "wacc": wacc * 100,
        "terminal_growth": tg * 100,
        "status": "FCFF DCF"
    }


def relative_valuation(
    m,
    sec
):

    price = num(
        m.get("Price")
    )

    eps = num(
        m.get("EPS")
    )

    equity = num(
        m.get("Equity")
    )

    shares = num(
        m.get("Shares")
    )

    # Actual book value per share.
    bvps = (
        equity / shares
        if pd.notna(equity)
        and pd.notna(shares)
        and shares > 0
        else np.nan
    )

    pe = num(
        m.get("P/E")
    )

    pb = num(
        m.get("P/B")
    )

    # Conservative reference ranges.
    peer_pe = {
        "Banks": 9.5,
        "Financial Services": 11,
        "Real Estate": 12,
        "Healthcare": 15,
        "Telecom & Technology": 14,
        "Energy & Petrochemicals": 9,
        "Consumer": 13,
        "Construction & Engineering": 11,
        "Industrial & Materials": 11,
        "General": 12
    }

    peer_pb = {
        "Banks": 1.35,
        "Financial Services": 1.5,
        "Real Estate": 1.4,
        "Healthcare": 1.8,
        "Telecom & Technology": 1.8,
        "Energy & Petrochemicals": 1.3,
        "Consumer": 1.6,
        "Construction & Engineering": 1.5,
        "Industrial & Materials": 1.5,
        "General": 1.5
    }

    pe_ref = peer_pe.get(
        sec,
        12
    )

    pb_ref = peer_pb.get(
        sec,
        1.5
    )

    values = []

    # Earnings valuation.
    if (
        pd.notna(eps)
        and eps > 0
    ):
        values.append(
            eps * pe_ref
        )

    # Book valuation.
    if (
        pd.notna(bvps)
        and bvps > 0
    ):
        values.append(
            bvps * pb_ref
        )

    # Current market multiple diagnostics.
    earnings_upside = np.nan
    book_upside = np.nan

    if (
        pd.notna(price)
        and price > 0
        and pd.notna(eps)
        and eps > 0
    ):
        earnings_upside = (
            eps * pe_ref / price - 1
        ) * 100

    if (
        pd.notna(price)
        and price > 0
        and pd.notna(bvps)
        and bvps > 0
    ):
        book_upside = (
            bvps * pb_ref / price - 1
        ) * 100

    return {
        "value": safe_median(values),
        "PE Fair Value": (
            eps * pe_ref
            if pd.notna(eps)
            and eps > 0
            else np.nan
        ),
        "PB Fair Value": (
            bvps * pb_ref
            if pd.notna(bvps)
            and bvps > 0
            else np.nan
        ),
        "PE Reference": pe_ref,
        "PB Reference": pb_ref,
        "BVPS": bvps,
        "Current PE": pe,
        "Current PB": pb,
        "PE Upside %": earnings_upside,
        "PB Upside %": book_upside,
        "methods": len(values)
    }


def valuation_engine(
    m,
    sec
):

    price = num(
        m.get("Price")
    )

    is_financial = sec in [
        "Banks",
        "Financial Services"
    ]

    conservative = fcff_dcf(
        m,
        "conservative"
    )

    base = fcff_dcf(
        m,
        "base"
    )

    optimistic = fcff_dcf(
        m,
        "optimistic"
    )

    relative = relative_valuation(
        m,
        sec
    )

    dcf_values = [
        conservative.get("value"),
        base.get("value"),
        optimistic.get("value")
    ]

    dcf_valid = [
        x
        for x in dcf_values
        if pd.notna(x) and x > 0
    ]

    dcf_base = base.get(
        "value"
    )

    relative_value = relative.get(
        "value"
    )

    # --------------------------------------------------------
    # Financial companies:
    # P/E + P/B are more relevant.
    # Industrial/non-financial:
    # DCF gets higher weight.
    # --------------------------------------------------------

    if is_financial:

        candidates = []

        if pd.notna(relative_value):
            candidates.append(
                relative_value
            )

        fair = safe_median(
            candidates
        )

        method = (
            "Relative P/E + P/B"
        )

    else:

        candidates = []

        if pd.notna(dcf_base):
            candidates.append(
                dcf_base
            )

        if pd.notna(relative_value):
            candidates.append(
                relative_value
            )

        if (
            pd.notna(dcf_base)
            and pd.notna(relative_value)
        ):
            # DCF gets 65%, relative 35%.
            fair = (
                dcf_base * .65
                + relative_value * .35
            )
        else:
            fair = safe_median(
                candidates
            )

        method = (
            "65% FCFF DCF + 35% Relative"
        )

    # --------------------------------------------------------
    # Fair value range
    # --------------------------------------------------------

    range_values = [
        conservative.get("value"),
        base.get("value"),
        optimistic.get("value"),
        relative_value
    ]

    range_values = [
        x
        for x in range_values
        if pd.notna(x)
        and x > 0
    ]

    if range_values:

        low = float(
            np.percentile(
                range_values,
                25
            )
        )

        high = float(
            np.percentile(
                range_values,
                75
            )
        )

    else:

        low = np.nan
        high = np.nan

    buy20 = (
        fair * .80
        if pd.notna(fair)
        else np.nan
    )

    buy30 = (
        fair * .70
        if pd.notna(fair)
        else np.nan
    )

    upside = (
        (fair / price - 1) * 100
        if pd.notna(fair)
        and pd.notna(price)
        and price > 0
        else np.nan
    )

    # Conservative upside.
    conservative_upside = (
        (low / price - 1) * 100
        if pd.notna(low)
        and pd.notna(price)
        and price > 0
        else np.nan
    )

    return {
        "DCF Conservative": conservative.get("value"),
        "DCF Base": dcf_base,
        "DCF Optimistic": optimistic.get("value"),
        "Relative": relative_value,
        "PE Fair Value": relative.get("PE Fair Value"),
        "PB Fair Value": relative.get("PB Fair Value"),
        "Fair Value Low": low,
        "Fair Value High": high,
        "Fair Value": fair,
        "Buy 20% MOS": buy20,
        "Strong Buy 30% MOS": buy30,
        "Upside %": upside,
        "Conservative Upside %": conservative_upside,
        "Valuation Method": method,
        "FCFF Base": base.get("fcff"),
        "WACC Base": base.get("wacc"),
        "Terminal Growth Base": base.get("terminal_growth"),
        "PE Reference": relative.get("PE Reference"),
        "PB Reference": relative.get("PB Reference"),
        "BVPS": relative.get("BVPS")
    }


# ============================================================
# TECHNICAL
# ============================================================

def technical(df):

    if (
        df is None
        or df.empty
        or "Close" not in df
        or len(df) < 220
    ):
        return {}

    d = df.copy()

    close = pd.to_numeric(
        d["Close"],
        errors="coerce"
    ).dropna()

    if len(close) < 220:
        return {}

    high = pd.to_numeric(
        d["High"],
        errors="coerce"
    ).reindex(close.index)

    low = pd.to_numeric(
        d["Low"],
        errors="coerce"
    ).reindex(close.index)

    vol = pd.to_numeric(
        d["Volume"],
        errors="coerce"
    ).reindex(close.index)

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

    delta = close.diff()

    gain = (
        delta
        .clip(lower=0)
        .ewm(
            alpha=1 / 14,
            adjust=False
        )
        .mean()
    )

    loss = (
        -delta
        .clip(upper=0)
        .ewm(
            alpha=1 / 14,
            adjust=False
        )
        .mean()
    )

    rs = (
        gain
        / loss.replace(0, np.nan)
    )

    rsi = (
        100
        - 100 / (1 + rs)
    )

    macd = (
        close.ewm(
            span=12,
            adjust=False
        ).mean()
        -
        close.ewm(
            span=26,
            adjust=False
        ).mean()
    )

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    tr = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(
        14
    ).mean()

    volume_avg = vol.rolling(
        20
    ).mean()

    last_volume_avg = (
        volume_avg.iloc[-1]
    )

    vr = (
        vol.iloc[-1] / last_volume_avg
        if pd.notna(last_volume_avg)
        and last_volume_avg
        else np.nan
    )

    c = float(
        close.iloc[-1]
    )

    e20 = float(
        ema20.iloc[-1]
    )

    e50 = float(
        ema50.iloc[-1]
    )

    e200 = float(
        ema200.iloc[-1]
    )

    rsi_last = num(
        rsi.iloc[-1]
    )

    macd_last = num(
        macd.iloc[-1]
    )

    signal_last = num(
        signal.iloc[-1]
    )

    flags = [
        c > e20,
        c > e50,
        c > e200,
        rsi_last > 50 if pd.notna(rsi_last) else False,
        (
            macd_last > signal_last
            if pd.notna(macd_last)
            and pd.notna(signal_last)
            else False
        ),
        vr >= 1
        if pd.notna(vr)
        else False
    ]

    score = (
        sum(flags)
        / len(flags)
        * 100
    )

    support = float(
        close.tail(20).min()
    )

    resistance = float(
        close.tail(20).max()
    )

    atr_last = num(
        atr.iloc[-1]
    )

    stop = max(
        support,
        c - (
            atr_last * 2
            if pd.notna(atr_last)
            else c * .08
        )
    )

    target = max(
        resistance,
        c * 1.05
    )

    return {
        "score": score,
        "price": c,
        "rsi": rsi_last,
        "macd": macd_last,
        "signal": signal_last,
        "atr_pct":
            atr_last / c * 100
            if pd.notna(atr_last)
            and c
            else np.nan,
        "volume_ratio": vr,
        "ema20": e20,
        "ema50": e50,
        "ema200": e200,
        "support": support,
        "resistance": resistance,
        "stop": stop,
        "target1": target,
        "last_date": get_last_date(
            df
        )
    }


# ============================================================
# BACKTEST
# ============================================================

def backtest(
    df,
    commission=.0015,
    slippage=.001,
    mc_runs=500
):

    if (
        df is None
        or len(df) < 260
    ):
        return {
            "trades": 0,
            "status": "بيانات غير كافية"
        }

    close = pd.to_numeric(
        df["Close"],
        errors="coerce"
    ).dropna()

    if len(close) < 260:
        return {
            "trades": 0,
            "status": "بيانات غير كافية"
        }

    ema = close.ewm(
        span=20,
        adjust=False
    ).mean()

    delta = close.diff()

    gain = (
        delta
        .clip(lower=0)
        .ewm(
            alpha=1 / 14,
            adjust=False
        )
        .mean()
    )

    loss = (
        -delta
        .clip(upper=0)
        .ewm(
            alpha=1 / 14,
            adjust=False
        )
        .mean()
    )

    rsi = (
        100
        - 100
        / (
            1
            + gain
            / loss.replace(
                0,
                np.nan
            )
        )
    )

    returns = []

    in_pos = False
    entry = np.nan

    for i in range(
        220,
        len(close)
    ):

        c = float(
            close.iloc[i]
        )

        current_ema = num(
            ema.iloc[i]
        )

        current_rsi = num(
            rsi.iloc[i]
        )

        if (
            not in_pos
            and pd.notna(current_ema)
            and pd.notna(current_rsi)
            and c > current_ema
            and current_rsi > 52
        ):

            entry = (
                c
                * (
                    1
                    + slippage
                    + commission
                )
            )

            in_pos = True

        elif (
            in_pos
            and (
                c < current_ema
                or (
                    pd.notna(current_rsi)
                    and current_rsi < 48
                )
            )
        ):

            exit_price = (
                c
                * (
                    1
                    - slippage
                    - commission
                )
            )

            if entry > 0:
                returns.append(
                    exit_price / entry - 1
                )

            in_pos = False

    if in_pos and entry > 0:

        final_exit = float(
            close.iloc[-1]
        ) * (
            1
            - slippage
            - commission
        )

        returns.append(
            final_exit / entry - 1
        )

    r = np.array(
        returns,
        dtype=float
    )

    trades = len(r)

    if not trades:
        return {
            "trades": 0,
            "status": "لا توجد صفقات"
        }

    curve = np.cumprod(
        1 + r
    )

    peak = np.maximum.accumulate(
        curve
    )

    dd = (
        peak - curve
    ) / peak * 100

    win = (
        (r > 0).mean()
        * 100
    )

    profit = (
        curve[-1] - 1
    ) * 100

    negative = r[r < 0]
    positive = r[r > 0]

    if len(negative):
        pf = (
            positive.sum()
            / abs(negative.sum())
        )
    else:
        pf = np.inf

    expectancy = (
        r.mean() * 100
    )

    sharpe = (
        r.mean()
        / r.std()
        * np.sqrt(trades)
        if r.std() > 0
        else np.nan
    )

    # Limit Monte Carlo to sensible values.
    mc_runs = int(
        np.clip(
            mc_runs,
            50,
            5000
        )
    )

    rng = np.random.default_rng(
        42
    )

    terminals = []
    dds = []

    for _ in range(
        mc_runs
    ):

        sample = rng.choice(
            r,
            size=trades,
            replace=True
        )

        curve_mc = np.cumprod(
            1 + sample
        )

        peak_mc = np.maximum.accumulate(
            curve_mc
        )

        dd_mc = (
            peak_mc - curve_mc
        ) / peak_mc * 100

        terminals.append(
            (curve_mc[-1] - 1)
            * 100
        )

        dds.append(
            np.max(dd_mc)
            if len(dd_mc)
            else 0
        )

    terminals = np.array(
        terminals
    )

    dds = np.array(
        dds
    )

    return {
        "trades": trades,
        "win_rate": win,
        "return": profit,
        "max_dd": float(
            dd.max()
        ),
        "pf": float(pf),
        "expectancy": expectancy,
        "sharpe": sharpe,
        "mc5": float(
            np.percentile(
                terminals,
                5
            )
        ),
        "mc50": float(
            np.percentile(
                terminals,
                50
            )
        ),
        "mc95": float(
            np.percentile(
                terminals,
                95
            )
        ),
        "mc_profit_prob": float(
            np.mean(
                terminals > 0
            ) * 100
        ),
        "mc_dd95": float(
            np.percentile(
                dds,
                95
            )
        ),
        "status": "تم"
    }


# ============================================================
# WFO
# ============================================================

def wfo_score(
    df,
    mc_runs=100
):

    if (
        df is None
        or len(df) < 600
    ):
        return {
            "score": np.nan,
            "oos_return": np.nan,
            "stability": np.nan,
            "folds": 0
        }

    n = len(df)

    fold = int(
        n / 4
    )

    scores = []
    returns = []

    for k in range(3):

        start = fold * (
            k + 1
        )

        end = fold * (
            k + 2
        )

        if end <= n:

            test = df.iloc[
                start:end
            ]

        else:

            test = df.iloc[
                -fold:
            ]

        bt = backtest(
            test,
            mc_runs=mc_runs
        )

        if bt.get(
            "trades",
            0
        ) >= 3:

            score = np.clip(
                50
                + bt.get(
                    "return",
                    0
                ),
                0,
                100
            )

            scores.append(
                score
            )

            returns.append(
                bt.get(
                    "return",
                    np.nan
                )
            )

    if not scores:
        return {
            "score": np.nan,
            "oos_return": np.nan,
            "stability": np.nan,
            "folds": 0
        }

    stability = (
        100
        - np.std(returns) * 2
        if len(returns) > 1
        else 50
    )

    return {
        "score": float(
            np.mean(scores)
        ),
        "oos_return": float(
            np.mean(returns)
        ),
        "stability": float(
            np.clip(
                stability,
                0,
                100
            )
        ),
        "folds": len(scores)
    }


# ============================================================
# SCORING
# ============================================================

def score_stock(
    fin,
    forensic,
    val,
    tech,
    bt,
    wfo,
    div
):

    rules = SECTOR_RULES[
        fin["sector"]
    ]

    weights = WEIGHTS[
        fin["sector"]
    ]

    fscore = []

    for metric in rules:

        x = num(
            fin["metrics"].get(
                metric
            )
        )

        if pd.isna(x):
            continue

        if metric in [
            "Revenue Growth",
            "Net Income Growth",
            "EPS Growth"
        ]:

            score = np.clip(
                50 + x * 1.5,
                0,
                100
            )

        elif metric in [
            "ROE",
            "ROIC"
        ]:

            score = np.clip(
                x * 3,
                0,
                100
            )

        elif metric == "ROA":

            score = np.clip(
                x * 15,
                0,
                100
            )

        elif metric in [
            "Gross Margin",
            "EBITDA Margin",
            "Net Margin",
            "FCF Margin"
        ]:

            score = np.clip(
                x * 2,
                0,
                100
            )

        elif metric == "Debt/Equity":

            score = np.clip(
                100
                - max(x, 0) * 40,
                0,
                100
            )

        elif metric == "Net Debt/EBITDA":

            score = np.clip(
                100
                - max(x, 0) * 18,
                0,
                100
            )

        elif metric == "Current Ratio":

            score = np.clip(
                x * 50,
                0,
                100
            )

        elif metric == "Dividend Yield":

            score = np.clip(
                x * 12,
                0,
                100
            )

        elif metric == "P/E":

            score = (
                np.clip(
                    100
                    - abs(x - 12) * 4,
                    0,
                    100
                )
                if x > 0
                else np.nan
            )

        elif metric == "P/B":

            score = (
                np.clip(
                    100
                    - abs(x - 1.4) * 35,
                    0,
                    100
                )
                if x > 0
                else np.nan
            )

        else:

            score = 50

        if np.isfinite(score):
            fscore.append(
                (
                    score,
                    weights.get(
                        metric,
                        0
                    )
                )
            )

    if fscore:

        financial = (
            sum(
                score * weight
                for score, weight
                in fscore
            )
            /
            sum(
                weight
                for _, weight
                in fscore
            )
        )

    else:

        financial = np.nan

    quality = safe_mean(
        [
            forensic["piotroski"]
            * 100
            / 9,

            forensic["earnings_quality"],

            forensic["roic_quality"]
        ]
    )

    upside = num(
        val.get("Upside %")
    )

    valuation = (
        50
        + np.clip(
            upside,
            -50,
            100
        ) * .35
        if pd.notna(upside)
        else 50
    )

    technical_score = num(
        tech.get("score")
    )

    evidence = []

    if bt.get(
        "trades",
        0
    ) >= 5:

        evidence.append(
            np.clip(
                50
                + bt.get(
                    "expectancy",
                    0
                ) * 5,
                0,
                100
            )
        )

    if pd.notna(
        wfo.get("score")
    ):

        evidence.append(
            wfo["score"]
        )

    if bt.get(
        "trades",
        0
    ) >= 5:

        evidence.append(
            bt.get(
                "mc_profit_prob",
                50
            )
        )

    evidence_score = (
        float(
            np.mean(evidence)
        )
        if evidence
        else np.nan
    )

    stability_components = []

    if pd.notna(
        wfo.get("stability")
    ):
        stability_components.append(
            wfo["stability"]
        )

    if bt.get(
        "trades",
        0
    ):

        stability_components.append(
            np.clip(
                100
                - bt.get(
                    "max_dd",
                    50
                ) * 2,
                0,
                100
            )
        )

    stability = safe_mean(
        stability_components
    )

    parts = [
        (financial, .30),
        (quality, .15),
        (valuation, .15),
        (technical_score, .15),
        (evidence_score, .15),
        (stability, .10)
    ]

    available = [
        (value, weight)
        for value, weight
        in parts
        if pd.notna(value)
    ]

    if available:

        final = (
            sum(
                value * weight
                for value, weight
                in available
            )
            /
            sum(
                weight
                for _, weight
                in available
            )
        )

    else:

        final = np.nan

    return {
        "financial": financial,
        "forensic": quality,
        "valuation": valuation,
        "technical": technical_score,
        "evidence": evidence_score,
        "stability": stability,
        "final": final
    }


# ============================================================
# ANALYZE ONE
# ============================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False
)
def analyze_one(
    sym,
    run_bt=True,
    mc_runs=500
):

    ds = DataSourceManager(
        sym
    ).load()

    if not ds.ok:

        return {
            "symbol": sym,
            "error":
                ds.error
                or "Yahoo data unavailable"
        }

    raw = ds.data

    try:

        (
            m,
            inc,
            bal,
            cf,
            info
        ) = normalize_financials(
            raw
        )

        sec = sector(
            sym,
            info
        )

        # ----------------------------------------------------
        # History
        # ----------------------------------------------------

        try:

            hist = raw[
                "ticker"
            ].history(
                period="5y",
                interval="1d",
                auto_adjust=False
            )

        except Exception:

            hist = pd.DataFrame()

        # ----------------------------------------------------
        # IMPORTANT:
        # Use historical close as current price whenever
        # available. This prevents stale Yahoo info price.
        # ----------------------------------------------------

        latest_price = get_latest_close(
            hist
        )

        if (
            pd.notna(latest_price)
            and latest_price > 0
        ):

            m["Price"] = latest_price

            market_cap = num(
                m.get("Market Cap")
            )

            # Do NOT overwrite real sharesOutstanding.
            if (
                pd.isna(
                    num(m.get("Shares"))
                )
                and pd.notna(market_cap)
            ):

                m["Shares"] = (
                    market_cap
                    / latest_price
                )

        # ----------------------------------------------------
        # Market cap can be recalculated using current price
        # only if shares are known.
        # ----------------------------------------------------

        shares = num(
            m.get("Shares")
        )

        if (
            pd.notna(shares)
            and shares > 0
            and pd.notna(latest_price)
        ):

            m["Market Cap"] = (
                shares
                * latest_price
            )

        # ----------------------------------------------------
        # Forensic
        # ----------------------------------------------------

        pi, tests = piotroski(
            m,
            inc,
            bal,
            cf
        )

        bene = beneish(
            m
        )

        alt = altman(
            m,
            sec
        )

        eq, accr = earnings_quality(
            m
        )

        rq = roic_quality(
            m
        )

        div = dividend_engine(
            raw["ticker"],
            m.get("Price")
        )

        m["Dividend Yield"] = (
            div.get("yield")
        )

        # ----------------------------------------------------
        # Valuation
        # ----------------------------------------------------

        fin = {
            "sector": sec,
            "metrics": m
        }

        val = valuation_engine(
            m,
            sec
        )

        # ----------------------------------------------------
        # Technical / Backtest
        # ----------------------------------------------------

        tech = technical(
            hist
        )

        if run_bt:

            bt = backtest(
                hist,
                mc_runs=mc_runs
            )

            wfo = wfo_score(
                hist,
                mc_runs=min(
                    100,
                    mc_runs
                )
            )

        else:

            bt = {
                "trades": 0,
                "status":
                    "غير مفعل"
            }

            wfo = {
                "score": np.nan,
                "oos_return": np.nan,
                "stability": np.nan,
                "folds": 0
            }

        forensic = {
            "piotroski": pi,
            "piotroski_tests": tests,
            "beneish": bene,
            "altman": alt,
            "earnings_quality": eq,
            "accrual": accr,
            "roic_quality": rq
        }

        scores = score_stock(
            fin,
            forensic,
            val,
            tech,
            bt,
            wfo,
            div
        )

        metric_values = [
            v
            for k, v in m.items()
            if not str(k).startswith("_")
        ]

        coverage = (
            np.mean(
                [
                    pd.notna(v)
                    for v in metric_values
                ]
            )
            * 100
            if metric_values
            else 0
        )

        return {
            "symbol": sym,
            "name":
                info.get(
                    "longName",
                    sym
                ),
            "sector": sec,
            "industry":
                info.get(
                    "industry",
                    ""
                ),
            "metrics": m,
            "valuation": val,
            "dividend": div,
            "technical": tech,
            "backtest": bt,
            "wfo": wfo,
            "forensic": forensic,
            "scores": scores,
            "coverage": coverage,
            "source": "Yahoo Finance",
            "last_date":
                get_last_date(hist),
            "source_errors":
                raw.get(
                    "source_errors",
                    []
                )
        }

    except Exception as e:

        return {
            "symbol": sym,
            "error": str(e)
        }


# ============================================================
# RUN ALL
# ============================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False
)
def run_all(
    symbols,
    run_bt,
    mc_runs
):

    output = []

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        futures = {
            executor.submit(
                analyze_one,
                symbol,
                run_bt,
                mc_runs
            ): symbol
            for symbol in symbols
        }

        for future in as_completed(
            futures
        ):

            symbol = futures[
                future
            ]

            try:

                output.append(
                    future.result()
                )

            except Exception as e:

                output.append(
                    {
                        "symbol": symbol,
                        "error": str(e)
                    }
                )

    return output


# ============================================================
# UI
# ============================================================

st.title(
    "🏛️ EGX Institutional Analyzer V5.1"
)

st.caption(
    "Financial Intelligence + Realistic FCFF DCF + Relative Valuation + "
    "Forensic Quality + V9 Technical + Backtest/WFO/OOS + Monte Carlo + Stability"
)

with st.sidebar:

    st.header(
        "⚙️ إعدادات المؤسسة"
    )

    min_cov = st.slider(
        "أقل اكتمال بيانات %",
        0,
        100,
        55,
        5
    )

    top_n = st.number_input(
        "عدد الأسهم في الترتيب",
        5,
        100,
        20
    )

    run_bt = st.checkbox(
        "تشغيل Backtest + WFO/OOS + Monte Carlo",
        True
    )

    mc_runs = st.selectbox(
        "Monte Carlo",
        [100, 250, 500, 1000],
        index=2
    )

    if st.button(
        "🔄 تحديث كامل"
    ):

        analyze_one.clear()
        run_all.clear()

        st.rerun()


# ============================================================
# EXECUTION
# ============================================================

with st.spinner(
    "🏗️ بناء التحليل المؤسسي..."
):

    results = run_all(
        STOCKS,
        run_bt,
        mc_runs
    )


# ============================================================
# TABLE
# ============================================================

rows = []

for r in results:

    if r.get("error"):
        continue

    if r.get(
        "coverage",
        0
    ) < min_cov:
        continue

    s = r["scores"]
    v = r["valuation"]
    t = r["technical"]
    b = r["backtest"]
    w = r["wfo"]
    f = r["forensic"]
    d = r["dividend"]

    rows.append(
        {
            "الترتيب": 0,

            "السهم":
                r["symbol"].replace(
                    ".CA",
                    ""
                ),

            "القطاع":
                r["sector"],

            "الدرجة النهائية":
                s.get("final"),

            "المالي":
                s.get("financial"),

            "الجودة المحاسبية":
                s.get("forensic"),

            "التقييم":
                s.get("valuation"),

            "الفني V9":
                s.get("technical"),

            "الدليل الإحصائي":
                s.get("evidence"),

            "الاستقرار":
                s.get("stability"),

            "القيمة العادلة":
                v.get("Fair Value"),

            "القيمة العادلة منخفضة":
                v.get("Fair Value Low"),

            "القيمة العادلة مرتفعة":
                v.get("Fair Value High"),

            "DCF محافظ":
                v.get("DCF Conservative"),

            "DCF Base":
                v.get("DCF Base"),

            "DCF متفائل":
                v.get("DCF Optimistic"),

            "Relative":
                v.get("Relative"),

            "شراء 20% MOS":
                v.get("Buy 20% MOS"),

            "شراء قوي 30% MOS":
                v.get("Strong Buy 30% MOS"),

            "الصعود %":
                v.get("Upside %"),

            "Piotroski":
                f["piotroski"],

            "Beneish Flags":
                f["beneish"]["risk_flags"],

            "Altman Z":
                f["altman"]["score"],

            "جودة الأرباح":
                f["earnings_quality"],

            "ROIC Quality":
                f["roic_quality"],

            "Dividend Yield %":
                d.get("yield"),

            "صفقات Backtest":
                b.get("trades", 0),

            "Win Rate %":
                b.get("win_rate", np.nan),

            "Return %":
                b.get("return", np.nan),

            "Max DD %":
                b.get("max_dd", np.nan),

            "Profit Factor":
                b.get("pf", np.nan),

            "Expectancy %":
                b.get("expectancy", np.nan),

            "Sharpe":
                b.get("sharpe", np.nan),

            "WFO Score":
                w.get("score", np.nan),

            "OOS Return %":
                w.get("oos_return", np.nan),

            "MC Median %":
                b.get("mc50", np.nan),

            "MC Profit Prob %":
                b.get(
                    "mc_profit_prob",
                    np.nan
                ),

            "اكتمال البيانات %":
                r["coverage"],

            "آخر شمعة":
                r["last_date"]
        }
    )


df = pd.DataFrame(
    rows
)

if not df.empty:

    df = df.sort_values(
        "الدرجة النهائية",
        ascending=False,
        na_position="last"
    ).reset_index(
        drop=True
    )

    df["الترتيب"] = (
        np.arange(
            1,
            len(df) + 1
        )
    )


# ============================================================
# RANKING
# ============================================================

st.subheader(
    "🏆 الترتيب المؤسسي النهائي"
)

if df.empty:

    st.warning(
        "لا توجد نتائج مؤهلة وفق حد اكتمال البيانات."
    )

else:

    st.dataframe(
        df.head(
            int(top_n)
        ),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ تنزيل التقرير CSV",
        df.to_csv(
            index=False,
            encoding="utf-8-sig"
        ).encode(
            "utf-8-sig"
        ),
        "EGX_Institutional_V5_1.csv",
        "text/csv"
    )


# ============================================================
# FULL STOCK REPORT
# ============================================================

st.subheader(
    "🔎 تقرير مؤسسي كامل لسهم"
)

valid = [
    r
    for r in results
    if not r.get("error")
]

if valid:

    symbols_sorted = sorted(
        [
            r["symbol"]
            for r in valid
        ]
    )

    sel = st.selectbox(
        "اختر السهم",
        symbols_sorted,
        format_func=lambda x:
            x.replace(
                ".CA",
                ""
            )
    )

    r = next(
        x
        for x in valid
        if x["symbol"] == sel
    )

    s = r["scores"]
    f = r["forensic"]
    v = r["valuation"]
    t = r["technical"]
    b = r["backtest"]
    w = r["wfo"]
    d = r["dividend"]

    # --------------------------------------------------------
    # Score cards
    # --------------------------------------------------------

    cols = st.columns(
        7
    )

    values = [
        s.get("final"),
        s.get("financial"),
        s.get("forensic"),
        s.get("valuation"),
        s.get("technical"),
        s.get("evidence"),
        s.get("stability")
    ]

    labels = [
        "Final Investment Score",
        "Financial",
        "Forensic",
        "Valuation",
        "Technical V9",
        "Evidence",
        "Stability"
    ]

    for col, label, value in zip(
        cols,
        labels,
        values
    ):

        col.metric(
            label,
            (
                "—"
                if pd.isna(value)
                else f"{value:.1f}"
            )
        )

    st.write(
        f"**{r['name']}** | "
        f"القطاع: **{r['sector']}** | "
        f"آخر شمعة: **{r['last_date']}** | "
        f"المصدر الأساسي: **{r['source']}** | "
        f"اكتمال البيانات: **{r['coverage']:.0f}%**"
    )

    # ========================================================
    # VALUATION
    # ========================================================

    st.markdown(
        "### 💰 Valuation V2 — DCF / FCFF + Relative"
    )

    valuation_rows = [
        {
            "النموذج":
                "DCF محافظ",
            "القيمة":
                v.get(
                    "DCF Conservative"
                )
        },
        {
            "النموذج":
                "DCF Base",
            "القيمة":
                v.get(
                    "DCF Base"
                )
        },
        {
            "النموذج":
                "DCF متفائل",
            "القيمة":
                v.get(
                    "DCF Optimistic"
                )
        },
        {
            "النموذج":
                "Relative P/E + P/B",
            "القيمة":
                v.get(
                    "Relative"
                )
        },
        {
            "النموذج":
                "P/E Fair Value",
            "القيمة":
                v.get(
                    "PE Fair Value"
                )
        },
        {
            "النموذج":
                "P/B Fair Value",
            "القيمة":
                v.get(
                    "PB Fair Value"
                )
        },
        {
            "النموذج":
                "القيمة العادلة المنخفضة",
            "القيمة":
                v.get(
                    "Fair Value Low"
                )
        },
        {
            "النموذج":
                "القيمة العادلة الأساسية",
            "القيمة":
                v.get(
                    "Fair Value"
                )
        },
        {
            "النموذج":
                "القيمة العادلة المرتفعة",
            "القيمة":
                v.get(
                    "Fair Value High"
                )
        },
        {
            "النموذج":
                "شراء بهامش أمان 20%",
            "القيمة":
                v.get(
                    "Buy 20% MOS"
                )
        },
        {
            "النموذج":
                "شراء قوي بهامش أمان 30%",
            "القيمة":
                v.get(
                    "Strong Buy 30% MOS"
                )
        },
        {
            "النموذج":
                "الصعود المحتمل %",
            "القيمة":
                v.get(
                    "Upside %"
                )
        },
        {
            "النموذج":
                "الصعود المحافظ %",
            "القيمة":
                v.get(
                    "Conservative Upside %"
                )
        }
    ]

    valuation_df = pd.DataFrame(
        valuation_rows
    )

    st.dataframe(
        valuation_df.style.format(
            {
                "القيمة": "{:.2f}"
            },
            na_rep="—"
        ),
        use_container_width=True,
        hide_index=True
    )

    st.write(
        f"**منهج التقييم:** "
        f"{v.get('Valuation Method', '—')}"
    )

    st.write(
        f"**WACC Base:** "
        f"{v.get('WACC Base', np.nan):.2f}% | "
        f"**Terminal Growth:** "
        f"{v.get('Terminal Growth Base', np.nan):.2f}% | "
        f"**PE Reference:** "
        f"{v.get('PE Reference', np.nan):.2f} | "
        f"**PB Reference:** "
        f"{v.get('PB Reference', np.nan):.2f}"
    )

    # ========================================================
    # FORENSIC
    # ========================================================

    st.markdown(
        "### 🧪 Forensic Accounting"
    )

    forensic_rows = [
        {
            "المحرك":
                "Piotroski F-Score",
            "القيمة":
                f["piotroski"],
            "المعنى":
                "قوة مالية تشغيلية"
        },
        {
            "المحرك":
                "Beneish Screening",
            "القيمة":
                f["beneish"][
                    "risk_flags"
                ],
            "المعنى":
                f["beneish"][
                    "status"
                ]
        },
        {
            "المحرك":
                "Altman Z-Score",
            "القيمة":
                f["altman"][
                    "score"
                ],
            "المعنى":
                f["altman"][
                    "status"
                ]
        },
        {
            "المحرك":
                "Earnings Quality",
            "القيمة":
                f["earnings_quality"],
            "المعنى":
                "جودة الأرباح والتدفقات"
        },
        {
            "المحرك":
                "ROIC Quality",
            "القيمة":
                f["roic_quality"],
            "المعنى":
                "كفاءة رأس المال"
        }
    ]

    st.dataframe(
        pd.DataFrame(
            forensic_rows
        ).style.format(
            {
                "القيمة": "{:.2f}"
            },
            na_rep="—"
        ),
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # TECHNICAL
    # ========================================================

    st.markdown(
        "### 📈 V9 Technical"
    )

    techdf = pd.DataFrame(
        [
            {
                "المؤشر": key,
                "القيمة": value
            }
            for key, value
            in t.items()
        ]
    )

    st.dataframe(
        techdf,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # BACKTEST
    # ========================================================

    st.markdown(
        "### 🧪 Backtest + WFO/OOS + Monte Carlo"
    )

    evidence_rows = []

    for key, value in b.items():

        evidence_rows.append(
            {
                "المؤشر": key,
                "القيمة": value
            }
        )

    for key, value in w.items():

        evidence_rows.append(
            {
                "المؤشر": key,
                "القيمة": value
            }
        )

    st.dataframe(
        pd.DataFrame(
            evidence_rows
        ),
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # DIVIDENDS
    # ========================================================

    st.markdown(
        "### 💵 Dividend Sustainability"
    )

    st.dataframe(
        pd.DataFrame(
            [d]
        ),
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # FINANCIAL DATA
    # ========================================================

    st.markdown(
        "### 📊 Financial Normalized Data"
    )

    financial_rows = [
        {
            "المؤشر": key,
            "القيمة": value
        }
        for key, value
        in r["metrics"].items()
        if not str(key).startswith("_")
    ]

    st.dataframe(
        pd.DataFrame(
            financial_rows
        ),
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # DATA WARNINGS
    # ========================================================

    source_errors = r.get(
        "source_errors",
        []
    )

    if source_errors:

        with st.expander(
            "⚠️ ملاحظات مصدر البيانات"
        ):

            for error in source_errors:

                st.write(
                    f"- {error}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EGX Institutional V5.1 — "
    "الأسعار الحالية تعتمد على آخر شمعة تاريخية متاحة عند توفرها، "
    "بدل الاعتماد فقط على currentPrice من Yahoo. "
    "DCF يستخدم FCFF أكثر اتساقًا، مع سيناريوهات محافظ/Base/متفائل، "
    "وRelative Valuation باستخدام P/E وP/B. "
    "النماذج أدوات تحليلية وليست ضمانًا للنتائج المستقبلية."
)
