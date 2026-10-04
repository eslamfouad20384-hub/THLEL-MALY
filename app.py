import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Any, Optional

st.set_page_config(
    page_title='EGX Institutional V5',
    page_icon='🏛️',
    layout='wide'
)

# ============================================================
# EGX INSTITUTIONAL V5
# Data -> TTM Normalization -> Financial Quality ->
# True FCFF Valuation -> 3 Scenario DCF ->
# Relative Valuation -> Dividends ->
# V9 Technical -> Backtest/WFO/OOS/Monte Carlo ->
# Stability -> Final Investment Score
# ============================================================

RAW = '''COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN MPCO ELSH MEPA ODIN EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH'''.split()

STOCKS = list(dict.fromkeys(x + '.CA' for x in RAW))

BANKS = set('COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB'.split())

RE = set(
    'PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD DCRC ARCC '
    'RMDA IDRE RREI EGREF EHDR MENA MPRC'.split()
)

HEALTH = set(
    'BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH'.split()
)

TECH = set('ETEL MTIE RAYA EFIH UBEE DGTZ GOUR'.split())

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
    if x not in BANKS | RE | HEALTH | TECH | ENERGY |
    CONSUMER | CONSTRUCTION | FIN
)

SECTOR_RULES = {
    'Banks': [
        'ROE', 'ROA', 'NIM', 'Cost/Income', 'NPL',
        'NPL Coverage', 'CAR', 'Loan Growth', 'Deposit Growth',
        'Net Income Growth', 'P/B', 'P/E', 'Dividend Yield'
    ],
    'Real Estate': [
        'Revenue Growth', 'EPS Growth', 'EBITDA Margin',
        'Net Margin', 'ROE', 'Debt/Equity', 'Net Debt/EBITDA',
        'Operating Cash Flow', 'FCF Margin', 'P/B', 'P/E'
    ],
    'Healthcare': [
        'Revenue Growth', 'EPS Growth', 'Net Margin',
        'EBITDA Margin', 'ROE', 'ROA', 'FCF Margin',
        'Debt/Equity', 'Current Ratio', 'P/E', 'P/B'
    ],
    'Telecom & Technology': [
        'Revenue Growth', 'EPS Growth', 'EBITDA Margin',
        'Net Margin', 'ROIC', 'FCF Margin', 'Net Debt/EBITDA',
        'ROE', 'P/E', 'EV/EBITDA', 'Dividend Yield'
    ],
    'Energy & Petrochemicals': [
        'Revenue Growth', 'EPS Growth', 'EBITDA Margin',
        'Net Margin', 'ROIC', 'FCF Margin', 'Debt/Equity',
        'Net Debt/EBITDA', 'ROE', 'P/E', 'EV/EBITDA',
        'Dividend Yield'
    ],
    'Consumer': [
        'Revenue Growth', 'EPS Growth', 'Gross Margin',
        'EBITDA Margin', 'Net Margin', 'ROE', 'ROIC',
        'FCF Margin', 'Debt/Equity', 'P/E', 'Dividend Yield'
    ],
    'Construction & Engineering': [
        'Revenue Growth', 'EBITDA Margin', 'Net Margin',
        'ROE', 'ROIC', 'Operating Cash Flow', 'FCF Margin',
        'Debt/Equity', 'Net Debt/EBITDA', 'P/E', 'P/B'
    ],
    'Industrial & Materials': [
        'Revenue Growth', 'EPS Growth', 'Gross Margin',
        'EBITDA Margin', 'Net Margin', 'ROE', 'ROIC',
        'FCF Margin', 'Debt/Equity', 'Net Debt/EBITDA',
        'P/E', 'P/B', 'Dividend Yield'
    ],
    'Financial Services': [
        'Revenue Growth', 'Net Income Growth', 'ROE', 'ROA',
        'Net Margin', 'Debt/Equity', 'Current Ratio',
        'P/E', 'P/B', 'Dividend Yield'
    ],
    'General': [
        'Revenue Growth', 'EPS Growth', 'Net Margin', 'ROE',
        'ROA', 'ROIC', 'FCF Margin', 'Debt/Equity',
        'Current Ratio', 'P/E', 'P/B', 'Dividend Yield'
    ]
}

WEIGHTS = {
    k: {m: 1 / len(v)}
    for k, v in SECTOR_RULES.items()
}

WEIGHTS['Banks'] = {
    'ROE': .15,
    'ROA': .07,
    'NIM': .12,
    'Cost/Income': .10,
    'NPL': .10,
    'NPL Coverage': .07,
    'CAR': .10,
    'Loan Growth': .07,
    'Deposit Growth': .05,
    'Net Income Growth': .08,
    'P/B': .05,
    'P/E': .02,
    'Dividend Yield': .02
}


# ============================================================
# BASIC HELPERS
# ============================================================

def num(x):
    try:
        x = float(x)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan


def pct(x):
    x = num(x)
    return np.nan if pd.isna(x) else x * 100


def clean_series(s):
    if s is None:
        return None

    try:
        s = pd.to_numeric(s, errors='coerce').dropna()
        if len(s) == 0:
            return None

        if not isinstance(s.index, pd.DatetimeIndex):
            try:
                s.index = pd.to_datetime(s.index)
            except Exception:
                pass

        return s
    except Exception:
        return None


def last(s):
    s = clean_series(s)

    if s is None or len(s) == 0:
        return np.nan

    return num(s.iloc[0])


def growth(s):
    s = clean_series(s)

    if s is None or len(s) < 2:
        return np.nan

    current = num(s.iloc[0])
    previous = num(s.iloc[1])

    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return np.nan

    return (current / previous - 1) * 100


def growth_ttm(current, previous):
    current = num(current)
    previous = num(previous)

    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return np.nan

    return (current / previous - 1) * 100


def find(df, names):
    if df is None or df.empty:
        return None

    for name in names:
        if name in df.index:
            return pd.to_numeric(df.loc[name], errors='coerce')

    for idx in df.index:
        low = str(idx).lower()

        for name in names:
            nl = name.lower()

            if nl in low or low in nl:
                return pd.to_numeric(df.loc[idx], errors='coerce')

    return None


def sum_last_n(s, n=4):
    s = clean_series(s)

    if s is None or len(s) < n:
        return np.nan

    return num(s.iloc[:n].sum())


def sum_period(s, start, end):
    s = clean_series(s)

    if s is None:
        return np.nan

    try:
        x = s[(s.index >= start) & (s.index <= end)]

        if x.empty:
            return np.nan

        return num(x.sum())
    except Exception:
        return np.nan


def get_latest_balance(df, names):
    return last(find(df, names))


def get_series_value(df, names):
    return find(df, names)


# ============================================================
# SECTOR
# ============================================================

def sector(sym, info):
    s = sym.replace('.CA', '')

    groups = [
        (BANKS, 'Banks'),
        (RE, 'Real Estate'),
        (HEALTH, 'Healthcare'),
        (TECH, 'Telecom & Technology'),
        (ENERGY, 'Energy & Petrochemicals'),
        (CONSUMER, 'Consumer'),
        (CONSTRUCTION, 'Construction & Engineering'),
        (FIN, 'Financial Services'),
        (INDUSTRIAL, 'Industrial & Materials')
    ]

    for g, n in groups:
        if s in g:
            return n

    text = (
        str(info.get('sector', '')) +
        ' ' +
        str(info.get('industry', ''))
    ).lower()

    if 'bank' in text:
        return 'Banks'

    if 'real estate' in text:
        return 'Real Estate'

    if any(x in text for x in ['health', 'medical', 'pharma']):
        return 'Healthcare'

    if any(
        x in text
        for x in ['telecom', 'software', 'technology', 'internet']
    ):
        return 'Telecom & Technology'

    if any(
        x in text
        for x in ['oil', 'gas', 'energy', 'petro']
    ):
        return 'Energy & Petrochemicals'

    if any(
        x in text
        for x in ['consumer', 'food', 'beverage', 'retail']
    ):
        return 'Consumer'

    if 'construction' in text or 'engineering' in text:
        return 'Construction & Engineering'

    if any(
        x in text
        for x in ['financial', 'insurance', 'investment']
    ):
        return 'Financial Services'

    return 'General'


# ============================================================
# MULTI-SOURCE DATA
# ============================================================

@dataclass
class SourceResult:
    source: str
    ok: bool
    data: Any = None
    error: str = ''


