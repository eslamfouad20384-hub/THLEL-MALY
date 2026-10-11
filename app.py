import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests, re, html
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="EGX Financial Data Collector", page_icon="📊", layout="wide")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}
CACHE_TTL = 3600

# قائمة مدمجة من رموز النسخة السابقة والقائمة المرجعية الموسعة.
# الرموز تظل ظاهرة حتى لو لم تتوفر لها بيانات.
RAW = r'''
COMI ADIB CIEB QNBA HDBK UBEE FAIT EXPA CICH HRHO EFGH CNFN MICH MUBI FWRY EFIH VALU
TMGH PHDC MNHD EMFD SODIC AMER ORHD ORAS SWDY MMMT AUTO ATLC ETEL EAST JUFO DOMT MFPC
ABUK EGAL AMOC EGAS SKPC TAQA ALCN UEFM BIOC NIPH ISPH DAPH MCQE MPCO MAAL RAYA RACC
GBCO GBCA MTIE OTHM NCCW NAEEM ROTO GHRS CCAP MOBG BINV DCRC DSCW EDBM ESRS KZPC SPMD
OCDI ODIN OCPH ODPH AIND AMIA ACGC APSW PACH PHTV EASB EGS ENGI FIPR FINS GTHE ICFC
IDHC IEEC INEG MENA MOIL NAHO OSCI PRCL PRMH SAFW SEIG SCTS SEDO SESC SHIP SMFR TAWF
TOLI TRTO UASG UEGC UNIT UNIP WADI YACO ZAHM ZEAL ZMID ZWDI ARCC AURC AXPH BTFH CLHO
DTPP FITE GEMM GMSH HITE IBCT ICID MOIN MPRC MPSO NDRG NINH PION PSMC SAUD SCEM SCFM
SLMF TANM TCOR TMMT VERT LCSW RUBX MEPA AMPI ARAB ALEX ECAP EGSW EMFD FITE HHDL MOIN
NEDA NSGB RAKT KABO SIPC SPIN SDTI SDAR AMER PHDC TMGH ORAS ORHD
ASCM ACTF KORA CRST NAPR GIHD EGCH ENPPI ELAB PMS ELMR PREG GDWA AIFI GOUR
BONY CERA COSG ELKA FERC MBSC TWSA MENA2 MIPH RAYA2
'''
LEGACY = tuple(dict.fromkeys(x.upper().replace('.CA','') for x in RAW.split() if re.fullmatch(r'[A-Za-z0-9]{2,10}(?:\.CA)?',x)))
CURRENT_RAW = r'''
COMI SWDY TMGH ETEL EGAL QNBE EAST MFPC ABUK ALCN HDBK EFIH ADIB ORAS FWRY EMFD SCTS ORHD EFID PHDC CANA GPPL JUFO BIOC VLMR VLMRA HRHO OCDI GBCO HELI BTFH FERC RAYA IRON CIEB FAITA FAIT EXPA EGCH PHAR CLHO VALU ARCC CIRA CCAP MTIE SCEM TAQA EFIC MCQE EGTS POUL SKPC NIPH ORWE MASR EGSA SAUD MOIL UBEE AMES EGBE ISPH RMDA TALM MBSC MHOT CICH ATQA AMOC CSAG BINV IFAP MPRC OLFI PRDC MOIN MIPH ISMQ OIH CPCI EGAS BONY PHTV DOMT SPHT AFMC KORA MPCI ZMID ELEC NINH SUGR ENGC ACAP AMIA NAPR AXPH GOUR CNFN ARAB AMER OCPH DSCW SPIN MICH GSSC KABO MFSC SVCE WCDF GDWA ADCI UNIT OFH UEFM AJWA SDTI INFI SAIB ELSH ELKA ASCM ACTF DAPH ACGC ACAMD ISMA LCSW GGCC KZPC SMFR ZEOT CRST ALRA CFGH ETRS EDFM ADPC NARE ATLC MILS MPCO PHGC IDRE GPIM UEGC GGRN RACC CEFM EHDR EALR NAHO AALR ECAP MOSC WKOL SNFC PRCL MAAL ODIN GTWL MENA SCFM DTPP NHPS NCCW CAED CERA DEIN SEIG SEIGA OBRI MEPA SIPC RREI NDRL AFDI AIDC ALUM AMII LUTS COSG ASPI EBSC POCO PRMH RTVC UNIP TANM GTEX MCRO KRDI APSW SPMD ICID ROTO AIHC MEGM ICLE RUBX TYCN EASB KWIN MOED RAKT AREH EEII CCRS EPCO GRCA GIHD ELWA ELNA DGTZ DCCC MMAT NEDA TRTO EPPK GMCI EOSB CPME COPR
'''
CURRENT = tuple(dict.fromkeys(x.upper().replace('.CA','') for x in CURRENT_RAW.split() if re.fullmatch(r'[A-Za-z0-9]{2,10}(?:\.CA)?',x)))

