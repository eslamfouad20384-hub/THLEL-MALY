import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

# ============================================================
# EGX FINANCIAL ANALYZER V3
# محلل الأسهم المصرية — تحليل مالي + تقييم + فني
# ============================================================

st.set_page_config(
    page_title="EGX Financial Analyzer V3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# إعدادات عامة
# ============================================================

MAX_WORKERS = 8
HISTORY_PERIOD = "3y"

# ============================================================
# قائمة الأسهم
# ============================================================

EGX_STOCKS = [
    "COMI.CA", "MFPC.CA", "PHDC.CA", "ORAS.CA", "HDBK.CA",
    "EFIH.CA", "AMES.CA", "INEG.CA", "BTFH.CA", "BIOC.CA",
    "CLHO.CA", "MBSC.CA", "MTIE.CA", "EGTS.CA", "EGSA.CA",
    "MHOT.CA", "EGBE.CA", "IFAP.CA", "PRDC.CA", "MIPH.CA",
    "MPCI.CA", "MOIN.CA", "ISMQ.CA", "AXPH.CA", "PHTV.CA",
    "CPCI.CA", "NINH.CA", "SPIN.CA", "ENGC.CA", "CNFN.CA",
    "SVCE.CA", "KABO.CA", "OFH.CA", "GSSC.CA", "WCDF.CA",
    "MFSC.CA", "SAIB.CA", "ACGC.CA", "UEFM.CA", "KZPC.CA",
    "ADCI.CA", "INFI.CA", "ASCM.CA", "VALU.CA", "ZEOT.CA",
    "SMFR.CA", "ETRS.CA", "CIRA.CA", "QNBE.CA", "EDFM.CA",
    "MILS.CA", "GBCO.CA", "ACTF.CA", "SCTS.CA", "HRHO.CA",
    "TMGH.CA", "FWRY.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA",
    "HELI.CA", "EAST.CA", "EFID.CA", "JUFO.CA", "ABUK.CA",
    "ESRS.CA", "EMFD.CA", "CCAP.CA", "ACAP.CA", "CICH.CA",
    "OCDI.CA", "ORHD.CA", "MASR.CA", "AIHC.CA", "ADIB.CA",
    "SAUD.CA", "CIEB.CA", "FAIT.CA", "AFDI.CA", "CANA.CA",
    "EXPA.CA", "ARCC.CA", "AJWA.CA", "MICH.CA", "SUGR.CA",
    "POUL.CA", "DOMT.CA", "ISMA.CA", "UEGC.CA", "FERC.CA",
    "UBEE.CA", "FAITA.CA", "MNHD.CA", "SUCE.CA", "SMPP.CA",
    "ALEX.CA", "CRST.CA", "DCRC.CA", "DIFC.CA", "MAAL.CA",
    "GGRN.CA", "GGCC.CA", "IEEC.CA", "NDRL.CA", "EFIC.CA",
    "GPIM.CA", "RTVC.CA", "RUBX.CA", "PRMH.CA", "UNIP.CA",
    "TWSA.CA", "ICLE.CA", "MEGM.CA", "EASB.CA", "APSW.CA",
    "MOED.CA", "KWIN.CA", "KORA.CA", "RMDA.CA", "OIH.CA",
    "NAPR.CA", "BONY.CA", "SPHT.CA", "SDTI.CA", "GTWL.CA",
    "CFGH.CA", "NAHO.CA", "ACAMD.CA", "NARE.CA", "CEFM.CA",
    "ASPI.CA", "SCFM.CA", "CERA.CA", "DEIN.CA", "MBEG.CA",
    "SIPC.CA", "NHPS.CA", "ROTO.CA", "TYCN.CA", "RAKT.CA",
    "EEII.CA", "CCRS.CA", "AREH.CA", "EPCO.CA", "FCMD.CA",
    "GRCA.CA", "GIHD.CA", "ELWA.CA", "MMAT.CA", "NEDA.CA",
    "EPPK.CA", "GMCI.CA", "CPME.CA", "VLMR.CA", "GPPL.CA",
    "ADPC.CA", "ADRI.CA", "AIDC.CA", "OBRI.CA", "RREI.CA",
    "RKAZ.CA", "SEIG.CA", "SNFC.CA", "TANM.CA", "UPMS.CA",
    "UTOP.CA", "VERT.CA", "WKOL.CA", "LUTS.CA", "AIFI.CA",
    "AMIA.CA", "AMII.CA", "ACRO.CA", "DGTZ.CA", "DTPP.CA",
    "EALR.CA", "EBSC.CA", "EGREF.CA", "EHDR.CA", "ELNA.CA",
    "EOSB.CA", "FIRE.CA", "FNAR.CA", "FTNS.CA", "GOUR.CA",
    "ICID.CA", "IDRE.CA", "KASABF.CA", "KRDI.CA", "LCSW.CA",
    "MOSC.CA", "TAQA.CA", "OLFI.CA", "SKPC.CA", "AMER.CA",
    "TALM.CA", "ALUM.CA", "ORWE.CA", "SPMD.CA", "ZMID.CA",
    "MENA.CA", "DAPH.CA", "RAYA.CA", "EGAL.CA", "ECAP.CA",
    "MPRC.CA", "AFMC.CA", "NCCW.CA", "SCEM.CA", "ARAB.CA",
    "GDWA.CA", "ELEC.CA", "IRON.CA", "ATQA.CA", "EGCH.CA",
    "ALCN.CA", "MPCO.CA", "ELSH.CA", "MEPA.CA", "ODIN.CA",
    "EGAS.CA", "RACC.CA", "PRCL.CA", "BINV.CA", "EDBM.CA",
    "MCQE.CA", "MOIL.CA", "NIPH.CA", "ISPH.CA", "DSCW.CA",
    "AALR.CA", "UNIT.CA", "PHAR.CA", "TRTO.CA", "CAED.CA",
    "CSAG.CA", "ICFC.CA", "ELKA.CA", "PHGC.CA", "NCGC.CA",
    "MCRO.CA", "ATLC.CA", "COSG.CA", "AMPI.CA", "COPR.CA",
    "OCPH.CA"
]

# إزالة التكرارات
EGX_STOCKS = list(dict.fromkeys(EGX_STOCKS))

# ============================================================
# القطاعات
# ============================================================

BANKS = {
    "COMI", "HDBK", "EGBE", "SAIB", "QNBE",
    "CICH", "SAUD", "CIEB", "ADIB"
}

FINANCIAL = {
    "EFIH", "BTFH", "VALU", "OFH", "CNFN", "MCQE",
    "ADCI", "ACAP", "FAIT", "AFDI", "UBEE", "FAITA",
    "AIFI", "AMIA", "AMII", "ATLC", "BINV", "DIFC"
}

REAL_ESTATE = {
    "PHDC", "PRDC", "TMGH", "HELI", "EMFD", "CCAP",
    "OCDI", "ORHD", "MASR", "MNHD", "DCRC", "ARCC",
    "RMDA", "IDRE", "RREI", "EGREF", "EHDR", "MENA",
    "MPRC"
}

HEALTHCARE = {
    "BIOC", "CLHO", "MIPH", "NIPH", "ISPH",
    "PHAR", "SPMD", "DAPH", "PHTV", "OCPH"
}

TECH = {
    "ETEL", "MTIE", "RAYA", "EFIH", "UBEE",
    "DGTZ", "GOUR"
}

ENERGY = {
    "AMOC", "SKPC", "EGAS", "TAQA", "MOIL",
    "GPIM", "EGAL", "ELSH", "MEPA"
}

CONSUMER = {
    "DOMT", "EAST", "JUFO", "SUGR", "POUL",
    "OLFI", "AJWA", "MICH", "UEGC", "ISMA",
    "GOUR", "FERC"
}

CONSTRUCTION = {
    "ORAS", "ENGC", "SVCE", "ARAB", "ELNA",
    "UPMS", "UNIT", "NCCW", "RACC", "PRCL",
    "AIDC"
}

def sector_of(ticker):
    symbol = ticker.replace(".CA", "")
    
    if symbol in BANKS:
        return "البنوك"
    if symbol in FINANCIAL:
        return "الخدمات المالية"
    if symbol in REAL_ESTATE:
        return "العقارات"
    if symbol in HEALTHCARE:
        return "الرعاية الصحية"
    if symbol in TECH:
        return "الاتصالات والتكنولوجيا"
    if symbol in ENERGY:
        return "الطاقة والبتروكيماويات"
    if symbol in CONSUMER:
        return "الأغذية والسلع الاستهلاكية"
    if symbol in CONSTRUCTION:
        return "الإنشاءات والهندسة"
    
    return "الصناعة والمواد / أخرى"

# ============================================================
# أدوات حسابية
# ============================================================

def safe_float(x):
    try:
        if x is None:
            return np.nan
        
        if isinstance(x, str):
            x = (
                x.replace(",", "")
                 .replace("%", "")
                 .replace("—", "")
                 .replace("-", "")
                 .strip()
            )
        
        return float(x)
    except Exception:
        return np.nan


def clean_number(x):
    x = safe_float(x)
    
    if pd.isna(x):
        return np.nan
    
    return x


def latest_value(df, names):
    if df is None or df.empty:
        return np.nan
    
    for name in names:
        if name in df.index:
            row = df.loc[name]
            
            if isinstance(row, pd.Series):
                row = row.dropna()
                
                if len(row):
                    return safe_float(row.iloc[0])
    
    return np.nan


def previous_value(df, names):
    if df is None or df.empty:
        return np.nan
    
    for name in names:
        if name in df.index:
            row = df.loc[name]
            
            if isinstance(row, pd.Series):
                row = row.dropna()
                
                if len(row) >= 2:
                    return safe_float(row.iloc[1])
    
    return np.nan


def growth(current, previous):
    current = safe_float(current)
    previous = safe_float(previous)
    
    if pd.isna(current) or pd.isna(previous):
        return np.nan
    
    if previous == 0:
        return np.nan
    
    return (current / previous - 1) * 100


def ratio(a, b):
    a = safe_float(a)
    b = safe_float(b)
    
    if pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    
    return a / b


def fmt_money(x):
    if pd.isna(x):
        return "—"
    
    x = float(x)
    
    if abs(x) >= 1_000_000_000:
        return f"{x / 1_000_000_000:.2f} مليار"
    
    if abs(x) >= 1_000_000:
        return f"{x / 1_000_000:.2f} مليون"
    
    if abs(x) >= 1_000:
        return f"{x / 1_000:.2f} ألف"
    
    return f"{x:,.2f}"


def fmt_pct(x):
    if pd.isna(x):
        return "—"
    return f"{x:.1f}%"


def fmt_price(x):
    if pd.isna(x):
        return "—"
    return f"{x:.2f}"

# ============================================================
# التقييم المالي
# ============================================================

def score_growth(x):
    if pd.isna(x):
        return 50
    
    if x >= 40:
        return 100
    if x >= 25:
        return 90
    if x >= 15:
        return 80
    if x >= 8:
        return 70
    if x >= 0:
        return 60
    if x >= -10:
        return 40
    
    return 20


def score_margin(x):
    if pd.isna(x):
        return 50
    
    if x >= 30:
        return 100
    if x >= 20:
        return 90
    if x >= 15:
        return 80
    if x >= 10:
        return 70
    if x >= 5:
        return 60
    if x >= 0:
        return 45
    
    return 20


def score_roe(x):
    if pd.isna(x):
        return 50
    
    if x >= 30:
        return 100
    if x >= 20:
        return 90
    if x >= 15:
        return 80
    if x >= 10:
        return 70
    if x >= 5:
        return 55
    
    return 35


def score_debt(x):
    if pd.isna(x):
        return 50
    
    if x <= 0:
        return 100
    if x <= 0.25:
        return 95
    if x <= 0.50:
        return 85
    if x <= 1:
        return 70
    if x <= 2:
        return 50
    
    return 25


def score_pe(x):
    if pd.isna(x) or x <= 0:
        return 50
    
    if x <= 5:
        return 100
    if x <= 8:
        return 90
    if x <= 12:
        return 80
    if x <= 16:
        return 65
    if x <= 22:
        return 50
    
    return 30


def score_pb(x):
    if pd.isna(x) or x <= 0:
        return 50
    
    if x <= 1:
        return 100
    if x <= 1.5:
        return 90
    if x <= 2.5:
        return 75
    if x <= 4:
        return 60
    
    return 40


def score_dividend(x):
    if pd.isna(x):
        return 50
    
    if x >= 8:
        return 100
    if x >= 5:
        return 90
    if x >= 3:
        return 80
    if x >= 1:
        return 65
    if x > 0:
        return 55
    
    return 30

# ============================================================
# التحليل الفني
# ============================================================

def technical_analysis(ticker):
    try:
        df = yf.download(
            ticker,
            period=HISTORY_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )
        
        if df is None or df.empty:
            return {}
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        required = {"Close", "High", "Low", "Volume"}
        
        if not required.issubset(set(df.columns)):
            return {}
        
        df = df.dropna(subset=["Close"])
        
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]
        
        price = float(close.iloc[-1])
        
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
        ema200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
        
        sma20 = float(close.rolling(20).mean().iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1])
        
        delta = close.diff()
        
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        rsi_value = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else np.nan
        
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        macd_value = float(macd.iloc[-1])
        signal_value = float(signal.iloc[-1])
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        atr_value = float(atr.iloc[-1])
        
        avg_volume = float(volume.rolling(20).mean().iloc[-1])
        
        if avg_volume > 0:
            volume_ratio = float(volume.iloc[-1] / avg_volume)
        else:
            volume_ratio = np.nan
        
        high_52 = float(close.tail(252).max())
        low_52 = float(close.tail(252).min())
        
        support = float(close.tail(30).min())
        resistance = float(close.tail(30).max())
        
        score = 50
        
        if price > ema20:
            score += 8
        else:
            score -= 8
        
        if price > ema50:
            score += 8
        else:
            score -= 8
        
        if price > ema200:
            score += 10
        else:
            score -= 10
        
        if ema20 > ema50:
            score += 7
        else:
            score -= 7
        
        if ema50 > ema200:
            score += 7
        else:
            score -= 7
        
        if not pd.isna(rsi_value):
            if 50 <= rsi_value <= 70:
                score += 8
            elif rsi_value > 70:
                score += 3
            elif rsi_value < 30:
                score += 2
            else:
                score -= 3
        
        if macd_value > signal_value:
            score += 7
        else:
            score -= 7
        
        if not pd.isna(volume_ratio):
            if volume_ratio >= 1.5:
                score += 5
            elif volume_ratio >= 1:
                score += 2
        
        score = max(0, min(100, score))
        
        if score >= 75:
            trend = "صاعد قوي"
        elif score >= 60:
            trend = "صاعد"
        elif score >= 45:
            trend = "محايد"
        elif score >= 30:
            trend = "هابط"
        else:
            trend = "هابط قوي"
        
        return {
            "السعر الفني": price,
            "EMA20": ema20,
            "EMA50": ema50,
            "EMA200": ema200,
            "SMA20": sma20,
            "SMA50": sma50,
            "SMA200": sma200,
            "RSI": rsi_value,
            "MACD": macd_value,
            "إشارة MACD": signal_value,
            "ATR": atr_value,
            "نسبة الحجم": volume_ratio,
            "قمة 52 أسبوع": high_52,
            "قاع 52 أسبوع": low_52,
            "الدعم": support,
            "المقاومة": resistance,
            "الدرجة الفنية": score,
            "الاتجاه": trend,
            "تاريخ آخر شمعة": df.index[-1].strftime("%Y-%m-%d")
        }
        
    except Exception:
        return {}

