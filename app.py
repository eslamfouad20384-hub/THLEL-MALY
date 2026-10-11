import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ============================================================
# EGX BOOK VALUE + LAST DAILY CLOSE ONLY
# The app retrieves ONLY: last available daily closing price and book value/share.
# ============================================================
st.set_page_config(page_title="EGX | السعر والقيمة الدفترية", page_icon="📊", layout="wide")
st.title("📊 الأسهم المصرية — السعر من آخر شمعة يومية والقيمة الدفترية")
st.caption("البيانات المعروضة فقط: آخر إغلاق يومي متاح + القيمة الدفترية للسهم. لا يوجد تحليل فني أو تقييم أو مؤشرات إضافية.")

# قائمة رموز مدمجة من القائمة السابقة في المشروع والقائمة المرجعية الموسعة.
# القائمة الحية تُضاف إليها الرموز التي يمكن اكتشافها من المصدر العام، عند توفره.
RAW_SYMBOLS = """COMI ADIB CIEB QNBA HDBK UBEE FAIT EXPA CICH HRHO EFGH CNFN MICH MUBI FWRY EFIH VALU TMGH PHDC MNHD EMFD SODIC AMER ORHD ORAS SWDY MMMT AUTO ATLC ETEL EAST JUFO DOMT MFPC ABUK EGAL AMOC EGAS SKPC TAQA ALCN UEFM BIOC NIPH ISPH DAPH MCQE MPCO MAAL RAYA RACC GBCO GBCA MTIE OTHM NCCW NAEEM ROTO GHRS CCAP MOBG BINV DCRC DSCW EDBM ESRS KZPC SPMD OCDI ODIN OCPH ODPH AIND AMIA ACGC APSW PACH PHTV EASB EGS ENGI FIPR FINS GTHE ICFC IDHC IEEC INEG MENA MOIL NAHO OSCI PRCL PRMH SAFW SEIG SCTS SEDO SESC SHIP SMFR TAWF TOLI TRTO UASG UEGC UNIT UNIP WADI YACO ZAHM ZEAL ZMID ZWDI ARCC AURC AXPH BTFH CLHO DTPP FITE GEMM GMSH HITE IBCT ICID MOIN MPRC MPSO NDRG NINH PION PSMC SAUD SCEM SCFM SLMF TANM TCOR TMMT VERT LCSW RUBX MEPA AMPI ARAB ALEX ECAP EGSW HHDL NEDA NSGB RAKT KABO SIPC SPIN SDTI SDAR ASCM ACTF KORA CRST NAPR GIHD EGCH ENPPI ELAB PMS ELMR PREG GDWA AIFI GOUR BONY CERA COSG ELKA FERC MBSC TWSA MENA2 MIPH RAYA2 QNBE EFID CANA GPPL VLMR VLMRA HELI IRON FAITA PHAR CIRA EFIC EGTS POUL ORWE MASR EGSA AMES EGBE RMDA TALM MHOT ATQA CSAG IFAP OLFI PRDC ISMQ OIH CPCI SPHT AFMC MPCI ELEC SUGR ENGC ACAP GSSC MFSC SVCE WCDF ADCI OFH AJWA INFI SAIB ELSH ACAMD ISMA GGCC ZEOT ALRA CFGH ETRS EDFM ADPC NARE MILS PHGC IDRE GPIM GGRN CEFM EHDR EALR AALR MOSC WKOL SNFC GTWL NHPS CAED DEIN SEIGA OBRI RREI NDRL AFDI AIDC ALUM AMII LUTS ASPI EBSC POCO RTVC GTEX MCRO KRDI AIHC MEGM ICLE TYCN KWIN MOED AREH EEII CCRS EPCO GRCA ELWA ELNA DGTZ DCCC MMAT EPPK GMCI EOSB CPME COPR"""
BASE_STOCKS = list(dict.fromkeys(s.strip().upper().replace('.CA','') for s in RAW_SYMBOLS.split() if s.strip()))

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}

@st.cache_data(ttl=6*60*60, show_spinner=False)
def get_all_symbols():
    symbols = list(BASE_STOCKS)
    # Try public exchange/company listings; retain embedded symbols if source is unavailable.
    urls = [
        "https://stockanalysis.com/list/egyptian-stock-exchange/",
        "https://www.egx.com.eg/en/ListedStocks.aspx",
    ]
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=12)
            if response.ok:
                html = response.text
                found = re.findall(r"/stocks/([A-Z0-9]{2,10})/", html)
                found += re.findall(r"(?:ticker|symbol)[^A-Z0-9]{0,20}([A-Z]{2,6})", html, re.I)
                for symbol in found:
                    symbol = symbol.upper().replace('.CA','')
                    if symbol not in symbols and symbol.isalnum():
                        symbols.append(symbol)
        except Exception:
            pass
    return symbols