class DataSourceManager:

    def __init__(self, ticker):
        self.ticker = ticker

    def yahoo(self):

        t = yf.Ticker(self.ticker)

        info = t.info or {}

        financials = t.financials
        balance = t.balance_sheet
        cashflow = t.cashflow

        # NEW:
        # Quarterly data for proper TTM calculations.
        try:
            q_financials = t.quarterly_financials
        except Exception:
            q_financials = pd.DataFrame()

        try:
            q_balance = t.quarterly_balance_sheet
        except Exception:
            q_balance = pd.DataFrame()

        try:
            q_cashflow = t.quarterly_cashflow
        except Exception:
            q_cashflow = pd.DataFrame()

        return SourceResult(
            'Yahoo Finance',
            True,
            {
                'ticker': t,
                'info': info,
                'financials': financials,
                'balance': balance,
                'cashflow': cashflow,
                'q_financials': q_financials,
                'q_balance': q_balance,
                'q_cashflow': q_cashflow
            }
        )

    def load(self):

        try:
            return self.yahoo()

        except Exception as e:

            return SourceResult(
                'Yahoo Finance',
                False,
                error=str(e)
            )


# ============================================================
# PRICE FROM HISTORY
# ============================================================

def latest_market_price(ticker, info):
    """
    Uses the latest daily candle as the primary price.
    Falls back to Yahoo currentPrice / regularMarketPrice.
    """

    try:

        hist = ticker.history(
            period='15d',
            interval='1d',
            auto_adjust=False
        )

        if (
            hist is not None
            and not hist.empty
            and 'Close' in hist.columns
        ):

            close = pd.to_numeric(
                hist['Close'],
                errors='coerce'
            ).dropna()

            if not close.empty:

                price = num(close.iloc[-1])

                last_date = close.index[-1]

                try:
                    last_date = pd.Timestamp(last_date).strftime(
                        '%Y-%m-%d'
                    )
                except Exception:
                    last_date = '—'

                return price, last_date

    except Exception:
        pass

    for key in [
        'regularMarketPrice',
        'currentPrice',
        'previousClose'
    ]:

        p = num(info.get(key))

        if pd.notna(p) and p > 0:
            return p, '—'

    return np.nan, '—'


# ============================================================
# TTM HELPERS
# ============================================================

def ttm_flow(qdf, names, annual_df=None):
    """
    Prefer latest 4 quarters.
    If quarterly data is unavailable, fallback to latest annual.
    """

    s = find(qdf, names)

    if s is not None:

        s = clean_series(s)

        if s is not None and len(s) >= 4:
            return sum_last_n(s, 4)

        if s is not None and len(s) > 0:
            # Partial quarterly data:
            # do not fabricate a TTM from incomplete quarters.
            return np.nan

    if annual_df is not None:
        return last(find(annual_df, names))

    return np.nan


def previous_ttm_flow(qdf, names, annual_df=None):
    """
    Previous 4-quarter period.
    Used for proper TTM growth.
    """

    s = find(qdf, names)

    if s is not None:

        s = clean_series(s)

        if s is not None and len(s) >= 8:
            return num(s.iloc[4:8].sum())

    # Annual fallback:
    # latest annual vs previous annual.
    if annual_df is not None:
        s = clean_series(find(annual_df, names))

        if s is not None and len(s) >= 2:
            return num(s.iloc[1])

    return np.nan


def ttm_eps(qdf, names, annual_df=None):
    s = find(qdf, names)

    if s is not None:

        s = clean_series(s)

        if s is not None and len(s) >= 4:
            return num(s.iloc[:4].sum())

    if annual_df is not None:
        return last(find(annual_df, names))

    return np.nan


# ============================================================
# FINANCIAL NORMALIZATION
# ============================================================