# ============================================================
# التحليل المالي لسهم
# ============================================================

def analyze_stock(ticker):
    try:
        symbol = ticker.replace(".CA", "")
        sector = sector_of(ticker)
        
        stock = yf.Ticker(ticker)
        
        info = {}
        
        try:
            info = stock.info
        except Exception:
            info = {}
        
        try:
            financials = stock.financials
        except Exception:
            financials = pd.DataFrame()
        
        try:
            balance = stock.balance_sheet
        except Exception:
            balance = pd.DataFrame()
        
        try:
            cashflow = stock.cashflow
        except Exception:
            cashflow = pd.DataFrame()
        
        price = np.nan
        
        # السعر من history أولًا لتقليل مشكلة السعر القديم
        technical = technical_analysis(ticker)
        
        if technical:
            price = technical.get("السعر الفني", np.nan)
        
        if pd.isna(price):
            for key in [
                "currentPrice",
                "regularMarketPrice",
                "previousClose"
            ]:
                value = safe_float(info.get(key))
                
                if not pd.isna(value) and value > 0:
                    price = value
                    break
        
        revenue = latest_value(
            financials,
            ["Total Revenue", "Operating Revenue"]
        )
        
        previous_revenue = previous_value(
            financials,
            ["Total Revenue", "Operating Revenue"]
        )
        
        revenue_growth = growth(revenue, previous_revenue)
        
        net_income = latest_value(
            financials,
            ["Net Income", "Net Income Common Stockholders"]
        )
        
        previous_net_income = previous_value(
            financials,
            ["Net Income", "Net Income Common Stockholders"]
        )
        
        net_income_growth = growth(
            net_income,
            previous_net_income
        )
        
        gross_profit = latest_value(
            financials,
            ["Gross Profit"]
        )
        
        operating_income = latest_value(
            financials,
            ["Operating Income"]
        )
        
        ebitda = latest_value(
            financials,
            ["EBITDA", "Normalized EBITDA"]
        )
        
        operating_cash_flow = latest_value(
            cashflow,
            ["Operating Cash Flow", "Total Cash From Operating Activities"]
        )
        
        capex = latest_value(
            cashflow,
            ["Capital Expenditure", "Capital Expenditures"]
        )
        
        if not pd.isna(capex):
            capex_abs = abs(capex)
        else:
            capex_abs = np.nan
        
        if not pd.isna(operating_cash_flow) and not pd.isna(capex_abs):
            fcf = operating_cash_flow - capex_abs
        else:
            fcf = np.nan
        
        total_assets = latest_value(
            balance,
            ["Total Assets"]
        )
        
        total_liabilities = latest_value(
            balance,
            ["Total Liabilities Net Minority Interest", "Total Liabilities"]
        )
        
        equity = latest_value(
            balance,
            ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"]
        )
        
        cash = latest_value(
            balance,
            ["Cash Cash Equivalents And Short Term Investments",
             "Cash And Cash Equivalents",
             "Cash"]
        )
        
        debt = latest_value(
            balance,
            ["Total Debt", "Long Term Debt And Capital Lease Obligation"]
        )
        
        shares = safe_float(
            info.get("sharesOutstanding")
        )
        
        if pd.isna(shares) or shares <= 0:
            shares = np.nan
        
        # مؤشرات
        net_margin = ratio(net_income, revenue) * 100
        gross_margin = ratio(gross_profit, revenue) * 100
        operating_margin = ratio(operating_income, revenue) * 100
        
        roe = ratio(net_income, equity) * 100
        roa = ratio(net_income, total_assets) * 100
        
        debt_equity = ratio(debt, equity)
        
        if not pd.isna(debt) and not pd.isna(cash):
            net_debt = debt - cash
        else:
            net_debt = np.nan
        
        net_debt_ebitda = ratio(net_debt, ebitda)
        
        fcf_margin = ratio(fcf, revenue) * 100
        
        eps = safe_float(info.get("trailingEps"))
        
        if pd.isna(eps) and not pd.isna(net_income) and not pd.isna(shares):
            eps = net_income / shares
        
        pe = safe_float(info.get("trailingPE"))
        
        if pd.isna(pe) and not pd.isna(eps) and eps > 0 and not pd.isna(price):
            pe = price / eps
        
        pb = safe_float(info.get("priceToBook"))
        
        if pd.isna(pb) and not pd.isna(equity) and not pd.isna(shares):
            book_value_per_share = equity / shares
            
            if book_value_per_share > 0:
                pb = price / book_value_per_share
        
        dividend_yield = safe_float(
            info.get("dividendYield")
        )
        
        # Yahoo قد يرجعها كنسبة مئوية
        if not pd.isna(dividend_yield):
            if dividend_yield < 1:
                dividend_yield *= 100
        
        dividend_rate = safe_float(
            info.get("dividendRate")
        )
        
        # ====================================================
        # التقييم المالي
        # ====================================================
        
        scores = []
        
        sg = score_growth(revenue_growth)
        sn = score_growth(net_income_growth)
        sm = score_margin(net_margin)
        sr = score_roe(roe)
        sd = score_debt(debt_equity)
        sp = score_pe(pe)
        sb = score_pb(pb)
        sdiv = score_dividend(dividend_yield)
        
        scores.extend([
            sg,
            sn,
            sm,
            sr,
            sd,
            sp,
            sb,
            sdiv
        ])
        
        financial_score = float(np.nanmean(scores))
        
        # خصم بسيط عند نقص البيانات
        available = sum(
            not pd.isna(x)
            for x in [
                revenue_growth,
                net_income_growth,
                net_margin,
                roe,
                debt_equity,
                pe,
                pb,
                dividend_yield
            ]
        )
        
        coverage = available / 8
        
        financial_score *= (0.75 + 0.25 * coverage)
        financial_score = max(0, min(100, financial_score))
        
        # ====================================================
        # القيمة العادلة
        # ====================================================
        
        fair_values = []
        
        # P/E
        if not pd.isna(eps) and eps > 0:
            sector_multiple = {
                "البنوك": 9,
                "الخدمات المالية": 10,
                "العقارات": 9,
                "الرعاية الصحية": 12,
                "الاتصالات والتكنولوجيا": 12,
                "الطاقة والبتروكيماويات": 9,
                "الأغذية والسلع الاستهلاكية": 11,
                "الإنشاءات والهندسة": 10,
                "الصناعة والمواد / أخرى": 9
            }.get(sector, 9)
            
            fair_pe = eps * sector_multiple
            fair_values.append(fair_pe)
        
        # P/B
        if not pd.isna(equity) and not pd.isna(shares):
            book_value = equity / shares
            
            if book_value > 0:
                fair_pb_multiple = {
                    "البنوك": 1.3,
                    "الخدمات المالية": 1.5,
                    "العقارات": 1.3,
                    "الرعاية الصحية": 2,
                    "الاتصالات والتكنولوجيا": 2,
                    "الطاقة والبتروكيماويات": 1.5,
                    "الأغذية والسلع الاستهلاكية": 2,
                    "الإنشاءات والهندسة": 1.5,
                    "الصناعة والمواد / أخرى": 1.5
                }.get(sector, 1.5)
                
                fair_pb = book_value * fair_pb_multiple
                fair_values.append(fair_pb)
        
        # FCF
        if not pd.isna(fcf) and not pd.isna(shares) and fcf > 0:
            fcf_per_share = fcf / shares
            
            fair_fcf = fcf_per_share * 10
            fair_values.append(fair_fcf)
        
        if fair_values:
            fair_value = float(np.median(fair_values))
        else:
            fair_value = np.nan
        
        if not pd.isna(fair_value):
            buy_price = fair_value * 0.80
            attractive_price = fair_value * 0.88
        else:
            buy_price = np.nan
            attractive_price = np.nan
        
        # ====================================================
        # التقييم الفني
        # ====================================================
        
        technical_score = technical.get(
            "الدرجة الفنية",
            50
        )
        
        # ====================================================
        # الدرجة الإجمالية
        # ====================================================
        
        final_score = (
            financial_score * 0.65 +
            technical_score * 0.35
        )
        
        final_score = max(
            0,
            min(100, final_score)
        )
        
        if final_score >= 85:
            classification = "ممتاز"
        elif final_score >= 75:
            classification = "قوي"
        elif final_score >= 65:
            classification = "جيد"
        elif final_score >= 50:
            classification = "متوسط"
        else:
            classification = "ضعيف"
        
        # ====================================================
        # أهداف 3 سنوات
        # ====================================================
        
        if not pd.isna(fair_value):
            target_base = fair_value * 1.35
            target_bull = fair_value * 1.75
            target_bear = fair_value * 0.80
        else:
            target_base = np.nan
            target_bull = np.nan
            target_bear = np.nan
        
        # ====================================================
        # النتيجة
        # ====================================================
        
        return {
            "الرمز": symbol,
            "الشركة": info.get("longName", symbol),
            "القطاع": sector,
            "السعر": price,
            "تاريخ السعر": technical.get("تاريخ آخر شمعة", ""),
            "الإيرادات": revenue,
            "نمو الإيرادات": revenue_growth,
            "صافي الربح": net_income,
            "نمو صافي الربح": net_income_growth,
            "هامش صافي الربح": net_margin,
            "الهامش التشغيلي": operating_margin,
            "ROE": roe,
            "ROA": roa,
            "الدين/حقوق الملكية": debt_equity,
            "صافي الدين": net_debt,
            "Net Debt/EBITDA": net_debt_ebitda,
            "التدفق التشغيلي": operating_cash_flow,
            "FCF": fcf,
            "هامش FCF": fcf_margin,
            "EPS": eps,
            "P/E": pe,
            "P/B": pb,
            "عائد التوزيعات": dividend_yield,
            "التوزيع للسهم": dividend_rate,
            "القيمة العادلة": fair_value,
            "سعر شراء جذاب": attractive_price,
            "سعر شراء قوي": buy_price,
            "هدف 3 سنوات أساسي": target_base,
            "هدف 3 سنوات متفائل": target_bull,
            "سيناريو محافظ": target_bear,
            "الدرجة المالية": financial_score,
            "الدرجة الفنية": technical_score,
            "الدرجة النهائية": final_score,
            "التصنيف": classification,
            **technical
        }
        
    except Exception as e:
        return {
            "الرمز": ticker.replace(".CA", ""),
            "الشركة": ticker,
            "القطاع": sector_of(ticker),
            "الخطأ": str(e)
        }