@st.cache_data(ttl=21600, show_spinner=False)
def get_universe():
    # القائمة ثابتة داخل الكود، مع محاولة إضافة الرموز الظاهرة من StockAnalysis.
    symbols=list(CURRENT)
    symbols.extend(x for x in LEGACY if x not in symbols)
    try:
        url='https://stockanalysis.com/list/egyptian-stock-exchange/'
        rr=requests.get(url,headers=HEADERS,timeout=12)
        if rr.ok:
            found=re.findall(r'/quote/egx/([A-Z][A-Z0-9]{1,9})(?:\.CA)?/?',rr.text,re.I)
            found += re.findall(r'\b([A-Z][A-Z0-9]{1,7})\.CA\b',rr.text)
            for x in found:
                x=x.upper().replace('.CA','')
                if x not in symbols and re.fullmatch(r'[A-Z][A-Z0-9]{1,9}',x): symbols.append(x)
    except Exception:
        pass
    return tuple(dict.fromkeys(symbols))

def parse_num(v):
    if v is None: return np.nan
    s=html.unescape(str(v)).replace(',', '').replace('٬','').replace('٫','.').strip()
    m=re.search(r'[-+]?\d+(?:\.\d+)?',s)
    try: return float(m.group(0)) if m else np.nan
    except Exception: return np.nan

def extract_label_number(page, labels):
    # يحاول قراءة الرقم القريب من التسمية في صفحات HTML.
    clean=html.unescape(page).replace('\u00a0',' ')
    clean=re.sub(r'<[^>]+>',' ',clean)
    clean=re.sub(r'\s+',' ',clean)
    for label in labels:
        pat=re.escape(label)+r'\s*(?:\([^)]*\))?\s*[:：]?\s*([-+]?\d[\d,]*(?:\.\d+)?)'
        m=re.search(pat,clean,re.I)
        if m:
            v=parse_num(m.group(1))
            if np.isfinite(v): return v
    return np.nan

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def mubasher_bvps(symbol):
    # نسختان من صفحة مباشر لتوسيع فرص العثور على القيمة الدفترية.
    urls=[f'https://english.mubasher.info/markets/EGX/stocks/{quote(symbol)}/',
          f'https://english-old.mubasher.info/markets/EGX/stocks/{quote(symbol)}']
    for url in urls:
        try:
            rr=requests.get(url,headers=HEADERS,timeout=9)
            if not rr.ok or not rr.text: continue
            val=extract_label_number(rr.text,[r'Book Value \(BVPS\)',r'Book Value Per Share',r'Book Value / Share',r'Book Value'])
            if np.isfinite(val): return {'bvps':val,'source':'Mubasher','url':url}
        except Exception: pass
    return {'bvps':np.nan,'source':'','url':''}

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def stockanalysis_bvps(symbol):
    urls=[f'https://stockanalysis.com/quote/egx/{quote(symbol)}/',
          f'https://stockanalysis.com/stocks/{quote(symbol.lower())}/']
    for url in urls:
        try:
            rr=requests.get(url,headers=HEADERS,timeout=9)
            if not rr.ok or not rr.text: continue
            val=extract_label_number(rr.text,['Book Value / Share','Book Value Per Share','Book Value per Share'])
            if np.isfinite(val): return {'bvps':val,'source':'StockAnalysis','url':url}
        except Exception: pass
    return {'bvps':np.nan,'source':'','url':''}

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def yahoo_data(symbol):
    ticker=yf.Ticker(symbol+'.CA')
    price=np.nan; price_date=''; bvps=np.nan; equity=np.nan; shares=np.nan; period=''
    # السعر: حصراً من آخر صف إغلاق في الشموع اليومية، وليس fast_info أو سعر لحظي.
    try:
        hist=ticker.history(period='10d',interval='1d',auto_adjust=False,actions=False)
        if hist is not None and not hist.empty and 'Close' in hist:
            q=hist.dropna(subset=['Close'])
            if not q.empty:
                price=float(q['Close'].iloc[-1])
                dt=pd.Timestamp(q.index[-1])
                price_date=dt.strftime('%Y-%m-%d')
    except Exception: pass
    # القيمة المباشرة من بيانات Yahoo إن توفرت.
    try:
        info=ticker.get_info()
        bvps=parse_num(info.get('bookValue'))
    except Exception: pass
    # احتياطي: حساب BVPS من أحدث حقوق ملكية وعدد أسهم متاحين فقط عند غياب القيمة المباشرة.
    try:
        bs=ticker.quarterly_balance_sheet
        if bs is None or bs.empty:
            bs=ticker.balance_sheet
        if bs is not None and not bs.empty:
            period=pd.Timestamp(bs.columns[0]).strftime('%Y-%m-%d')
            for key in ['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity','Total Stockholder Equity']:
                if key in bs.index:
                    vals=pd.to_numeric(bs.loc[key],errors='coerce').dropna()
                    if len(vals): equity=float(vals.iloc[0]); break
    except Exception: pass
    try:
        info=ticker.get_info()
        shares=parse_num(info.get('sharesOutstanding'))
    except Exception: pass
    if (not np.isfinite(bvps) or bvps<=0) and np.isfinite(equity) and np.isfinite(shares) and shares>0:
        bvps=equity/shares
    return {'price':price,'price_date':price_date,'bvps':bvps,'equity':equity,'shares':shares,'period':period,'source':'Yahoo Finance' if np.isfinite(bvps) else ''}