def get_last_daily_close(symbol):
    """Return the last non-null Close from downloaded daily candles only."""
    ticker = symbol if symbol.endswith('.CA') else symbol + '.CA'
    try:
        hist = yf.download(
            ticker, period="15d", interval="1d", auto_adjust=False,
            progress=False, threads=False, actions=False
        )
        if hist is None or hist.empty:
            return np.nan, None
        if isinstance(hist.columns, pd.MultiIndex):
            try:
                hist = hist.xs(ticker, axis=1, level=-1)
            except Exception:
                hist.columns = hist.columns.get_level_values(0)
        if "Close" not in hist.columns:
            return np.nan, None
        close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if close.empty:
            return np.nan, None
        last_date = pd.Timestamp(close.index[-1]).date().isoformat()
        return float(close.iloc[-1]), last_date
    except Exception:
        return np.nan, None


def get_book_value_per_share(symbol):
    """Use Yahoo's BVPS when available; otherwise equity / shares outstanding.
    No price, technical indicator, valuation or other financial metric is returned.
    """
    ticker = symbol if symbol.endswith('.CA') else symbol + '.CA'
    try:
        obj = yf.Ticker(ticker)
        info = obj.get_info() or {}
        bvps = info.get("bookValue")
        try:
            bvps = float(bvps)
            if np.isfinite(bvps) and bvps > 0:
                return bvps, "Yahoo Finance: bookValue"
        except (TypeError, ValueError):
            pass
        shares = info.get("sharesOutstanding")
        try:
            shares = float(shares)
        except (TypeError, ValueError):
            shares = np.nan
        # Latest available balance-sheet equity divided by shares outstanding.
        balance = obj.get_balance_sheet()
        if balance is not None and not balance.empty and np.isfinite(shares) and shares > 0:
            equity = np.nan
            for row in ("Stockholders Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest", "Common Stock Equity"):
                if row in balance.index:
                    vals = pd.to_numeric(balance.loc[row], errors="coerce").dropna()
                    if not vals.empty:
                        equity = float(vals.iloc[0])
                        break
            if np.isfinite(equity):
                return equity / shares, "Yahoo Finance: latest equity / sharesOutstanding"
    except Exception:
        pass
    return np.nan, "غير متاح من المصدر"


def analyze_symbol(symbol):
    price, candle_date = get_last_daily_close(symbol)
    bvps, bv_source = get_book_value_per_share(symbol)
    return {
        "رمز السهم": symbol + ".CA",
        "السعر من آخر إغلاق يومي (جنيه)": price,
        "تاريخ آخر شمعة يومية": candle_date or "غير متاح",
        "القيمة الدفترية للسهم (جنيه)": bvps,
        "مصدر القيمة الدفترية": bv_source,
    }

with st.sidebar:
    st.header("الإعدادات")
    workers = st.slider("عدد الاتصالات المتوازية", 1, 8, 4)
    run = st.button("🔄 جلب السعر والقيمة الدفترية", type="primary", use_container_width=True)

symbols = get_all_symbols()
st.info(f"عدد الرموز المضمنة والمكتشفة: {len(symbols)} — يتم الاحتفاظ بالرموز حتى لو كانت البيانات غير متاحة.")

if run:
    results = []
    progress = st.progress(0, text="جاري جلب آخر إغلاق يومي والقيمة الدفترية...")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(analyze_symbol, s): s for s in symbols}
        total = len(futures)
        for i, future in enumerate(as_completed(futures), start=1):
            symbol = futures[future]
            try:
                results.append(future.result())
            except Exception:
                results.append({"رمز السهم": symbol + ".CA", "السعر من آخر إغلاق يومي (جنيه)": np.nan,
                                "تاريخ آخر شمعة يومية": "غير متاح", "القيمة الدفترية للسهم (جنيه)": np.nan,
                                "مصدر القيمة الدفترية": "غير متاح من المصدر"})
            progress.progress(i / total, text=f"تم فحص {i} من {total} سهم")
    df = pd.DataFrame(results)
    df = df.sort_values("رمز السهم", kind="stable").reset_index(drop=True)
    st.session_state["egx_book_price_results"] = df
    progress.empty()

if "egx_book_price_results" in st.session_state:
    df = st.session_state["egx_book_price_results"]
    c1, c2, c3 = st.columns(3)
    c1.metric("عدد الأسهم في الجدول", f"{len(df):,}")
    c2.metric("أسعار يومية متاحة", f"{df['السعر من آخر إغلاق يومي (جنيه)'].notna().sum():,}")
    c3.metric("قيم دفترية متاحة", f"{df['القيمة الدفترية للسهم (جنيه)'].notna().sum():,}")
    st.dataframe(df, use_container_width=True, hide_index=True, height=650)
    st.download_button("⬇️ تنزيل CSV", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="EGX_Last_Daily_Close_Book_Value.csv", mime="text/csv")
    st.caption("تنبيه: عدم ظهور قيمة لا يعني أن القيمة الدفترية صفر؛ قد تكون غير متاحة من مصدر البيانات. تاريخ السعر هو تاريخ آخر شمعة يومية أعادها المصدر، وقد لا يطابق تاريخ اليوم إذا كان السوق مغلقًا أو البيانات متأخرة.")
else:
    st.warning("اضغط زر الجلب لعرض عمودَي السعر والقيمة الدفترية فقط، مع تاريخ الشمعة ومصدر القيمة الدفترية للمراجعة.")