# ============================================================
# واجهة التطبيق
# ============================================================

st.title("📊 EGX Financial Analyzer V3")

st.markdown(
    """
    ### محلل الأسهم المصرية
    **تحليل مالي + تقييم + قيمة عادلة + سعر شراء + تحليل فني**
    """
)

st.info(
    "⚠️ البيانات تعتمد على المصادر المتاحة عبر Yahoo Finance وقد يوجد تأخير أو نقص في بعض القوائم المالية."
)

# ============================================================
# الشريط الجانبي
# ============================================================

st.sidebar.header("⚙️ إعدادات التحليل")

workers = st.sidebar.slider(
    "عدد العمليات المتوازية",
    1,
    16,
    8
)

top_n = st.sidebar.slider(
    "عدد الأسهم المعروضة",
    5,
    50,
    20
)

sector_filter = st.sidebar.selectbox(
    "اختيار القطاع",
    [
        "كل القطاعات",
        "البنوك",
        "الخدمات المالية",
        "العقارات",
        "الرعاية الصحية",
        "الاتصالات والتكنولوجيا",
        "الطاقة والبتروكيماويات",
        "الأغذية والسلع الاستهلاكية",
        "الإنشاءات والهندسة",
        "الصناعة والمواد / أخرى"
    ]
)