def _statement_row(df, candidates):
    """Return the first available statement row from candidate labels."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return {}
    norm = {re.sub(r'[^a-z0-9]', '', str(idx).lower()): idx for idx in df.index}
    for candidate in candidates:
        key = re.sub(r'[^a-z0-9]', '', candidate.lower())
        if key in norm:
            row = pd.to_numeric(df.loc[norm[key]], errors='coerce')
            return {pd.Timestamp(col).strftime('%Y-%m-%d'): float(val)
                    for col, val in row.items() if pd.notna(val)}
    for candidate in candidates:
        key = re.sub(r'[^a-z0-9]', '', candidate.lower())
        for nk, original in norm.items():
            if key and (key in nk or nk in key):
                row = pd.to_numeric(df.loc[original], errors='coerce')
                vals = {pd.Timestamp(col).strftime('%Y-%m-%d'): float(val)
                        for col, val in row.items() if pd.notna(val)}
                if vals:
                    return vals
    return {}


def _safe_statement(ticker, attr):
    try:
        value = getattr(ticker, attr)
        return value if isinstance(value, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=21600, show_spinner=False)
def financial_history(symbol, years=5):
    """Collect Yahoo annual/quarterly income statement and balance-sheet fields."""
    ticker = yf.Ticker(symbol + '.CA')
    annual_income = _safe_statement(ticker, 'income_stmt')
    annual_bs = _safe_statement(ticker, 'balance_sheet')
    quarterly_income = _safe_statement(ticker, 'quarterly_income_stmt')
    quarterly_bs = _safe_statement(ticker, 'quarterly_balance_sheet')
    field_candidates = {
        'الإيرادات / المبيعات': ['Total Revenue', 'Operating Revenue', 'Revenue', 'Total Operating Income'],
        'صافي الربح': ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing Operation Net Minority Interest', 'Net Income Including Noncontrolling Interests'],
        'إجمالي الأصول': ['Total Assets'],
        'إجمالي الالتزامات': ['Total Liabilities Net Minority Interest', 'Total Liabilities', 'Total Liab'],
        'حقوق الملكية': ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity', 'Total Stockholder Equity', 'Stockholders Equity Including Minority Interest'],
    }
    def build_period_rows(income_df, bs_df, frequency):
        values = {}
        for label, candidates in field_candidates.items():
            src = income_df if label in ('الإيرادات / المبيعات', 'صافي الربح') else bs_df
            values[label] = _statement_row(src, candidates)
        dates = sorted(set().union(*(set(v.keys()) for v in values.values())), reverse=True)
        dates = dates[:max(3, min(int(years), 5))] if frequency == 'سنوي' else dates[:8]
        rows = []
        for date in dates:
            row = {'رمز السهم': symbol + '.CA', 'نوع الفترة': frequency, 'نهاية الفترة': date,
                   'الإيرادات / المبيعات': np.nan, 'صافي الربح': np.nan,
                   'إجمالي الأصول': np.nan, 'إجمالي الالتزامات': np.nan, 'حقوق الملكية': np.nan,
                   'مصدر البيانات المالية': 'Yahoo Finance'}
            for label in field_candidates:
                if date in values[label]: row[label] = values[label][date]
            rows.append(row)
        return rows
    annual_rows = build_period_rows(annual_income, annual_bs, 'سنوي')
    quarterly_rows = build_period_rows(quarterly_income, quarterly_bs, 'ربع سنوي')
    shares = np.nan; shares_date = ''; shares_source = ''
    try:
        start_date = datetime.utcnow().replace(year=datetime.utcnow().year - 5).strftime('%Y-%m-%d')
        series = ticker.get_shares_full(start=start_date)
        if series is not None and len(series):
            ser = pd.to_numeric(series, errors='coerce').dropna().sort_index()
            if len(ser):
                shares = float(ser.iloc[-1])
                shares_date = pd.Timestamp(ser.index[-1]).strftime('%Y-%m-%d')
                shares_source = 'Yahoo Finance — تاريخي'
    except Exception:
        pass
    if not np.isfinite(shares):
        try:
            info = ticker.get_info()
            val = parse_num(info.get('sharesOutstanding'))
            if np.isfinite(val) and val > 0:
                shares = float(val)
                shares_source = 'Yahoo Finance — عدد حالي، التاريخ غير متاح'
        except Exception:
            pass
    return {'annual': annual_rows, 'quarterly': quarterly_rows,
            'shares': shares, 'shares_date': shares_date, 'shares_source': shares_source}


def analyze_symbol(symbol, years=5):
    y = yahoo_data(symbol)
    m = mubasher_bvps(symbol)
    s = stockanalysis_bvps(symbol)
    fin = financial_history(symbol, years)
    options = [m, s, y]
    chosen = next((x for x in options if np.isfinite(x.get('bvps', np.nan)) and x.get('bvps', np.nan) > 0), None)
    if chosen:
        bvps = float(chosen['bvps']); source = chosen.get('source', ''); bvps_status = 'متاحة'
    else:
        bvps = np.nan; source = ''; bvps_status = 'غير متاحة'
    periods = fin['quarterly'] or fin['annual']
    latest_period = periods[0]['نهاية الفترة'] if periods else y.get('period', '')
    return {
        'رمز السهم': symbol + '.CA',
        'السعر من آخر إغلاق يومي (جنيه)': y['price'], 'تاريخ شمعة السعر': y['price_date'],
        'القيمة الدفترية للسهم (جنيه)': bvps, 'مصدر القيمة الدفترية': source,
        'تاريخ أحدث فترة مالية متاحة': latest_period, 'عدد الأسهم': fin['shares'],
        'تاريخ عدد الأسهم': fin['shares_date'], 'مصدر عدد الأسهم': fin['shares_source'],
        'حالة القيمة الدفترية': bvps_status, 'رابط مباشر': m.get('url', ''),
        'رابط StockAnalysis': s.get('url', ''), '_annual': fin['annual'], '_quarterly': fin['quarterly']}

st.title('📊 الأسهم المصرية — بيانات السعر والقوائم المالية')
st.caption('مرحلة 1: آخر إغلاق يومي والقيمة الدفترية. مرحلة 2: الإيرادات وصافي الربح سنويًا، والأصول والالتزامات وحقوق الملكية سنويًا وربع سنوي، وعدد الأسهم مع تاريخه إن توفر.')
with st.expander('مصادر البيانات وحدود التغطية', expanded=False):
    st.markdown('''- **السعر اليومي:** آخر إغلاق يومي متاح من Yahoo Finance، مع تاريخ الشمعة.
- **القيمة الدفترية:** Mubasher ثم StockAnalysis ثم Yahoo Finance، مع إبقاء الخانة فارغة إذا لم نجد رقمًا صالحًا.
- **القوائم المالية السنوية والربع سنوية:** Yahoo Finance عبر income statement وbalance sheet.
- **عدد الأسهم:** سلسلة عدد الأسهم التاريخية من Yahoo عند توافرها؛ وإلا عدد الأسهم الحالي مع توضيح أن تاريخه غير متاح.
- **مهم:** تغطية Yahoo للأسهم المصرية غير كاملة. الفراغ لا يعني صفرًا، ولا يعني أن الشركة لا تنشر هذه البيانات. الأرقام تعرض كما أعادها المصدر، ويجب التحقق من العملة ووحدة العرض قبل استخدامها في حسابات التقييم.''')

cset1, cset2 = st.columns([1, 2])
years = cset1.selectbox('عدد السنوات السنوية المطلوبة', [3, 4, 5], index=2)
workers = cset2.slider('عدد عمليات الجلب المتوازية', 1, 12, 5)
if st.button('🔄 جلب / تحديث البيانات', type='primary'):
    st.cache_data.clear()
    st.rerun()

symbols = get_universe()
st.info(f'عدد الرموز الفريدة داخل قائمة البرنامج: {len(symbols)} — الرموز التي لا تتوفر لها بيانات ستظل في النتائج مع توضيح الخانات الناقصة.')
if st.button('▶️ ابدأ جلب البيانات المالية', type='primary'):
    summaries, annual_rows, quarterly_rows = [], [], []
    progress = st.progress(0); status = st.empty()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(analyze_symbol, sym, years): sym for sym in symbols}
        total = len(futures)
        for i, future in enumerate(as_completed(futures), 1):
            sym = futures[future]
            try:
                result = future.result()
                annual_rows.extend(result.pop('_annual', []))
                quarterly_rows.extend(result.pop('_quarterly', []))
                summaries.append(result)
            except Exception:
                summaries.append({'رمز السهم': sym + '.CA', 'السعر من آخر إغلاق يومي (جنيه)': np.nan,
                    'تاريخ شمعة السعر': '', 'القيمة الدفترية للسهم (جنيه)': np.nan,
                    'مصدر القيمة الدفترية': '', 'تاريخ أحدث فترة مالية متاحة': '', 'عدد الأسهم': np.nan,
                    'تاريخ عدد الأسهم': '', 'مصدر عدد الأسهم': '', 'حالة القيمة الدفترية': 'خطأ في الجلب',
                    'رابط مباشر': '', 'رابط StockAnalysis': ''})
            progress.progress(i / max(total, 1)); status.text(f'تم فحص {i} من {total}: {sym}')
    summary_df = pd.DataFrame(summaries).sort_values('رمز السهم').reset_index(drop=True)
    st.session_state['summary_results'] = summary_df
    st.session_state['annual_results'] = pd.DataFrame(annual_rows)
    st.session_state['quarterly_results'] = pd.DataFrame(quarterly_rows)

if 'summary_results' in st.session_state:
    summary_df = st.session_state['summary_results']
    annual_df = st.session_state.get('annual_results', pd.DataFrame())
    quarterly_df = st.session_state.get('quarterly_results', pd.DataFrame())
    a, b, c, d = st.columns(4)
    a.metric('إجمالي الرموز', len(summary_df))
    b.metric('أسعار يومية متاحة', int(summary_df['السعر من آخر إغلاق يومي (جنيه)'].notna().sum()))
    c.metric('أسهم لها بيانات سنوية', int(annual_df['رمز السهم'].nunique()) if not annual_df.empty else 0)
    d.metric('أسهم لها بيانات ربع سنوية', int(quarterly_df['رمز السهم'].nunique()) if not quarterly_df.empty else 0)
    tab1, tab2, tab3 = st.tabs(['ملخص الأسهم', 'القوائم السنوية', 'القوائم ربع السنوية'])
    with tab1:
        st.dataframe(summary_df, use_container_width=True, hide_index=True,
                     column_config={'رابط مباشر': st.column_config.LinkColumn('رابط مباشر'), 'رابط StockAnalysis': st.column_config.LinkColumn('رابط StockAnalysis')})
        st.download_button('⬇️ تنزيل ملخص الأسهم CSV', summary_df.to_csv(index=False).encode('utf-8-sig'), 'egx_summary.csv', 'text/csv')
    with tab2:
        if annual_df.empty:
            st.warning('لم يتم إرجاع قوائم سنوية من المصدر للرموز المختارة.')
        else:
            annual_df = annual_df.sort_values(['رمز السهم', 'نهاية الفترة'], ascending=[True, False])
            st.dataframe(annual_df, use_container_width=True, hide_index=True)
            st.download_button('⬇️ تنزيل القوائم السنوية CSV', annual_df.to_csv(index=False).encode('utf-8-sig'), 'egx_annual_financials.csv', 'text/csv')
    with tab3:
        if quarterly_df.empty:
            st.warning('لم يتم إرجاع قوائم ربع سنوية من المصدر للرموز المختارة.')
        else:
            quarterly_df = quarterly_df.sort_values(['رمز السهم', 'نهاية الفترة'], ascending=[True, False])
            st.dataframe(quarterly_df, use_container_width=True, hide_index=True)
            st.download_button('⬇️ تنزيل القوائم ربع السنوية CSV', quarterly_df.to_csv(index=False).encode('utf-8-sig'), 'egx_quarterly_financials.csv', 'text/csv')