def normalize_financials(raw):

    info = raw.get('info', {})

    inc = raw.get(
        'financials',
        pd.DataFrame()
    )

    bal = raw.get(
        'balance',
        pd.DataFrame()
    )

    cf = raw.get(
        'cashflow',
        pd.DataFrame()
    )

    qinc = raw.get(
        'q_financials',
        pd.DataFrame()
    )

    qbal = raw.get(
        'q_balance',
        pd.DataFrame()
    )

    qcf = raw.get(
        'q_cashflow',
        pd.DataFrame()
    )

    # --------------------------------------------------------
    # TTM FLOW ITEMS
    # --------------------------------------------------------

    R = ttm_flow(
        qinc,
        ['Total Revenue', 'Operating Revenue', 'Revenue'],
        inc
    )

    R_prev = previous_ttm_flow(
        qinc,
        ['Total Revenue', 'Operating Revenue', 'Revenue'],
        inc
    )

    NI = ttm_flow(
        qinc,
        ['Net Income', 'Net Income Common Stockholders'],
        inc
    )

    NI_prev = previous_ttm_flow(
        qinc,
        ['Net Income', 'Net Income Common Stockholders'],
        inc
    )

    EBIT = ttm_flow(
        qinc,
        ['EBIT', 'Operating Income'],
        inc
    )

    EBITDA = ttm_flow(
        qinc,
        ['EBITDA', 'Normalized EBITDA'],
        inc
    )

    GROSS = ttm_flow(
        qinc,
        ['Gross Profit'],
        inc
    )

    OCF = ttm_flow(
        qcf,
        [
            'Operating Cash Flow',
            'Total Cash From Operating Activities'
        ],
        cf
    )

    CAPEX = ttm_flow(
        qcf,
        [
            'Capital Expenditure',
            'Capital Expenditures'
        ],
        cf
    )

    DA = ttm_flow(
        qcf,
        [
            'Depreciation And Amortization',
            'Depreciation',
            'Depreciation And Amortization In Cash Flow'
        ],
        cf
    )

    TAX = ttm_flow(
        qinc,
        [
            'Tax Provision',
            'Income Tax Expense'
        ],
        inc
    )

    PRETAX = ttm_flow(
        qinc,
        [
            'Pretax Income',
            'Pretax Income Loss'
        ],
        inc
    )

    # --------------------------------------------------------
    # BALANCE SHEET
    # Latest available quarter first.
    # --------------------------------------------------------

    EQ = get_latest_balance(
        qbal,
        [
            'Stockholders Equity',
            'Total Equity Gross Minority Interest',
            'Common Stock Equity'
        ]
    )

    if pd.isna(EQ):
        EQ = get_latest_balance(
            bal,
            [
                'Stockholders Equity',
                'Total Equity Gross Minority Interest',
                'Common Stock Equity'
            ]
        )

    AS = get_latest_balance(
        qbal,
        ['Total Assets']
    )

    if pd.isna(AS):
        AS = get_latest_balance(
            bal,
            ['Total Assets']
        )

    D = get_latest_balance(
        qbal,
        [
            'Total Debt',
            'Long Term Debt',
            'Total Debt And Capital Lease Obligation'
        ]
    )

    if pd.isna(D):
        D = get_latest_balance(
            bal,
            [
                'Total Debt',
                'Long Term Debt',
                'Total Debt And Capital Lease Obligation'
            ]
        )

    C = get_latest_balance(
        qbal,
        [
            'Cash Cash Equivalents And Short Term Investments',
            'Cash And Cash Equivalents',
            'Cash Financial'
        ]
    )

    if pd.isna(C):
        C = get_latest_balance(
            bal,
            [
                'Cash Cash Equivalents And Short Term Investments',
                'Cash And Cash Equivalents',
                'Cash Financial'
            ]
        )

    CURRENT_ASSETS = get_latest_balance(
        qbal,
        [
            'Current Assets',
            'Total Current Assets'
        ]
    )

    if pd.isna(CURRENT_ASSETS):
        CURRENT_ASSETS = get_latest_balance(
            bal,
            [
                'Current Assets',
                'Total Current Assets'
            ]
        )

    CURRENT_LIABILITIES = get_latest_balance(
        qbal,
        [
            'Current Liabilities',
            'Total Current Liabilities'
        ]
    )

    if pd.isna(CURRENT_LIABILITIES):
        CURRENT_LIABILITIES = get_latest_balance(
            bal,
            [
                'Current Liabilities',
                'Total Current Liabilities'
            ]
        )

    WORKING_CAPITAL = (
        CURRENT_ASSETS - CURRENT_LIABILITIES
        if pd.notna(CURRENT_ASSETS)
        and pd.notna(CURRENT_LIABILITIES)
        else np.nan
    )

    RETAINED = get_latest_balance(
        qbal,
        [
            'Retained Earnings',
            'Retained Earnings Common'
        ]
    )

    if pd.isna(RETAINED):
        RETAINED = get_latest_balance(
            bal,
            [
                'Retained Earnings',
                'Retained Earnings Common'
            ]
        )

    # --------------------------------------------------------
    # PRICE / SHARES
    # --------------------------------------------------------

    price, last_price_date = latest_market_price(
        raw['ticker'],
        info
    )

    mcap = num(info.get('marketCap'))

    shares = num(
        info.get('sharesOutstanding')
    )

    # Safe fallback.
    if pd.isna(shares) or shares <= 0:

        if (
            pd.notna(mcap)
            and pd.notna(price)
            and price > 0
        ):
            shares = mcap / price

    EPS = ttm_eps(
        qinc,
        ['Diluted EPS', 'Basic EPS'],
        inc
    )

    # If EPS is unavailable, derive it from TTM NI / shares.
    if (
        pd.isna(EPS)
        and pd.notna(NI)
        and pd.notna(shares)
        and shares > 0
    ):
        EPS = NI / shares

    BVPS = (
        EQ / shares
        if pd.notna(EQ)
        and pd.notna(shares)
        and shares > 0
        else np.nan
    )

    # --------------------------------------------------------
    # FCFF INPUTS
    # --------------------------------------------------------

    # Tax rate:
    # use actual TTM tax / pretax when possible.
    tax_rate = np.nan

    if (
        pd.notna(TAX)
        and pd.notna(PRETAX)
        and PRETAX > 0
    ):
        tax_rate = np.clip(
            TAX / PRETAX,
            0,
            .40
        )

    if pd.isna(tax_rate):
        tax_rate = .22

    # NOPAT
    NOPAT = (
        EBIT * (1 - tax_rate)
        if pd.notna(EBIT)
        else np.nan
    )

    # FCFF historical proxy:
    # NOPAT + D&A - Capex - change NWC
    #
    # Change in NWC requires two balance-sheet dates.
    # If unavailable, keep Delta NWC at zero rather than inventing it.
    delta_nwc = 0.0

    # Capex is normally negative in cashflow statements.
    capex_outflow = (
        abs(CAPEX)
        if pd.notna(CAPEX)
        else np.nan
    )

    FCFF = np.nan

    if (
        pd.notna(NOPAT)
        and pd.notna(DA)
        and pd.notna(capex_outflow)
    ):
        FCFF = (
            NOPAT
            + DA
            - capex_outflow
            - delta_nwc
        )

    # --------------------------------------------------------
    # OLD FCF retained for quality analysis
    # --------------------------------------------------------

    FCF = np.nan

    if pd.notna(OCF) and pd.notna(CAPEX):

        if CAPEX < 0:
            FCF = OCF + CAPEX
        else:
            FCF = OCF - CAPEX

    # --------------------------------------------------------
    # FCF GROWTH
    # --------------------------------------------------------

    previous_fcf = np.nan

    prev_ocf = previous_ttm_flow(
        qcf,
        [
            'Operating Cash Flow',
            'Total Cash From Operating Activities'
        ],
        cf
    )

    prev_capex = previous_ttm_flow(
        qcf,
        [
            'Capital Expenditure',
            'Capital Expenditures'
        ],
        cf
    )

    if (
        pd.notna(prev_ocf)
        and pd.notna(prev_capex)
    ):

        if prev_capex < 0:
            previous_fcf = prev_ocf + prev_capex
        else:
            previous_fcf = prev_ocf - prev_capex

    FCF_GROWTH = growth_ttm(
        FCF,
        previous_fcf
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    metrics = {

        # TTM core
        'Revenue': R,
        'Net Income': NI,
        'Equity': EQ,
        'Assets': AS,
        'Debt': D,
        'Cash': C,

        'Operating Cash Flow': OCF,
        'Capex': CAPEX,
        'FCF': FCF,

        # True FCFF
        'EBIT': EBIT,
        'EBITDA': EBITDA,
        'D&A': DA,
        'Tax Rate': tax_rate * 100,
        'NOPAT': NOPAT,
        'Delta NWC': delta_nwc,
        'FCFF': FCFF,

        'Gross Profit': GROSS,

        'EPS': EPS,
        'BVPS': BVPS,

        'Shares': shares,
        'Market Cap': mcap,
        'Price': price,

        'Working Capital': WORKING_CAPITAL,
        'Retained Earnings': RETAINED,

        # TTM Growth
        'Revenue Growth': growth_ttm(
            R,
            R_prev
        ),

        'Net Income Growth': growth_ttm(
            NI,
            NI_prev
        ),

        'EPS Growth': np.nan,

        # FCF Growth is independent
        'FCF Growth': FCF_GROWTH
    }

    # EPS growth using quarterly EPS when possible.
    eps_series = clean_series(
        find(
            qinc,
            ['Diluted EPS', 'Basic EPS']
        )
    )

    if eps_series is not None and len(eps_series) >= 8:

        current_eps_ttm = num(
            eps_series.iloc[:4].sum()
        )

        previous_eps_ttm = num(
            eps_series.iloc[4:8].sum()
        )

        metrics['EPS Growth'] = growth_ttm(
            current_eps_ttm,
            previous_eps_ttm
        )

    else:

        annual_eps = find(
            inc,
            ['Diluted EPS', 'Basic EPS']
        )

        metrics['EPS Growth'] = growth(
            annual_eps
        )

    # --------------------------------------------------------
    # RATIOS
    # --------------------------------------------------------

    metrics.update({

        'Gross Margin':
            GROSS / R * 100
            if pd.notna(GROSS)
            and pd.notna(R)
            and R
            else np.nan,

        'EBITDA Margin':
            EBITDA / R * 100
            if pd.notna(EBITDA)
            and pd.notna(R)
            and R
            else np.nan,

        'Net Margin':
            NI / R * 100
            if pd.notna(NI)
            and pd.notna(R)
            and R
            else np.nan,

        'ROE':
            NI / EQ * 100
            if pd.notna(NI)
            and pd.notna(EQ)
            and EQ
            else pct(info.get('returnOnEquity')),

        'ROA':
            NI / AS * 100
            if pd.notna(NI)
            and pd.notna(AS)
            and AS
            else pct(info.get('returnOnAssets')),

        'ROIC':
            EBIT /
            (
                EQ + D -
                (C if pd.notna(C) else 0)
            ) * 100
            if pd.notna(EBIT)
            and pd.notna(EQ)
            and pd.notna(D)
            and (
                EQ + D -
                (C if pd.notna(C) else 0)
            )
            else np.nan,

        'FCF Margin':
            FCF / R * 100
            if pd.notna(FCF)
            and pd.notna(R)
            and R
            else np.nan,

        'FCFF Margin':
            FCFF / R * 100
            if pd.notna(FCFF)
            and pd.notna(R)
            and R
            else np.nan,

        'Debt/Equity':
            D / EQ
            if pd.notna(D)
            and pd.notna(EQ)
            and EQ
            else (
                num(info.get('debtToEquity')) / 100
                if pd.notna(
                    num(info.get('debtToEquity'))
                )
                else np.nan
            ),

        'Net Debt/EBITDA':
            (D - C) / EBITDA
            if pd.notna(D)
            and pd.notna(C)
            and pd.notna(EBITDA)
            and EBITDA
            else np.nan,

        'Current Ratio':
            num(info.get('currentRatio')),

        'P/E':
            (
                price / EPS
                if pd.notna(price)
                and pd.notna(EPS)
                and EPS > 0
                else num(info.get('trailingPE'))
            ),

        'P/B':
            (
                price / BVPS
                if pd.notna(price)
                and pd.notna(BVPS)
                and BVPS > 0
                else num(info.get('priceToBook'))
            ),

        'EV/EBITDA':
            num(info.get('enterpriseToEbitda')),

        'Dividend Yield':
            pct(info.get('dividendYield'))
    })

    return (
        metrics,
        inc,
        bal,
        cf,
        info,
        last_price_date
    )


# ============================================================
# FORENSIC QUALITY
# ============================================================

def piotroski(m, inc, bal, cf):

    points = 0
    tests = []

    roe = num(m.get('ROE'))
    ocf = num(m.get('Operating Cash Flow'))
    NI = num(m.get('Net Income'))
    margin = num(m.get('Net Margin'))
    fcf = num(m.get('FCF'))

    checks = [

        ('صافي الربح موجب', NI > 0),

        ('التدفق التشغيلي موجب', ocf > 0),

        ('ROE موجب', roe > 0),

        ('FCF موجب', fcf > 0),

        ('هامش صافي موجب', margin > 0),

        (
            'الدين/حقوق الملكية تحت السيطرة',
            num(m.get('Debt/Equity')) < 1.5
        ),

        (
            'نمو الإيرادات موجب',
            num(m.get('Revenue Growth')) > 0
        ),

        (
            'نمو صافي الربح موجب',
            num(m.get('Net Income Growth')) > 0
        ),

        (
            'نمو EPS موجب',
            num(m.get('EPS Growth')) > 0
        )
    ]

    for n, c in checks:

        passed = int(bool(c))

        points += passed

        tests.append(
            (n, passed)
        )

    return min(points, 9), tests


def beneish(m):

    components = {
        'DSRI': np.nan,
        'GMI': np.nan,
        'AQI': np.nan,
        'SGI': np.nan,
        'DEPI': np.nan,
        'SGAI': np.nan,
        'LVGI': np.nan,
        'TATA': np.nan
    }

    risk = 0
    available = 0

    revenue_growth = num(
        m.get('Revenue Growth')
    )

    if pd.notna(revenue_growth):

        available += 1

        if revenue_growth > 80:
            risk += 1

    net_margin = num(
        m.get('Net Margin')
    )

    if pd.notna(net_margin):

        available += 1

        if net_margin < 0:
            risk += 1

    de = num(
        m.get('Debt/Equity')
    )

    if pd.notna(de):

        available += 1

        if de > 2:
            risk += 1

    fcf_margin = num(
        m.get('FCF Margin')
    )

    if pd.notna(fcf_margin):

        available += 1

        if fcf_margin < 0:
            risk += 1

    return {
        'risk_flags': risk,
        'available': available,
        'components': components,
        'status':
            'مبدئي — يحتاج 2 سنوات كاملة من بنود القوائم'
            if available < 4
            else 'Screening'
    }


def altman(m, sec):

    assets = num(m.get('Assets'))

    A = (
        num(m.get('Working Capital')) / assets
        if pd.notna(num(m.get('Working Capital')))
        and pd.notna(assets)
        and assets
        else np.nan
    )

    B = (
        num(m.get('Retained Earnings')) / assets
        if pd.notna(num(m.get('Retained Earnings')))
        and pd.notna(assets)
        and assets
        else np.nan
    )

    C = (
        num(m.get('EBIT')) / assets
        if pd.notna(num(m.get('EBIT')))
        and pd.notna(assets)
        and assets
        else np.nan
    )

    D = (
        num(m.get('Market Cap')) /
        num(m.get('Debt'))
        if pd.notna(num(m.get('Market Cap')))
        and pd.notna(num(m.get('Debt')))
        and num(m.get('Debt')) > 0
        else np.nan
    )

    E = (
        num(m.get('Revenue')) / assets
        if pd.notna(num(m.get('Revenue')))
        and pd.notna(assets)
        and assets
        else np.nan
    )

    if any(
        pd.isna(x)
        for x in [A, B, C, D, E]
    ):
        return {
            'score': np.nan,
            'status': 'بيانات غير كافية'
        }

    z = (
        1.2 * A +
        1.4 * B +
        3.3 * C +
        0.6 * D +
        1.0 * E
    )

    return {
        'score': z,
        'status':
            'منطقة خطر مرتفعة'
            if z < 1.8
            else 'منطقة مراقبة'
            if z < 3
            else 'منطقة سليمة'
    }


def earnings_quality(m):

    ocf = num(
        m.get('Operating Cash Flow')
    )

    ni = num(
        m.get('Net Income')
    )

    fcf = num(
        m.get('FCF')
    )

    roe = num(
        m.get('ROE')
    )

    accrual = (
        (ocf - ni) / abs(ni)
        if pd.notna(ocf)
        and pd.notna(ni)
        and ni
        else np.nan
    )

    score = 50

    if pd.notna(accrual):
        score += np.clip(
            -accrual * 25,
            -25,
            25
        )

    if pd.notna(fcf) and pd.notna(ni):
        score += 15 if fcf > ni else -15

    if pd.notna(roe):
        score += np.clip(
            roe - 10,
            -20,
            20
        )

    return float(
        np.clip(score, 0, 100)
    ), accrual


def roic_quality(m):

    roic = num(m.get('ROIC'))
    fcfm = num(m.get('FCF Margin'))
    growthv = num(m.get('Revenue Growth'))

    values = [

        np.clip(roic * 2.5, 0, 100)
        if pd.notna(roic)
        else np.nan,

        np.clip(fcfm * 2, 0, 100)
        if pd.notna(fcfm)
        else np.nan,

        np.clip(50 + growthv, 0, 100)
        if pd.notna(growthv)
        else np.nan
    ]

    score = np.nanmean(values)

    return (
        float(score)
        if np.isfinite(score)
        else np.nan
    )


# ============================================================
# DIVIDENDS
# ============================================================

def dividend_engine(t, price):

    try:

        s = pd.to_numeric(
            t.dividends,
            errors='coerce'
        ).dropna()

        s = s[s > 0]

        if s.empty:

            return {
                'yield': np.nan,
                'last': np.nan,
                'count3y': 0,
                'sustainability': np.nan
            }

        now = (
            pd.Timestamp.now(tz=s.index.tz)
            if getattr(s.index, 'tz', None)
            else pd.Timestamp.now()
        )

        d12 = s[
            s.index >= now - pd.Timedelta(days=365)
        ]

        d3 = s[
            s.index >= now - pd.Timedelta(days=1095)
        ]

        total = float(d12.sum())

        y = (
            total / price * 100
            if price
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
            'yield': y,
            'last': float(s.iloc[-1]),
            'date': s.index[-1].strftime('%Y-%m-%d'),
            'count3y': len(d3),
            'sustainability': sustainability
        }

    except Exception:

        return {
            'yield': np.nan,
            'last': np.nan,
            'count3y': 0,
            'sustainability': np.nan
        }


# ============================================================
# TRUE FCFF DCF
# ============================================================

def fcff_dcf_scenario(
    m,
    years=5,
    wacc=0.14,
    tg=0.04,
    growth_override=None,
    name='Base'
):
    """
    True FCFF framework:

    FCFF =
        NOPAT
        + D&A
        - Capex
        - Delta NWC

    Then:
        Enterprise Value =
            PV(FCFF) + PV(Terminal Value)

    Equity Value =
        Enterprise Value
        - Debt
        + Cash

    Per share =
        Equity Value / Shares
    """

    fcff = num(m.get('FCFF'))
    shares = num(m.get('Shares'))
    debt = num(m.get('Debt'))
    cash = num(m.get('Cash'))

    if (
        pd.isna(fcff)
        or fcff <= 0
        or pd.isna(shares)
        or shares <= 0
    ):

        return {
            'value': np.nan,
            'enterprise': np.nan,
            'equity': np.nan,
            'status': 'True FCFF غير متاح',
            'scenario': name
        }

    # --------------------------------------------------------
    # Growth assumptions
    # --------------------------------------------------------

    revenue_growth = num(
        m.get('Revenue Growth')
    )

    fcf_growth = num(
        m.get('FCF Growth')
    )

    # Use independent FCF growth as primary signal.
    if growth_override is not None:

        g0 = growth_override

    elif pd.notna(fcf_growth):

        g0 = fcf_growth / 100

    elif pd.notna(revenue_growth):

        g0 = revenue_growth / 100

    else:

        g0 = 0.06

    # Conservative limits.
    g0 = np.clip(
        g0,
        -0.05,
        0.20
    )

    # Growth fades toward terminal growth.
    growths = []

    for i in range(years):

        fade = i / max(years - 1, 1)

        g = (
            g0 * (1 - fade * .65)
            + tg * (fade * .65)
        )

        g = max(
            g,
            tg
        )

        growths.append(g)

    # --------------------------------------------------------
    # Forecast
    # --------------------------------------------------------

    pv = 0.0
    current_fcff = fcff

    for year, gr in enumerate(
        growths,
        start=1
    ):

        current_fcff *= (
            1 + gr
        )

        pv += (
            current_fcff /
            ((1 + wacc) ** year)
        )

    # Terminal value
    denominator = wacc - tg

    if denominator <= 0:
        return {
            'value': np.nan,
            'enterprise': np.nan,
            'equity': np.nan,
            'status': 'WACC يجب أن يكون أكبر من Terminal Growth',
            'scenario': name
        }

    terminal = (
        current_fcff *
        (1 + tg) /
        denominator
    )

    terminal_pv = (
        terminal /
        ((1 + wacc) ** years)
    )

    enterprise = (
        pv +
        terminal_pv
    )

    equity = (
        enterprise -
        (debt if pd.notna(debt) else 0)
        +
        (cash if pd.notna(cash) else 0)
    )

    value = (
        equity / shares
    )

    return {
        'value': value,
        'enterprise': enterprise,
        'equity': equity,
        'status': 'True FCFF DCF',
        'scenario': name,
        'wacc': wacc,
        'terminal_growth': tg,
        'initial_growth': g0,
        'fcff': fcff
    }


# ============================================================
# 3 SCENARIO VALUATION
# ============================================================

def dcf_three_scenarios(m):

    # --------------------------------------------------------
    # Conservative
    # --------------------------------------------------------

    conservative = fcff_dcf_scenario(
        m,
        years=5,
        wacc=.15,
        tg=.03,
        name='Conservative'
    )

    # --------------------------------------------------------
    # Base
    # --------------------------------------------------------

    base = fcff_dcf_scenario(
        m,
        years=5,
        wacc=.13,
        tg=.04,
        name='Base'
    )

    # --------------------------------------------------------
    # Optimistic
    # --------------------------------------------------------

    optimistic = fcff_dcf_scenario(
        m,
        years=5,
        wacc=.12,
        tg=.045,
        name='Optimistic'
    )

    values = [
        conservative.get('value'),
        base.get('value'),
        optimistic.get('value')
    ]

    valid = [
        x for x in values
        if pd.notna(x) and x > 0
    ]

    # Base is the main fair-value anchor.
    fair_dcf = (
        base.get('value')
        if pd.notna(base.get('value'))
        and base.get('value') > 0
        else (
            float(np.nanmedian(valid))
            if valid
            else np.nan
        )
    )

    return {
        'Conservative DCF':
            conservative.get('value'),

        'Base DCF':
            base.get('value'),

        'Optimistic DCF':
            optimistic.get('value'),

        'DCF Fair Value':
            fair_dcf,

        'Conservative Detail':
            conservative,

        'Base Detail':
            base,

        'Optimistic Detail':
            optimistic
    }


# ============================================================
# RELATIVE VALUATION
# ============================================================

def relative_valuation(m, sector):

    pe = num(m.get('P/E'))
    pb = num(m.get('P/B'))

    price = num(m.get('Price'))
    eps = num(m.get('EPS'))
    bv = num(m.get('BVPS'))

    pe_ref = {
        'Banks': 10,
        'Financial Services': 11,
        'Real Estate': 12,
        'Healthcare': 15,
        'Telecom & Technology': 14,
        'Energy & Petrochemicals': 9,
        'Consumer': 13,
        'Construction & Engineering': 11,
        'Industrial & Materials': 11
    }.get(
        sector,
        12
    )

    pb_ref = (
        1.4
        if sector == 'Banks'
        else 1.5
    )

    vals = []

    pe_value = np.nan
    pb_value = np.nan

    if (
        pd.notna(eps)
        and eps > 0
    ):

        pe_value = eps * pe_ref
        vals.append(pe_value)

    if (
        pd.notna(bv)
        and bv > 0
    ):

        pb_value = bv * pb_ref
        vals.append(pb_value)

    return {
        'value':
            float(np.nanmedian(vals))
            if vals
            else np.nan,

        'PE Fair Value':
            pe_value,

        'PB Fair Value':
            pb_value,

        'pe_ref':
            pe_ref,

        'pb_ref':
            pb_ref,

        'methods':
            len(vals)
    }


# ============================================================
# NORMALIZED EARNINGS VALUE
# ============================================================

def normalized_earnings_value(m, sector):

    eps = num(
        m.get('EPS')
    )

    if pd.isna(eps) or eps <= 0:
        return np.nan

    pe_ref = {
        'Banks': 10,
        'Financial Services': 11,
        'Real Estate': 12,
        'Healthcare': 15,
        'Telecom & Technology': 14,
        'Energy & Petrochemicals': 9,
        'Consumer': 13,
        'Construction & Engineering': 11,
        'Industrial & Materials': 11
    }.get(
        sector,
        12
    )

    return eps * pe_ref


# ============================================================
# COMPLETE VALUATION ENGINE
# ============================================================

def valuation_engine(m, sector):

    price = num(
        m.get('Price')
    )

    dcf = dcf_three_scenarios(m)

    relative = relative_valuation(
        m,
        sector
    )

    normalized = normalized_earnings_value(
        m,
        sector
    )

    base_dcf = num(
        dcf.get('Base DCF')
    )

    relative_value = num(
        relative.get('value')
    )

    # --------------------------------------------------------
    # Fair Value
    #
    # Base DCF is the primary intrinsic anchor.
    # Relative value is a secondary confirmation.
    #
    # This avoids the old problem where median of two values
    # became a simple average and pulled fair value arbitrarily.
    # --------------------------------------------------------

    if (
        pd.notna(base_dcf)
        and base_dcf > 0
        and pd.notna(relative_value)
        and relative_value > 0
    ):

        fair = (
            base_dcf * .70 +
            relative_value * .30
        )

    elif (
        pd.notna(base_dcf)
        and base_dcf > 0
    ):

        fair = base_dcf

    elif (
        pd.notna(relative_value)
        and relative_value > 0
    ):

        fair = relative_value

    elif (
        pd.notna(normalized)
        and normalized > 0
    ):

        fair = normalized

    else:

        fair = np.nan

    conservative = num(
        dcf.get('Conservative DCF')
    )

    optimistic = num(
        dcf.get('Optimistic DCF')
    )

    # --------------------------------------------------------
    # Safety margins
    # --------------------------------------------------------

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

    return {

        'DCF/FCFF':
            base_dcf,

        'Conservative DCF':
            conservative,

        'Base DCF':
            base_dcf,

        'Optimistic DCF':
            optimistic,

        'Relative':
            relative_value,

        'Normalized Earnings':
            normalized,

        'Fair Value':
            fair,

        'Buy 20% MOS':
            buy20,

        'Strong Buy 30% MOS':
            buy30,

        'Upside %':
            upside,

        'DCF Low':
            conservative,

        'DCF High':
            optimistic,

        'PE Fair Value':
            relative.get('PE Fair Value'),

        'PB Fair Value':
            relative.get('PB Fair Value'),

        'PE Reference':
            relative.get('pe_ref'),

        'PB Reference':
            relative.get('pb_ref')
    }


# ============================================================
# TECHNICAL
# ============================================================

def technical(df):

    if (
        df is None
        or df.empty
        or 'Close' not in df
        or len(df) < 220
    ):
        return {}

    d = df.copy()

    close = pd.to_numeric(
        d['Close'],
        errors='coerce'
    ).dropna()

    high = pd.to_numeric(
        d['High'],
        errors='coerce'
    ).reindex(close.index)

    low = pd.to_numeric(
        d['Low'],
        errors='coerce'
    ).reindex(close.index)

    vol = pd.to_numeric(
        d['Volume'],
        errors='coerce'
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

    gain = delta.clip(
        lower=0
    ).ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    loss = (
        -delta.clip(lower=None, upper=0)
    ).ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    rsi = (
        100 -
        100 /
        (
            1 +
            gain /
            loss.replace(
                0,
                np.nan
            )
        )
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

    sig = macd.ewm(
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

    vol_mean = (
        vol.rolling(20).mean().iloc[-1]
    )

    vr = (
        vol.iloc[-1] / vol_mean
        if pd.notna(vol_mean)
        and vol_mean
        else np.nan
    )

    c = float(close.iloc[-1])

    e20 = float(ema20.iloc[-1])
    e50 = float(ema50.iloc[-1])
    e200 = float(ema200.iloc[-1])

    flags = [
        c > e20,
        c > e50,
        c > e200,
        rsi.iloc[-1] > 50,
        macd.iloc[-1] > sig.iloc[-1],
        vr >= 1 if pd.notna(vr) else False
    ]

    score = (
        sum(flags) /
        6 *
        100
    )

    support = float(
        close.tail(20).min()
    )

    resistance = float(
        close.tail(20).max()
    )

    stop = max(
        support,
        c -
        (
            atr.iloc[-1] * 2
            if pd.notna(atr.iloc[-1])
            else c * .08
        )
    )

    target = max(
        resistance,
        c * 1.05
    )

    return {

        'score': score,
        'price': c,

        'rsi':
            float(rsi.iloc[-1]),

        'macd':
            float(macd.iloc[-1]),

        'signal':
            float(sig.iloc[-1]),

        'atr_pct':
            float(
                atr.iloc[-1] /
                c *
                100
            )
            if pd.notna(atr.iloc[-1])
            else np.nan,

        'volume_ratio':
            float(vr)
            if pd.notna(vr)
            else np.nan,

        'ema20': e20,
        'ema50': e50,
        'ema200': e200,

        'support': support,
        'resistance': resistance,

        'stop': stop,
        'target1': target,

        'last_date':
            close.index[-1].strftime(
                '%Y-%m-%d'
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
            'trades': 0,
            'status': 'بيانات غير كافية'
        }

    close = pd.to_numeric(
        df['Close'],
        errors='coerce'
    ).dropna()

    ema = close.ewm(
        span=20,
        adjust=False
    ).mean()

    delta = close.diff()

    gain = delta.clip(
        lower=0
    ).ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    loss = (
        -delta.clip(lower=None, upper=0)
    ).ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    rsi = (
        100 -
        100 /
        (
            1 +
            gain /
            loss.replace(
                0,
                np.nan
            )
        )
    )

    returns = []

    in_pos = False
    entry = 0

    for i in range(
        220,
        len(close)
    ):

        c = close.iloc[i]

        if (
            not in_pos
            and c > ema.iloc[i]
            and rsi.iloc[i] > 52
        ):

            entry = (
                float(c) *
                (
                    1 +
                    slippage +
                    commission
                )
            )

            in_pos = True

        elif (
            in_pos
            and (
                c < ema.iloc[i]
                or rsi.iloc[i] < 48
            )
        ):

            exitp = (
                float(c) *
                (
                    1 -
                    slippage -
                    commission
                )
            )

            returns.append(
                exitp / entry - 1
            )

            in_pos = False

    if in_pos:

        returns.append(
            float(close.iloc[-1]) /
            entry -
            1
        )

    r = np.array(
        returns,
        dtype=float
    )

    trades = len(r)

    if not trades:

        return {
            'trades': 0,
            'status': 'لا توجد صفقات'
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
        (r > 0).mean() *
        100
    )

    profit = (
        curve[-1] - 1
    ) * 100

    if (r < 0).any():

        pf = (
            r[r > 0].sum() /
            abs(r[r < 0].sum())
        )

    else:

        pf = np.inf

    exp = (
        r.mean() *
        100
    )

    sharpe = (
        r.mean() /
        r.std() *
        np.sqrt(trades)
        if r.std() > 0
        else np.nan
    )

    # --------------------------------------------------------
    # Monte Carlo
    # --------------------------------------------------------

    mc_runs = max(
        int(mc_runs),
        10
    )

    rng = np.random.default_rng(
        42
    )

    terminals = []
    dds = []

    for _ in range(mc_runs):

        sample = rng.choice(
            r,
            size=trades,
            replace=True
        )

        c = np.cumprod(
            1 + sample
        )

        p = np.maximum.accumulate(
            c
        )

        terminals.append(
            (c[-1] - 1) * 100
        )

        dds.append(
            np.max(
                (p - c) / p
            ) * 100
        )

    terminals = np.array(
        terminals
    )

    dds = np.array(
        dds
    )

    return {

        'trades':
            trades,

        'win_rate':
            float(win),

        'return':
            float(profit),

        'max_dd':
            float(dd.max()),

        'pf':
            float(pf),

        'expectancy':
            float(exp),

        'sharpe':
            float(sharpe),

        'mc5':
            float(
                np.percentile(
                    terminals,
                    5
                )
            ),

        'mc50':
            float(
                np.percentile(
                    terminals,
                    50
                )
            ),

        'mc95':
            float(
                np.percentile(
                    terminals,
                    95
                )
            ),

        'mc_profit_prob':
            float(
                np.mean(
                    terminals > 0
                ) * 100
            ),

        'mc_dd95':
            float(
                np.percentile(
                    dds,
                    95
                )
            ),

        'status':
            'تم'
    }


# ============================================================
# WFO
# ============================================================

def wfo_score(df):

    if (
        df is None
        or len(df) < 600
    ):

        return {
            'score': np.nan,
            'oos_return': np.nan,
            'stability': np.nan,
            'folds': 0
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
            mc_runs=100
        )

        if bt.get(
            'trades',
            0
        ) >= 3:

            scores.append(
                np.clip(
                    50 +
                    bt['return'],
                    0,
                    100
                )
            )

            returns.append(
                bt['return']
            )

    return {

        'score':
            float(
                np.mean(scores)
            )
            if scores
            else np.nan,

        'oos_return':
            float(
                np.mean(returns)
            )
            if returns
            else np.nan,

        'stability':
            float(
                100 -
                np.std(returns) * 2
            )
            if len(returns) > 1
            else (
                50
                if returns
                else np.nan
            ),

        'folds':
            len(scores)
    }


# ============================================================
# INSTITUTIONAL SCORE
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

    fscore = []

    rules = SECTOR_RULES[
        fin['sector']
    ]

    w = WEIGHTS[
        fin['sector']
    ]

    for k in rules:

        x = num(
            fin['metrics'].get(k)
        )

        if pd.isna(x):
            continue

        if k in [
            'Revenue Growth',
            'Net Income Growth',
            'EPS Growth',
            'FCF Growth'
        ]:

            s = np.clip(
                50 + x * 1.5,
                0,
                100
            )

        elif k in [
            'ROE',
            'ROIC'
        ]:

            s = np.clip(
                x * 3,
                0,
                100
            )

        elif k == 'ROA':

            s = np.clip(
                x * 15,
                0,
                100
            )

        elif k in [
            'Gross Margin',
            'EBITDA Margin',
            'Net Margin',
            'FCF Margin'
        ]:

            s = np.clip(
                x * 2,
                0,
                100
            )

        elif k == 'Debt/Equity':

            s = np.clip(
                100 -
                max(x, 0) * 40,
                0,
                100
            )

        elif k == 'Net Debt/EBITDA':

            s = np.clip(
                100 -
                max(x, 0) * 18,
                0,
                100
            )

        elif k == 'Current Ratio':

            s = np.clip(
                x * 50,
                0,
                100
            )

        elif k == 'Dividend Yield':

            s = np.clip(
                x * 12,
                0,
                100
            )

        elif k == 'P/E':

            s = (
                np.clip(
                    100 -
                    abs(x - 12) * 4,
                    0,
                    100
                )
                if x > 0
                else np.nan
            )

        elif k == 'P/B':

            s = (
                np.clip(
                    100 -
                    abs(x - 1.4) * 35,
                    0,
                    100
                )
                if x > 0
                else np.nan
            )

        else:

            s = 50

        if np.isfinite(s):

            fscore.append(
                (s, w[k])
            )

    financial = (
        sum(
            s * ww
            for s, ww in fscore
        )
        /
        sum(
            ww
            for _, ww in fscore
        )
        if fscore
        else np.nan
    )

    quality = np.nanmean([
        forensic['piotroski'] *
        100 / 9,

        forensic['earnings_quality'],

        forensic['roic_quality']
    ])

    valuation = (
        50 +
        np.clip(
            num(
                val.get('Upside %')
            ),
            -50,
            100
        ) *
        .35
        if pd.notna(
            num(val.get('Upside %'))
        )
        else 50
    )

    technical = num(
        tech.get('score')
    )

    evidence = []

    if bt.get(
        'trades',
        0
    ) >= 5:

        evidence.append(
            np.clip(
                50 +
                bt.get(
                    'expectancy',
                    0
                ) * 5,
                0,
                100
            )
        )

    if pd.notna(
        wfo.get('score')
    ):

        evidence.append(
            wfo['score']
        )

    if bt.get(
        'trades',
        0
    ) >= 5:

        evidence.append(
            bt.get(
                'mc_profit_prob',
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

    stability = np.nanmean([
        wfo.get(
            'stability',
            np.nan
        ),

        np.clip(
            100 -
            bt.get(
                'max_dd',
                50
            ) * 2,
            0,
            100
        )
        if bt.get(
            'trades',
            0
        )
        else np.nan
    ])

    parts = [

        (financial, .30),
        (quality, .15),
        (valuation, .15),
        (technical, .15),
        (evidence_score, .15),
        (stability, .10)
    ]

    avail = [
        (v, w)
        for v, w in parts
        if pd.notna(v)
    ]

    final = (
        sum(
            v * w
            for v, w in avail
        )
        /
        sum(
            w
            for _, w in avail
        )
        if avail
        else np.nan
    )

    return {

        'financial':
            financial,

        'forensic':
            quality,

        'valuation':
            valuation,

        'technical':
            technical,

        'evidence':
            evidence_score,

        'stability':
            stability,

        'final':
            final
    }


# ============================================================
# SINGLE STOCK ANALYSIS
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
            'symbol': sym,
            'error': ds.error
        }

    raw = ds.data

    (
        m,
        inc,
        bal,
        cf,
        info,
        last_price_date
    ) = normalize_financials(
        raw
    )

    sec = sector(
        sym,
        info
    )

    pi, tests = piotroski(
        m,
        inc,
        bal,
        cf
    )

    bene = beneish(m)

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
        raw['ticker'],
        m.get('Price')
    )

    m['Dividend Yield'] = div.get(
        'yield'
    )

    fin = {
        'sector': sec,
        'metrics': m
    }

    val = valuation_engine(
        m,
        sec
    )

    try:

        hist = raw['ticker'].history(
            period='5y',
            interval='1d',
            auto_adjust=False
        )

    except Exception:

        hist = pd.DataFrame()

    tech = technical(
        hist
    )

    if run_bt:

        bt = backtest(
            hist,
            mc_runs=mc_runs
        )

        wfo = wfo_score(
            hist
        )

    else:

        bt = {
            'trades': 0
        }

        wfo = {
            'score': np.nan,
            'oos_return': np.nan,
            'stability': np.nan,
            'folds': 0
        }

    forensic = {

        'piotroski':
            pi,

        'beneish':
            bene,

        'altman':
            alt,

        'earnings_quality':
            eq,

        'roic_quality':
            rq
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

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    coverage_values = []

    for k, v in m.items():

        if k.startswith('_'):
            continue

        coverage_values.append(
            pd.notna(v)
        )

    coverage = (
        np.mean(
            coverage_values
        ) * 100
        if coverage_values
        else 0
    )

    # Technical last candle takes priority.
    actual_last_date = (
        tech.get(
            'last_date',
            last_price_date
        )
        if tech
        else last_price_date
    )

    return {

        'symbol':
            sym,

        'name':
            info.get(
                'longName',
                sym
            ),

        'sector':
            sec,

        'industry':
            info.get(
                'industry',
                ''
            ),

        'metrics':
            m,

        'valuation':
            val,

        'dividend':
            div,

        'technical':
            tech,

        'backtest':
            bt,

        'wfo':
            wfo,

        'forensic':
            forensic,

        'scores':
            scores,

        'coverage':
            coverage,

        'source':
            'Yahoo Finance',

        'last_date':
            actual_last_date
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

    out = []

    with ThreadPoolExecutor(
        max_workers=8
    ) as ex:

        futures = {
            ex.submit(
                analyze_one,
                s,
                run_bt,
                mc_runs
            ): s
            for s in symbols
        }

        for f in as_completed(
            futures
        ):

            try:

                out.append(
                    f.result()
                )

            except Exception as e:

                out.append({
                    'symbol':
                        futures[f],
                    'error':
                        str(e)
                })

    return out


# ============================================================
# UI
# ============================================================

st.title(
    '🏛️ EGX Institutional Analyzer V5'
)

st.caption(
    'Financial Intelligence + TTM + True FCFF + '
    '3-Scenario DCF + Relative Valuation + '
    'Forensic Quality + V9 Technical Evidence + '
    'Backtest/WFO/OOS + Monte Carlo + Stability'
)

with st.sidebar:

    st.header(
        '⚙️ إعدادات المؤسسة'
    )

    min_cov = st.slider(
        'أقل اكتمال بيانات %',
        0,
        100,
        55,
        5
    )

    top_n = st.number_input(
        'عدد الأسهم في الترتيب',
        5,
        100,
        20
    )

    run_bt = st.checkbox(
        'تشغيل Backtest + WFO/OOS + Monte Carlo',
        True
    )

    mc_runs = st.selectbox(
        'Monte Carlo',
        [100, 250, 500, 1000],
        index=2
    )

    if st.button(
        '🔄 تحديث كامل'
    ):

        analyze_one.clear()
        run_all.clear()

        st.rerun()


# ============================================================
# RUN
# ============================================================

with st.spinner(
    '🏗️ بناء التحليل المؤسسي...'
):

    results = run_all(
        tuple(STOCKS),
        run_bt,
        mc_runs
    )


# ============================================================
# RANKING TABLE
# ============================================================

rows = []

for r in results:

    if (
        r.get('error')
        or r.get(
            'coverage',
            0
        ) < min_cov
    ):
        continue

    s = r['scores']
    v = r['valuation']
    t = r['technical']
    b = r['backtest']
    w = r['wfo']
    f = r['forensic']
    d = r['dividend']

    rows.append({

        'الترتيب':
            0,

        'السهم':
            r['symbol'].replace(
                '.CA',
                ''
            ),

        'القطاع':
            r['sector'],

        'الدرجة النهائية':
            s.get('final'),

        'المالي':
            s.get('financial'),

        'الجودة المحاسبية':
            s.get('forensic'),

        'التقييم':
            s.get('valuation'),

        'الفني V9':
            s.get('technical'),

        'الدليل الإحصائي':
            s.get('evidence'),

        'الاستقرار':
            s.get('stability'),

        'القيمة العادلة':
            v.get('Fair Value'),

        'DCF محافظ':
            v.get('Conservative DCF'),

        'DCF أساسي':
            v.get('Base DCF'),

        'DCF متفائل':
            v.get('Optimistic DCF'),

        'شراء 20% MOS':
            v.get('Buy 20% MOS'),

        'شراء قوي 30% MOS':
            v.get('Strong Buy 30% MOS'),

        'الصعود %':
            v.get('Upside %'),

        'Piotroski':
            f['piotroski'],

        'Beneish Flags':
            f['beneish']['risk_flags'],

        'Altman Z':
            f['altman']['score'],

        'جودة الأرباح':
            f['earnings_quality'],

        'ROIC Quality':
            f['roic_quality'],

        'Dividend Yield %':
            d.get('yield'),

        'صفقات Backtest':
            b.get('trades', 0),

        'Win Rate %':
            b.get(
                'win_rate',
                np.nan
            ),

        'Return %':
            b.get(
                'return',
                np.nan
            ),

        'Max DD %':
            b.get(
                'max_dd',
                np.nan
            ),

        'Profit Factor':
            b.get(
                'pf',
                np.nan
            ),

        'Expectancy %':
            b.get(
                'expectancy',
                np.nan
            ),

        'Sharpe':
            b.get(
                'sharpe',
                np.nan
            ),

        'WFO Score':
            w.get(
                'score',
                np.nan
            ),

        'OOS Return %':
            w.get(
                'oos_return',
                np.nan
            ),

        'MC Median %':
            b.get(
                'mc50',
                np.nan
            ),

        'MC Profit Prob %':
            b.get(
                'mc_profit_prob',
                np.nan
            ),

        'اكتمال البيانات %':
            r['coverage'],

        'آخر شمعة':
            r['last_date']
    })


df = pd.DataFrame(
    rows
)

if not df.empty:

    df = df.sort_values(
        'الدرجة النهائية',
        ascending=False,
        na_position='last'
    ).reset_index(
        drop=True
    )

    df['الترتيب'] = np.arange(
        1,
        len(df) + 1
    )


# ============================================================
# FINAL RANKING
# ============================================================

st.subheader(
    '🏆 الترتيب المؤسسي النهائي'
)

if df.empty:

    st.warning(
        'لا توجد نتائج مؤهلة وفق حد اكتمال البيانات.'
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
        '⬇️ تنزيل التقرير CSV',

        df.to_csv(
            index=False,
            encoding='utf-8-sig'
        ).encode(
            'utf-8-sig'
        ),

        'EGX_Institutional_V5.csv',

        'text/csv'
    )


# ============================================================
# FULL STOCK REPORT
# ============================================================

st.subheader(
    '🔎 تقرير مؤسسي كامل لسهم'
)

if results:

    valid = [
        r
        for r in results
        if not r.get('error')
    ]

    if valid:

        sel = st.selectbox(
            'اختر السهم',
            sorted(
                [
                    r['symbol']
                    for r in valid
                ]
            ),
            format_func=lambda x:
                x.replace(
                    '.CA',
                    ''
                )
        )

        r = next(
            x
            for x in valid
            if x['symbol'] == sel
        )

        s = r['scores']
        f = r['forensic']
        v = r['valuation']
        t = r['technical']
        b = r['backtest']
        w = r['wfo']
        d = r['dividend']

        cols = st.columns(
            7
        )

        labels = [
            'Final Investment Score',
            'Financial',
            'Forensic',
            'Valuation',
            'Technical V9',
            'Evidence',
            'Stability'
        ]

        values = [
            s['final'],
            s['financial'],
            s['forensic'],
            s['valuation'],
            s['technical'],
            s['evidence'],
            s['stability']
        ]

        for c, label, val in zip(
            cols,
            labels,
            values
        ):

            c.metric(
                label,
                '—'
                if pd.isna(val)
                else f'{val:.1f}'
            )

        st.write(
            f"**{r['name']}** | "
            f"القطاع: **{r['sector']}** | "
            f"آخر شمعة: **{r['last_date']}** | "
            f"المصدر الأساسي: **{r['source']}** | "
            f"اكتمال البيانات: **{r['coverage']:.0f}%**"
        )

        # ----------------------------------------------------
        # VALUATION
        # ----------------------------------------------------

        st.markdown(
            '### 💰 True FCFF + 3-Scenario DCF + Relative Valuation'
        )

        valuation_rows = [

            {
                'النموذج':
                    'DCF محافظ',
                'القيمة':
                    v.get(
                        'Conservative DCF'
                    )
            },

            {
                'النموذج':
                    'DCF أساسي',
                'القيمة':
                    v.get(
                        'Base DCF'
                    )
            },

            {
                'النموذج':
                    'DCF متفائل',
                'القيمة':
                    v.get(
                        'Optimistic DCF'
                    )
            },

            {
                'النموذج':
                    'Sector Relative',
                'القيمة':
                    v.get(
                        'Relative'
                    )
            },

            {
                'النموذج':
                    'Normalized Earnings',
                'القيمة':
                    v.get(
                        'Normalized Earnings'
                    )
            },

            {
                'النموذج':
                    'القيمة العادلة المدمجة',
                'القيمة':
                    v.get(
                        'Fair Value'
                    )
            },

            {
                'النموذج':
                    'شراء بهامش أمان 20%',
                'القيمة':
                    v.get(
                        'Buy 20% MOS'
                    )
            },

            {
                'النموذج':
                    'شراء قوي بهامش أمان 30%',
                'القيمة':
                    v.get(
                        'Strong Buy 30% MOS'
                    )
            },

            {
                'النموذج':
                    'الصعود المحتمل %',
                'القيمة':
                    v.get(
                        'Upside %'
                    )
            }
        ]

        valuation_df = pd.DataFrame(
            valuation_rows
        )

        st.dataframe(
            valuation_df.style.format(
                {
                    'القيمة':
                        '{:.2f}'
                },
                na_rep='—'
            ),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DCF ASSUMPTIONS
        # ----------------------------------------------------

        st.markdown(
            '#### ⚙️ مدخلات FCFF المستخدمة'
        )

        m = r['metrics']

        fcff_inputs = pd.DataFrame([
            {
                'المؤشر':
                    'Revenue TTM',
                'القيمة':
                    m.get('Revenue')
            },

            {
                'المؤشر':
                    'Revenue Growth TTM %',
                'القيمة':
                    m.get('Revenue Growth')
            },

            {
                'المؤشر':
                    'FCF TTM',
                'القيمة':
                    m.get('FCF')
            },

            {
                'المؤشر':
                    'FCF Growth TTM %',
                'القيمة':
                    m.get('FCF Growth')
            },

            {
                'المؤشر':
                    'EBIT TTM',
                'القيمة':
                    m.get('EBIT')
            },

            {
                'المؤشر':
                    'D&A TTM',
                'القيمة':
                    m.get('D&A')
            },

            {
                'المؤشر':
                    'NOPAT',
                'القيمة':
                    m.get('NOPAT')
            },

            {
                'المؤشر':
                    'Capex',
                'القيمة':
                    m.get('Capex')
            },

            {
                'المؤشر':
                    'Delta NWC',
                'القيمة':
                    m.get('Delta NWC')
            },

            {
                'المؤشر':
                    'True FCFF',
                'القيمة':
                    m.get('FCFF')
            },

            {
                'المؤشر':
                    'Tax Rate %',
                'القيمة':
                    m.get('Tax Rate')
            },

            {
                'المؤشر':
                    'Shares Outstanding',
                'القيمة':
                    m.get('Shares')
            },

            {
                'المؤشر':
                    'BVPS',
                'القيمة':
                    m.get('BVPS')
            }
        ])

        st.dataframe(
            fcff_inputs.style.format(
                {
                    'القيمة':
                        '{:.2f}'
                },
                na_rep='—'
            ),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # FORENSIC
        # ----------------------------------------------------

        st.markdown(
            '### 🧪 Forensic Accounting'
        )

        forensic_df = pd.DataFrame([

            {
                'المحرك':
                    'Piotroski F-Score',
                'القيمة':
                    f['piotroski'],
                'المعنى':
                    'قوة مالية تشغيلية'
            },

            {
                'المحرك':
                    'Beneish M-Score',
                'القيمة':
                    f['beneish']['risk_flags'],
                'المعنى':
                    f['beneish']['status']
            },

            {
                'المحرك':
                    'Altman Z-Score',
                'القيمة':
                    f['altman']['score'],
                'المعنى':
                    f['altman']['status']
            },

            {
                'المحرك':
                    'Earnings Quality',
                'القيمة':
                    f['earnings_quality'],
                'المعنى':
                    'جودة الأرباح والتدفقات'
            },

            {
                'المحرك':
                    'ROIC Quality',
                'القيمة':
                    f['roic_quality'],
                'المعنى':
                    'كفاءة رأس المال'
            }

        ])

        st.dataframe(
            forensic_df.style.format(
                {
                    'القيمة':
                        '{:.2f}'
                },
                na_rep='—'
            ),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # TECHNICAL
        # ----------------------------------------------------

        st.markdown(
            '### 📈 V9 Technical + Backtest + WFO/OOS + Monte Carlo'
        )

        techdf = pd.DataFrame([
            {
                'المؤشر': k,
                'القيمة': val
            }
            for k, val in t.items()
        ])

        st.dataframe(
            techdf,
            use_container_width=True,
            hide_index=True
        )

        evdf = pd.DataFrame(
            [
                {
                    'المؤشر': k,
                    'القيمة': val
                }
                for k, val in b.items()
            ]
            +
            [
                {
                    'المؤشر': k,
                    'القيمة': val
                }
                for k, val in w.items()
            ]
        )

        st.dataframe(
            evdf,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DIVIDENDS
        # ----------------------------------------------------

        st.markdown(
            '### 💵 Dividend Sustainability'
        )

        st.dataframe(
            pd.DataFrame([d]),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # FINANCIAL NORMALIZED DATA
        # ----------------------------------------------------

        st.markdown(
            '### 📊 Financial TTM / Normalized Data'
        )

        fm = pd.DataFrame([
            {
                'المؤشر': k,
                'القيمة': val
            }
            for k, val in r['metrics'].items()
            if not k.startswith('_')
        ])

        st.dataframe(
            fm,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    'V5 Institutional: الأسعار اليومية تستخدم آخر Daily Close '
    'متاح من Yahoo/yfinance عند توفره، والبيانات المالية تستخدم '
    'TTM من آخر 4 أرباع عند توفرها. تقييم الشركات غير المالية '
    'يعتمد على True FCFF + 3 Scenario DCF + Relative Valuation. '
    'الشركات المالية/البنوك تحتاج نماذج Equity/Dividend أكثر '
    'تخصصًا من FCFF. النماذج أدوات تحليلية وليست ضمانًا للنتائج المستقبلية.'
)