run_analysis = st.sidebar.button(
    "🚀 تشغيل التحليل",
    use_container_width=True
)

# ============================================================
# الجلسة
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()

if run_analysis:
    
    stocks_to_analyze = EGX_STOCKS.copy()
    
    if sector_filter != "كل القطاعات":
        stocks_to_analyze = [
            x for x in stocks_to_analyze
            if sector_of(x) == sector_filter
        ]
    
    progress = st.progress(0)
    status = st.empty()
    
    results = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        
        futures = {
            executor.submit(analyze_stock, ticker): ticker
            for ticker in stocks_to_analyze
        }
        
        total = len(futures)
        completed = 0
        
        for future in as_completed(futures):
            
            completed += 1
            
            try:
                result = future.result()
                
                if result:
                    results.append(result)
            
            except Exception:
                pass
            
            progress.progress(
                completed / max(total, 1)
            )
            
            status.write(
                f"جاري تحليل {completed} من {total} سهم..."
            )
    
    progress.empty()
    status.empty()
    
    df = pd.DataFrame(results)
    
    if not df.empty:
        df = df[
            ~df["الرمز"].duplicated()
        ].copy()
        
        if "الدرجة النهائية" in df.columns:
            df = df.sort_values(
                "الدرجة النهائية",
                ascending=False
            )
    
    st.session_state.results = df
    
    st.success(
        f"تم تحليل {len(df)} سهم من أصل {len(stocks_to_analyze)} سهم."
    )

# ============================================================
# عرض النتائج
# ============================================================

df = st.session_state.results

if df.empty:
    
    st.warning(
        "اضغط «تشغيل التحليل» لبدء تحليل الأسهم."
    )
    
    st.markdown(
        f"""
        **عدد الأسهم في قاعدة البيانات:** {len(EGX_STOCKS)}
        
        التطبيق يقوم بتحليل:
        - النمو
        - الربحية
        - جودة الميزانية
        - الديون
        - التدفقات النقدية
        - التقييم
        - التوزيعات
        - الاتجاه الفني
        - القيمة العادلة
        - سعر الشراء
        - أهداف 3 سنوات
        """
    )
    
    st.stop()

# ============================================================
# التبويبات
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🏆 الترتيب",
        "🏭 القطاعات",
        "🔎 تحليل سهم",
        "📊 البيانات الكاملة"
    ]
)

# ============================================================
# الترتيب
# ============================================================

with tab1:
    
    st.subheader("🏆 أفضل الأسهم حسب الدرجة الإجمالية")
    
    display = df.head(top_n).copy()
    
    columns = [
        "الرمز",
        "الشركة",
        "القطاع",
        "السعر",
        "الدرجة المالية",
        "الدرجة الفنية",
        "الدرجة النهائية",
        "التصنيف",
        "القيمة العادلة",
        "سعر شراء جذاب",
        "هدف 3 سنوات أساسي",
        "P/E",
        "نمو الإيرادات",
        "نمو صافي الربح",
        "ROE",
        "عائد التوزيعات"
    ]
    
    columns = [
        x for x in columns
        if x in display.columns
    ]
    
    table = display[columns].copy()
    
    numeric_cols = [
        "السعر",
        "الدرجة المالية",
        "الدرجة الفنية",
        "الدرجة النهائية",
        "القيمة العادلة",
        "سعر شراء جذاب",
        "هدف 3 سنوات أساسي",
        "P/E",
        "نمو الإيرادات",
        "نمو صافي الربح",
        "ROE",
        "عائد التوزيعات"
    ]
    
    for col in numeric_cols:
        if col in table.columns:
            table[col] = pd.to_numeric(
                table[col],
                errors="coerce"
            ).round(2)
    
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("### 📌 قراءة الدرجات")
    
    st.write(
        """
        **الدرجة المالية = 65%** من الدرجة النهائية  
        **الدرجة الفنية = 35%** من الدرجة النهائية
        
        الدرجة لا تعني ضمان ارتفاع السهم، وإنما تجمع مجموعة من مؤشرات
        الجودة والنمو والتقييم والاتجاه الفني.
        """
    )

# ============================================================
# القطاعات
# ============================================================

with tab2:
    
    st.subheader("🏭 مقارنة القطاعات")
    
    if "القطاع" in df.columns:
        
        sector_summary = (
            df.groupby("القطاع")
            .agg(
                عدد_الأسهم=("الرمز", "count"),
                متوسط_المالي=("الدرجة المالية", "mean"),
                متوسط_الفني=("الدرجة الفنية", "mean"),
                متوسط_النهائي=("الدرجة النهائية", "mean"),
                متوسط_نمو_الإيرادات=("نمو الإيرادات", "mean"),
                متوسط_ROE=("ROE", "mean")
            )
            .reset_index()
        )
        
        sector_summary = sector_summary.sort_values(
            "متوسط_النهائي",
            ascending=False
        )
        
        sector_summary.columns = [
            "القطاع",
            "عدد الأسهم",
            "متوسط الدرجة المالية",
            "متوسط الدرجة الفنية",
            "متوسط الدرجة النهائية",
            "متوسط نمو الإيرادات",
            "متوسط ROE"
        ]
        
        st.dataframe(
            sector_summary.round(2),
            use_container_width=True,
            hide_index=True
        )
        
        st.bar_chart(
            sector_summary.set_index("القطاع")[
                "متوسط الدرجة النهائية"
            ]
        )

# ============================================================
# تحليل سهم منفرد
# ============================================================

with tab3:
    
    st.subheader("🔎 تحليل سهم بالتفصيل")
    
    symbols = sorted(
        df["الرمز"].dropna().unique().tolist()
    )
    
    selected = st.selectbox(
        "اختر السهم",
        symbols
    )
    
    row = df[
        df["الرمز"] == selected
    ].iloc[0]
    
    st.markdown(
        f"## {row.get('الشركة', selected)} — {selected}"
    )
    
    # --------------------------------------------------------
    # بطاقات رئيسية
    # --------------------------------------------------------
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    c1.metric(
        "السعر",
        fmt_price(row.get("السعر"))
    )
    
    c2.metric(
        "الدرجة النهائية",
        f"{row.get('الدرجة النهائية', np.nan):.1f}/100"
    )
    
    c3.metric(
        "الدرجة المالية",
        f"{row.get('الدرجة المالية', np.nan):.1f}"
    )
    
    c4.metric(
        "الدرجة الفنية",
        f"{row.get('الدرجة الفنية', np.nan):.1f}"
    )
    
    c5.metric(
        "التصنيف",
        row.get("التصنيف", "—")
    )
    
    # --------------------------------------------------------
    # التقييم
    # --------------------------------------------------------
    
    st.markdown("### 🎯 التقييم والقيمة العادلة")
    
    valuation = pd.DataFrame({
        "البند": [
            "السعر الحالي",
            "القيمة العادلة",
            "سعر شراء جذاب",
            "سعر شراء قوي",
            "هدف 3 سنوات — محافظ",
            "هدف 3 سنوات — أساسي",
            "هدف 3 سنوات — متفائل"
        ],
        "القيمة": [
            row.get("السعر"),
            row.get("القيمة العادلة"),
            row.get("سعر شراء جذاب"),
            row.get("سعر شراء قوي"),
            row.get("سيناريو محافظ"),
            row.get("هدف 3 سنوات أساسي"),
            row.get("هدف 3 سنوات متفائل")
        ]
    })
    
    valuation["القيمة"] = valuation["القيمة"].apply(
        lambda x: fmt_price(x)
    )
    
    st.dataframe(
        valuation,
        use_container_width=True,
        hide_index=True
    )
    
    # --------------------------------------------------------
    # المؤشرات المالية
    # --------------------------------------------------------
    
    st.markdown("### 💰 المؤشرات المالية")
    
    financial_table = pd.DataFrame({
        "المؤشر": [
            "الإيرادات",
            "نمو الإيرادات",
            "صافي الربح",
            "نمو صافي الربح",
            "هامش صافي الربح",
            "ROE",
            "ROA",
            "الدين / حقوق الملكية",
            "صافي الدين",
            "Net Debt / EBITDA",
            "التدفق النقدي التشغيلي",
            "FCF",
            "هامش FCF",
            "EPS",
            "P/E",
            "P/B",
            "عائد التوزيعات",
            "التوزيع للسهم"
        ],
        "القيمة": [
            fmt_money(row.get("الإيرادات")),
            fmt_pct(row.get("نمو الإيرادات")),
            fmt_money(row.get("صافي الربح")),
            fmt_pct(row.get("نمو صافي الربح")),
            fmt_pct(row.get("هامش صافي الربح")),
            fmt_pct(row.get("ROE")),
            fmt_pct(row.get("ROA")),
            (
                f"{row.get('الدين/حقوق الملكية'):.2f}"
                if not pd.isna(row.get("الدين/حقوق الملكية"))
                else "—"
            ),
            fmt_money(row.get("صافي الدين")),
            (
                f"{row.get('Net Debt/EBITDA'):.2f}"
                if not pd.isna(row.get("Net Debt/EBITDA"))
                else "—"
            ),
            fmt_money(row.get("التدفق التشغيلي")),
            fmt_money(row.get("FCF")),
            fmt_pct(row.get("هامش FCF")),
            fmt_price(row.get("EPS")),
            (
                f"{row.get('P/E'):.2f}"
                if not pd.isna(row.get("P/E"))
                else "—"
            ),
            (
                f"{row.get('P/B'):.2f}"
                if not pd.isna(row.get("P/B"))
                else "—"
            ),
            fmt_pct(row.get("عائد التوزيعات")),
            fmt_price(row.get("التوزيع للسهم"))
        ]
    })
    
    st.dataframe(
        financial_table,
        use_container_width=True,
        hide_index=True
    )
    
    # --------------------------------------------------------
    # الفني
    # --------------------------------------------------------
    
    st.markdown("### 📈 التحليل الفني")
    
    technical_table = pd.DataFrame({
        "المؤشر": [
            "الاتجاه",
            "RSI",
            "MACD",
            "EMA20",
            "EMA50",
            "EMA200",
            "ATR",
            "نسبة الحجم",
            "الدعم",
            "المقاومة",
            "قاع 52 أسبوع",
            "قمة 52 أسبوع",
            "آخر شمعة"
        ],
        "القيمة": [
            row.get("الاتجاه", "—"),
            (
                f"{row.get('RSI'):.2f}"
                if not pd.isna(row.get("RSI"))
                else "—"
            ),
            (
                f"{row.get('MACD'):.2f}"
                if not pd.isna(row.get("MACD"))
                else "—"
            ),
            fmt_price(row.get("EMA20")),
            fmt_price(row.get("EMA50")),
            fmt_price(row.get("EMA200")),
            fmt_price(row.get("ATR")),
            (
                f"{row.get('نسبة الحجم'):.2f}x"
                if not pd.isna(row.get("نسبة الحجم"))
                else "—"
            ),
            fmt_price(row.get("الدعم")),
            fmt_price(row.get("المقاومة")),
            fmt_price(row.get("قاع 52 أسبوع")),
            fmt_price(row.get("قمة 52 أسبوع")),
            row.get("تاريخ آخر شمعة", "—")
        ]
    })
    
    st.dataframe(
        technical_table,
        use_container_width=True,
        hide_index=True
    )
    
    # --------------------------------------------------------
    # خلاصة
    # --------------------------------------------------------
    
    st.markdown("### 🧠 الخلاصة الآلية")
    
    current_price = row.get("السعر")
    fair_value = row.get("القيمة العادلة")
    buy_price = row.get("سعر شراء قوي")
    
    if (
        not pd.isna(current_price)
        and not pd.isna(fair_value)
    ):
        
        upside = (
            (fair_value / current_price - 1) * 100
        )
        
        if upside >= 25:
            valuation_text = "يوجد هامش صعود نظري جيد مقابل القيمة العادلة."
        elif upside >= 10:
            valuation_text = "يوجد هامش صعود متوسط مقابل القيمة العادلة."
        elif upside >= -10:
            valuation_text = "السعر قريب نسبيًا من القيمة العادلة."
        else:
            valuation_text = "السعر أعلى من القيمة العادلة المحسوبة."
    
    else:
        valuation_text = "لا توجد بيانات كافية لحساب هامش القيمة."
    
    st.info(
        f"""
        **القطاع:** {row.get('القطاع', '—')}
        
        **الاتجاه الفني:** {row.get('الاتجاه', '—')}
        
        **التقييم:** {valuation_text}
        
        **سعر الشراء القوي المحسوب:** {fmt_price(buy_price)}
        
        **ملاحظة:** القيمة العادلة نموذج تقديري وليست سعرًا مضمونًا.
        """
    )

# ============================================================
# البيانات الكاملة
# ============================================================

with tab4:
    
    st.subheader("📊 قاعدة البيانات الكاملة")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    csv = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )
    
    st.download_button(
        "⬇️ تحميل النتائج CSV",
        data=csv,
        file_name="EGX_Financial_Analyzer_V3.csv",
        mime="text/csv",
        use_container_width=True
    )

# ============================================================
# تذييل
# ============================================================

st.markdown("---")

st.caption(
    f"""
    EGX Financial Analyzer V3 | آخر تحديث للتطبيق: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    النتائج تحليلية وليست توصية شراء أو بيع. 
    يجب مراجعة القوائم المالية والإفصاحات الرسمية قبل اتخاذ قرار استثماري.
    """
)
