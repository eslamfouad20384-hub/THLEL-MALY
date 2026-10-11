import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests, re, html
from io import StringIO
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
def _stockanalysis_parse_value(value, multiplier=1.0):
    """Parse StockAnalysis table cells and normalize their stated unit to EGP."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    raw = str(value).strip().replace(',', '').replace('−', '-')
    if raw in {'', '-', '—', '–', 'N/A', 'n/a', 'None'}:
        return np.nan
    m = re.search(r'([-+]?\d+(?:\.\d+)?)\s*([KMBT])?', raw, re.I)
    if not m:
        return np.nan
    number = float(m.group(1))
    suffix = (m.group(2) or '').upper()
    scale = {'': 1, 'K': 1e3, 'M': 1e6, 'B': 1e9, 'T': 1e12}.get(suffix, 1)
    return number * scale * multiplier


def _period_date_from_label(label):
    """Convert StockAnalysis labels such as Dec '25, Q2 2026 or FY 2025 to period-end dates."""
    text = str(label or '').replace('’', "'").strip()
    m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*'?\s*(\d{2,4})\b", text, re.I)
    if m:
        year = int(m.group(2)); year = year + 2000 if year < 100 else year
        month = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}[m.group(1).lower()]
        return f'{year:04d}-{month:02d}-{pd.Period(f"{year}-{month:02d}").days_in_month:02d}'
    m = re.search(r'\bQ([1-4])\s*(\d{4})\b', text, re.I)
    if m:
        q, year = int(m.group(1)), int(m.group(2)); month = q * 3
        return f'{year:04d}-{month:02d}-{pd.Period(f"{year}-{month:02d}").days_in_month:02d}'
    m = re.search(r'\bFY\s*(\d{4})\b|\b(20\d{2})\b', text, re.I)
    if m:
        year = int(m.group(1) or m.group(2)); return f'{year:04d}-12-31'
    return ''


@st.cache_data(ttl=21600, show_spinner=False)
def stockanalysis_financial_history(symbol, years=5):
    """Best-effort extraction of StockAnalysis financial tables; keeps source and unit explicit."""
    base = f'https://stockanalysis.com/quote/egx/{quote(symbol)}/financials/'
    pages = [
        ('سنوي', base),
        ('سنوي', base + 'balance-sheet/'),
        ('ربع سنوي', base + '?p=quarterly'),
        ('ربع سنوي', base + 'balance-sheet/?p=quarterly'),
        ('سنوي', base + 'cash-flow-statement/'),
        ('ربع سنوي', base + 'cash-flow-statement/?p=quarterly'),
    ]
    aliases = {
        'الإيرادات / المبيعات': ['revenue', 'total revenue', 'operating revenue'],
        'صافي الربح': ['net income', 'net income common stockholders', 'net income to common shareholders'],
        'إجمالي الأصول': ['total assets'],
        'إجمالي الالتزامات': ['total liabilities'],
        'حقوق الملكية': ['shareholders equity', "shareholders' equity", 'total common equity', 'total equity'],
        'رأس المال / الأسهم العادية': ['common stock', 'common shares outstanding', 'total common shares outstanding'],
        'التدفقات النقدية التشغيلية': ['operating cash flow', 'cash from operations', 'cash flow from operations', 'net cash provided by operating activities'],
    }
    out = []
    for frequency, url in pages:
        try:
            rr = requests.get(url, headers=HEADERS, timeout=12)
            if not rr.ok or not rr.text:
                continue
            page_text = html.unescape(re.sub(r'<[^>]+>', ' ', rr.text))
            # StockAnalysis financial tables commonly report values in millions EGP.
            multiplier = 1e6 if re.search(r'(?:financials|millions)\s+in\s+millions\s+EGP|millions\s+EGP', page_text, re.I) else 1.0
            try:
                tables = pd.read_html(StringIO(rr.text))
            except Exception:
                tables = []
            for table in tables:
                if table.empty or len(table.columns) < 2:
                    continue
                # Flatten multi-row / tuple headers while preserving column labels.
                cols = []
                for c in table.columns:
                    if isinstance(c, tuple): cols.append(' '.join(str(x) for x in c if str(x) != 'nan'))
                    else: cols.append(str(c))
                table.columns = cols
                label_col = table.columns[0]
                labels = table[label_col].astype(str).str.strip()
                if not labels.str.contains(r'Revenue|Net Income|Total Assets|Total Liabilities|Shareholders.? Equity|Common Stock|Operating Cash Flow|Cash from Operations|Cash Flow from Operations|Net Cash Provided by Operating Activities', case=False, regex=True).any():
                    continue
                # A Period Ending row gives exact month/quarter ends; otherwise use period headers.
                date_by_col = {}
                period_rows = table[labels.str.contains('Period Ending', case=False, na=False)]
                if not period_rows.empty:
                    pr = period_rows.iloc[0]
                    for col in table.columns[1:]:
                        date_by_col[col] = _period_date_from_label(pr[col])
                for col in table.columns[1:]:
                    if not date_by_col.get(col): date_by_col[col] = _period_date_from_label(col)
                valid_cols = [(col, date_by_col[col]) for col in table.columns[1:] if date_by_col.get(col)]
                if not valid_cols:
                    continue
                for col, period_date in valid_cols:
                    # If the quarterly toggle was ignored by the website, do not mislabel annual December-only data as quarterly.
                    if frequency == 'ربع سنوي' and period_date[5:7] == '12' and not re.search(r'Q[1-4]|Quarterly', str(col), re.I):
                        continue
                    try:
                        year = int(period_date[:4])
                        if frequency == 'سنوي' and year < datetime.utcnow().year - max(3, min(int(years), 5)):
                            continue
                    except Exception:
                        pass
                    row = {'رمز السهم': symbol + '.CA', 'نوع الفترة': frequency, 'نهاية الفترة': period_date,
                           'الإيرادات / المبيعات': np.nan, 'صافي الربح': np.nan, 'إجمالي الأصول': np.nan,
                           'إجمالي الالتزامات': np.nan, 'حقوق الملكية': np.nan, 'رأس المال / الأسهم العادية': np.nan, 'التدفقات النقدية التشغيلية': np.nan,
                           'مصدر البيانات المالية': 'StockAnalysis', 'وحدة المصدر الأصلية': 'ملايين جنيه مصري' if multiplier == 1e6 else 'الوحدة كما ظهرت بالمصدر'}
                    for _, tr in table.iterrows():
                        label = str(tr[label_col]).strip().lower()
                        for field, names in aliases.items():
                            if any(label == name or label.startswith(name + ' ') for name in names):
                                val = _stockanalysis_parse_value(tr[col], multiplier=multiplier)
                                if pd.notna(val): row[field] = val
                    if any(pd.notna(row[k]) for k in aliases):
                        out.append(row)
        except Exception:
            continue
    # Collapse duplicate rows from multiple tables/pages for the same period, preferring populated fields.
    if not out:
        return {'annual': [], 'quarterly': []}
    df = pd.DataFrame(out)
    result = {'annual': [], 'quarterly': []}
    fields = list(aliases.keys())
    for freq in ('سنوي', 'ربع سنوي'):
        part = df[df['نوع الفترة'] == freq].sort_values('نهاية الفترة', ascending=False)
        for (sym, period), grp in part.groupby(['رمز السهم', 'نهاية الفترة'], sort=False):
            row = {'رمز السهم': sym, 'نوع الفترة': freq, 'نهاية الفترة': period,
                   'مصدر البيانات المالية': 'StockAnalysis', 'وحدة المصدر الأصلية': 'ملايين جنيه مصري بعد التطبيع إلى جنيه' }
            for field in fields:
                vals = pd.to_numeric(grp[field], errors='coerce').dropna() if field in grp else pd.Series(dtype=float)
                row[field] = float(vals.iloc[0]) if len(vals) else np.nan
            result['annual' if freq == 'سنوي' else 'quarterly'].append(row)
    return result


def financial_history(symbol, years=5):
    """Collect Yahoo annual/quarterly income statement and balance-sheet fields."""
    ticker = yf.Ticker(symbol + '.CA')
    annual_income = _safe_statement(ticker, 'income_stmt')
    annual_bs = _safe_statement(ticker, 'balance_sheet')
    quarterly_income = _safe_statement(ticker, 'quarterly_income_stmt')
    quarterly_bs = _safe_statement(ticker, 'quarterly_balance_sheet')
    annual_cf = _safe_statement(ticker, 'cashflow')
    quarterly_cf = _safe_statement(ticker, 'quarterly_cashflow')
    field_candidates = {
        'الإيرادات / المبيعات': ['Total Revenue', 'Operating Revenue', 'Revenue', 'Total Operating Income'],
        'صافي الربح': ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing Operation Net Minority Interest', 'Net Income Including Noncontrolling Interests'],
        'إجمالي الأصول': ['Total Assets'],
        'إجمالي الالتزامات': ['Total Liabilities Net Minority Interest', 'Total Liabilities', 'Total Liab'],
        'حقوق الملكية': ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity', 'Total Stockholder Equity', 'Stockholders Equity Including Minority Interest'],
        'رأس المال / الأسهم العادية': ['Common Stock', 'Capital Stock', 'Ordinary Share Capital'],
        'التدفقات النقدية التشغيلية': ['Operating Cash Flow', 'Cash Flow From Continuing Operating Activities', 'Net Cash Provided By Operating Activities', 'Cash From Operations'],
    }
    def build_period_rows(income_df, bs_df, cf_df, frequency):
        values = {}
        for label, candidates in field_candidates.items():
            if label in ('الإيرادات / المبيعات', 'صافي الربح'):
                src = income_df
            elif label == 'التدفقات النقدية التشغيلية':
                src = cf_df
            else:
                src = bs_df
            values[label] = _statement_row(src, candidates)
        dates = sorted(set().union(*(set(v.keys()) for v in values.values())), reverse=True)
        dates = dates[:max(3, min(int(years), 5))] if frequency == 'سنوي' else dates[:8]
        rows = []
        for date in dates:
            row = {'رمز السهم': symbol + '.CA', 'نوع الفترة': frequency, 'نهاية الفترة': date,
                   'الإيرادات / المبيعات': np.nan, 'صافي الربح': np.nan,
                   'إجمالي الأصول': np.nan, 'إجمالي الالتزامات': np.nan, 'حقوق الملكية': np.nan, 'رأس المال / الأسهم العادية': np.nan, 'التدفقات النقدية التشغيلية': np.nan,
                   'مصدر البيانات المالية': 'Yahoo Finance'}
            for label in field_candidates:
                if date in values[label]: row[label] = values[label][date]
            rows.append(row)
        return rows
    annual_rows = build_period_rows(annual_income, annual_bs, annual_cf, 'سنوي')
    quarterly_rows = build_period_rows(quarterly_income, quarterly_bs, quarterly_cf, 'ربع سنوي')
    # Add StockAnalysis as an independent fallback. Yahoo values are never silently overwritten.
    sa = stockanalysis_financial_history(symbol, years)
    statement_comparisons = []
    financial_fields = ['الإيرادات / المبيعات', 'صافي الربح', 'إجمالي الأصول', 'إجمالي الالتزامات', 'حقوق الملكية', 'التدفقات النقدية التشغيلية']
    for freq_key, yahoo_rows in [('annual', annual_rows), ('quarterly', quarterly_rows)]:
        sa_rows = sa.get(freq_key, [])
        by_period = {str(r.get('نهاية الفترة')): r for r in sa_rows}
        for yr in yahoo_rows:
            alt = by_period.get(str(yr.get('نهاية الفترة')))
            for field in financial_fields:
                if not alt: continue
                yv = pd.to_numeric(pd.Series([yr.get(field, np.nan)]), errors='coerce').iloc[0]
                sv = pd.to_numeric(pd.Series([alt.get(field, np.nan)]), errors='coerce').iloc[0]
                if pd.notna(yv) and pd.notna(sv):
                    rel = abs(float(yv)-float(sv))/max(abs(float(yv)),abs(float(sv)),1e-9)*100
                    if rel >= 10:
                        statement_comparisons.append({'رمز السهم': symbol+'.CA', 'نوع الفترة': yr.get('نوع الفترة',''), 'نهاية الفترة': yr.get('نهاية الفترة',''), 'البند': field, 'Yahoo Finance': float(yv), 'StockAnalysis': float(sv), 'الفرق النسبي %': round(rel,2), 'وحدة Yahoo': 'كما أعادها المصدر؛ يلزم التحقق', 'وحدة StockAnalysis': alt.get('وحدة المصدر الأصلية',''), 'الحالة': 'تعارض يحتاج مراجعة؛ لم يتم اختيار قيمة تلقائيًا'})
                elif pd.isna(yv) and pd.notna(sv):
                    yr[field] = float(sv)
                    yr['مصدر البيانات المالية'] = 'Yahoo Finance + StockAnalysis (استكمال الخانات الناقصة)'
    # Add StockAnalysis periods not returned by Yahoo; these remain clearly labeled as alternate-source rows.
    for freq_key, yahoo_rows in [('annual', annual_rows), ('quarterly', quarterly_rows)]:
        existing = {str(r.get('نهاية الفترة')) for r in yahoo_rows}
        for alt in sa.get(freq_key, []):
            if str(alt.get('نهاية الفترة')) not in existing:
                yahoo_rows.append(alt)
    annual_rows = sorted(annual_rows, key=lambda r: str(r.get('نهاية الفترة','')), reverse=True)
    quarterly_rows = sorted(quarterly_rows, key=lambda r: str(r.get('نهاية الفترة','')), reverse=True)
    shares = np.nan; shares_date = ''; shares_source = ''; shares_history = []
    try:
        start_date = datetime.utcnow().replace(year=datetime.utcnow().year - 5).strftime('%Y-%m-%d')
        series = ticker.get_shares_full(start=start_date)
        if series is not None and len(series):
            ser = pd.to_numeric(series, errors='coerce').dropna().sort_index()
            if len(ser):
                shares = float(ser.iloc[-1])
                shares_date = pd.Timestamp(ser.index[-1]).strftime('%Y-%m-%d')
                shares_source = 'Yahoo Finance — تاريخي'
                shares_history = [{'رمز السهم': symbol + '.CA', 'تاريخ عدد الأسهم': pd.Timestamp(dt).strftime('%Y-%m-%d'), 'عدد الأسهم': float(value), 'المصدر': 'Yahoo Finance — تاريخي'} for dt, value in ser.items() if pd.notna(value)]
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
    return {'annual': annual_rows, 'quarterly': quarterly_rows, 'shares_history': shares_history,
            'shares': shares, 'shares_date': shares_date, 'shares_source': shares_source, 'statement_comparisons': statement_comparisons}


def analyze_symbol(symbol, years=5):
    y = yahoo_data(symbol)
    m = mubasher_bvps(symbol)
    s = stockanalysis_bvps(symbol)
    fin = financial_history(symbol, years)
    options = [m, s, y]
    valid = [x for x in options if np.isfinite(x.get('bvps', np.nan)) and x.get('bvps', np.nan) > 0]
    chosen = valid[0] if valid else None
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
        'BVPS Mubasher': m.get('bvps', np.nan), 'BVPS StockAnalysis': s.get('bvps', np.nan),
        'BVPS Yahoo Finance': y.get('bvps', np.nan),
        'تاريخ أحدث فترة مالية متاحة': latest_period, 'عدد الأسهم': fin['shares'],
        'تاريخ عدد الأسهم': fin['shares_date'], 'مصدر عدد الأسهم': fin['shares_source'],
        'حقوق الملكية من Yahoo': y.get('equity', np.nan), 'تاريخ حقوق الملكية من Yahoo': y.get('period', ''),
        'حالة القيمة الدفترية': bvps_status, 'رابط مباشر': m.get('url', ''),
        'رابط StockAnalysis': s.get('url', ''), '_annual': fin['annual'], '_quarterly': fin['quarterly'],
        '_shares_history': fin.get('shares_history', []), '_statement_comparisons': fin.get('statement_comparisons', [])}


def _date_age_days(value):
    try:
        dt = pd.to_datetime(value, errors='coerce', utc=True)
        if pd.isna(dt): return None
        return max(0, (pd.Timestamp.now(tz='UTC') - dt).days)
    except Exception:
        return None


def build_quality_report(summary_df, annual_df, quarterly_df, shares_history_df):
    """Create transparent data-quality flags; never silently choose a conflicting number."""
    issues = []
    def add(symbol, category, severity, detail, fields='', sources='', periods='', units=''):
        issues.append({'رمز السهم': symbol, 'نوع الفحص': category, 'الخطورة': severity,
                       'التفاصيل': detail, 'البيانات المعنية': fields, 'المصادر': sources,
                       'الفترات': periods, 'الوحدات / ملاحظات': units})

    # Missingness and freshness at the summary level
    for _, row in summary_df.iterrows():
        sym = str(row.get('رمز السهم', ''))
        if pd.isna(row.get('السعر من آخر إغلاق يومي (جنيه)', np.nan)):
            add(sym, 'بيانات ناقصة', 'مرتفعة', 'السعر اليومي غير متاح.', 'السعر', 'Yahoo Finance', str(row.get('تاريخ شمعة السعر', '')), 'سعر السهم بالجنيه حسب المصدر')
        age = _date_age_days(row.get('تاريخ شمعة السعر', ''))
        if age is not None and age > 5:
            add(sym, 'حداثة البيانات', 'متوسطة' if age <= 15 else 'مرتفعة', f'آخر شمعة أقدم من {age} يومًا؛ تحقق من توقف التداول أو تأخر المصدر.', 'السعر وتاريخ الشمعة', 'Yahoo Finance', str(row.get('تاريخ شمعة السعر', '')), 'أيام تقويمية')
        if pd.isna(row.get('القيمة الدفترية للسهم (جنيه)', np.nan)):
            add(sym, 'بيانات ناقصة', 'متوسطة', 'القيمة الدفترية للسهم غير متاحة من المصادر التي جرى فحصها.', 'BVPS', 'Mubasher / StockAnalysis / Yahoo Finance', '', 'القيمة بالجنيه؛ قد تكون التغطية غير متاحة')
        # Compare all available BVPS source values, preserving all raw values.
        vals = []
        for col, source_name in [('BVPS Mubasher','Mubasher'), ('BVPS StockAnalysis','StockAnalysis'), ('BVPS Yahoo Finance','Yahoo Finance')]:
            v = pd.to_numeric(pd.Series([row.get(col, np.nan)]), errors='coerce').iloc[0]
            if pd.notna(v) and v > 0: vals.append((source_name, float(v)))
        if len(vals) >= 2:
            numbers = [v for _, v in vals]
            spread = (max(numbers) - min(numbers)) / max(abs(float(np.median(numbers))), 1e-9) * 100
            if spread > 10:
                add(sym, 'اختلاف مصادر', 'مرتفعة' if spread > 25 else 'متوسطة',
                    f'توجد فروق بين قيم BVPS؛ التفاوت النسبي التقريبي {spread:.1f}%. لم يتم اختيار رقم باعتباره الصحيح تلقائيًا.',
                    'BVPS', '؛ '.join(f'{n}: {v:g}' for n,v in vals), 'تواريخ تقارير المصادر غير متاحة دائمًا', 'جنيه/سهم؛ راجع تعريف القيمة والفترة والوحدة')
        # Reconcile equity / shares against chosen BVPS only as a review flag, not a hard error.
        equity = pd.to_numeric(pd.Series([row.get('حقوق الملكية من Yahoo', np.nan)]), errors='coerce').iloc[0]
        shares = pd.to_numeric(pd.Series([row.get('عدد الأسهم', np.nan)]), errors='coerce').iloc[0]
        bvps = pd.to_numeric(pd.Series([row.get('القيمة الدفترية للسهم (جنيه)', np.nan)]), errors='coerce').iloc[0]
        if pd.notna(equity) and pd.notna(shares) and shares > 0 and pd.notna(bvps) and bvps > 0:
            implied = equity / shares
            rel = abs(implied - bvps) / max(abs(bvps), 1e-9) * 100
            if rel > 20:
                add(sym, 'مطابقة محاسبية', 'مراجعة مطلوبة',
                    f'حقوق الملكية ÷ عدد الأسهم ≈ {implied:,.4g} مقابل BVPS المعروضة {bvps:,.4g} (فرق {rel:.1f}%). قد ينتج الفرق عن اختلاف الفترة أو التعريف أو الوحدة أو عدد الأسهم.',
                    'حقوق الملكية، عدد الأسهم، BVPS', 'Yahoo Finance مقابل ' + str(row.get('مصدر القيمة الدفترية','')), 
                    f"حقوق الملكية: {row.get('تاريخ حقوق الملكية من Yahoo','')}؛ عدد الأسهم: {row.get('تاريخ عدد الأسهم','')}؛ BVPS: التاريخ غير مؤكد", 'لا تُعتبر مخالفة مؤكدة قبل توحيد العملة والوحدة وتاريخ التقرير ونطاق حقوق الأقلية')

    # Statement rows: missing fields, stale periods, duplicates, and repeated/flat values.
    expected = ['الإيرادات / المبيعات', 'صافي الربح', 'إجمالي الأصول', 'إجمالي الالتزامات', 'حقوق الملكية']
    for label, df, stale_limit in [('سنوي', annual_df, 550), ('ربع سنوي', quarterly_df, 190)]:
        if df is None or df.empty: continue
        key_cols = [c for c in ['رمز السهم','نوع الفترة','نهاية الفترة'] if c in df.columns]
        if len(key_cols) == 3:
            dupmask = df.duplicated(key_cols, keep=False)
            for _, r in df[dupmask].iterrows():
                add(str(r.get('رمز السهم','')), 'تكرار سجلات', 'متوسطة', 'يوجد أكثر من سجل لنفس السهم ونوع الفترة وتاريخ نهايتها.', ', '.join(key_cols), str(r.get('مصدر البيانات المالية','')), str(r.get('نهاية الفترة','')), 'تم اكتشاف التكرار دون حذف السجلات')
        for _, r in df.iterrows():
            sym = str(r.get('رمز السهم','')); period = str(r.get('نهاية الفترة',''))
            missing = [c for c in expected if c in df.columns and pd.isna(r.get(c, np.nan))]
            if missing:
                add(sym, 'بيانات ناقصة', 'متوسطة', f"حقول غير متاحة في سجل {label}: " + '، '.join(missing), ', '.join(missing), str(r.get('مصدر البيانات المالية','')), period, 'القيم غير المتاحة تظل فارغة ولا تُعامل كصفر')
            age = _date_age_days(period)
            if age is not None and age > stale_limit:
                add(sym, 'حداثة البيانات المالية', 'متوسطة' if age <= stale_limit*1.5 else 'مرتفعة', f'نهاية فترة القوائم أقدم من {age} يومًا.', 'القوائم المالية', str(r.get('مصدر البيانات المالية','')), period, f'حد التنبيه: {stale_limit} يومًا؛ التقادم لا يعني وحده أن البيانات خاطئة')

    # Changes in reported share capital (only when the source exposes a distinct capital line).
    capital_frames = []
    for frame in (annual_df, quarterly_df):
        if frame is not None and not frame.empty and 'رأس المال / الأسهم العادية' in frame.columns:
            part = frame[['رمز السهم', 'نهاية الفترة', 'رأس المال / الأسهم العادية']].copy()
            part['رأس المال / الأسهم العادية'] = pd.to_numeric(part['رأس المال / الأسهم العادية'], errors='coerce')
            part = part.dropna(subset=['رأس المال / الأسهم العادية'])
            if not part.empty: capital_frames.append(part)
    if capital_frames:
        capital_df = pd.concat(capital_frames, ignore_index=True).drop_duplicates(['رمز السهم','نهاية الفترة'])
        for sym, grp in capital_df.groupby('رمز السهم'):
            grp = grp.sort_values('نهاية الفترة')
            if len(grp) >= 2:
                first, last = grp.iloc[0], grp.iloc[-1]
                old, new = first['رأس المال / الأسهم العادية'], last['رأس المال / الأسهم العادية']
                change = (new / old - 1) * 100 if old else np.nan
                if pd.notna(change) and abs(change) >= 5:
                    add(sym, 'تغير رأس المال', 'مرتفعة' if abs(change) >= 20 else 'متوسطة',
                        f"تغير بند رأس المال/الأسهم العادية بنحو {change:+.1f}% بين {first['نهاية الفترة']} و{last['نهاية الفترة']}.",
                        'رأس المال / الأسهم العادية', 'Yahoo Finance — القوائم المالية', f"{first['نهاية الفترة']} إلى {last['نهاية الفترة']}", 'قد تختلف تسمية البند أو وحدته؛ يلزم التحقق من إيضاحات القوائم والإفصاحات الرسمية')

    # Share-count changes, only if Yahoo returned dated historical observations.
    if shares_history_df is not None and not shares_history_df.empty:
        for sym, grp in shares_history_df.groupby('رمز السهم'):
            grp = grp.copy()
            grp['عدد الأسهم'] = pd.to_numeric(grp['عدد الأسهم'], errors='coerce')
            grp = grp.dropna(subset=['عدد الأسهم']).sort_values('تاريخ عدد الأسهم')
            if len(grp) >= 2:
                first, last = grp.iloc[0], grp.iloc[-1]
                change = (last['عدد الأسهم'] / first['عدد الأسهم'] - 1) * 100 if first['عدد الأسهم'] else np.nan
                if pd.notna(change) and abs(change) >= 5:
                    add(sym, 'تغير عدد الأسهم', 'مرتفعة' if abs(change) >= 20 else 'متوسطة',
                        f"تغير عدد الأسهم المسجل بنحو {change:+.1f}% بين {first['تاريخ عدد الأسهم']} و{last['تاريخ عدد الأسهم']}.",
                        'عدد الأسهم', 'Yahoo Finance — تاريخي', f"{first['تاريخ عدد الأسهم']} إلى {last['تاريخ عدد الأسهم']}", 'قد يعكس زيادة رأس مال أو تجزئة/توزيع أسهم أو تعديلات مصدر؛ يحتاج تحققًا من إفصاحات الشركة')

    # Duplicate source rows across statement data are flagged, not silently removed.
    return pd.DataFrame(issues, columns=['رمز السهم','نوع الفحص','الخطورة','التفاصيل','البيانات المعنية','المصادر','الفترات','الوحدات / ملاحظات'])

# ========================= المرحلة الرابعة: مؤشرات التحليل المالي =========================
# تصنيف أولي للقطاعات؛ الرموز غير المؤكدة تظل "غير محدد" ولا يتم اختلاق قطاع لها.
SECTOR_MAP = {
    'بنوك': set('COMI ADIB CIEB QNBA HDBK UBEE FAIT EXPA CICH MUBI EGBE SAIB CANA'.split()),
    'خدمات مالية غير مصرفية': set('HRHO EFGH CNFN MICH FWRY EFIH VALU BTFH RAYA RACC BINV NAEEM'.split()),
    'عقارات': set('TMGH PHDC MNHD EMFD SODIC AMER ORHD OTHM OCDI ODIN HELI'.split()),
    'صناعة ومواد أساسية': set('SWDY MMMT AUTO EGAL ESRS KZPC SPMD UEFM AMOC SKPC MFPC ABUK TAQA EGAS'.split()),
    'أدوية ورعاية صحية': set('BIOC NIPH ISPH DAPH OCPH ODPH PHAR CLHO IDHC RMDA AXPH MIPH'.split()),
    'اتصالات وتكنولوجيا': set('ETEL EFIH FWRY GBCO MTIE'.split()),
    'أغذية ومشروبات': set('EAST JUFO DOMT OLFI POUL'.split()),
    'طاقة وبترول': set('AMOC EGAS SKPC TAQA MOIL'.split()),
}

def classify_sector(symbol):
    code = str(symbol).upper().replace('.CA','').strip()
    for sector, members in SECTOR_MAP.items():
        if code in members:
            return sector
    return 'غير محدد'


def _num(row, key):
    try:
        v = pd.to_numeric(pd.Series([row.get(key, np.nan)]), errors='coerce').iloc[0]
        return float(v) if pd.notna(v) and np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def _pct_change(current, previous):
    if not np.isfinite(current) or not np.isfinite(previous) or abs(previous) < 1e-9:
        return np.nan
    # Growth is not economically interpretable as a conventional percentage when prior value <= 0.
    if previous <= 0:
        return np.nan
    return (current / previous - 1.0) * 100.0


def _latest_period_rows(frame):
    if frame is None or frame.empty or 'نهاية الفترة' not in frame.columns:
        return pd.DataFrame()
    work = frame.copy()
    work['نهاية الفترة'] = work['نهاية الفترة'].astype(str)
    work = work.sort_values('نهاية الفترة', ascending=False)
    # For duplicated same-period records, combine only missing cells; do not average conflicting values.
    out = []
    for (symbol, period), grp in work.groupby(['رمز السهم','نهاية الفترة'], dropna=False, sort=False):
        row = grp.iloc[0].to_dict()
        for col in work.columns:
            if pd.isna(row.get(col, np.nan)):
                candidates = grp[col].dropna() if col in grp else pd.Series(dtype=object)
                if len(candidates): row[col] = candidates.iloc[0]
        out.append(row)
    return pd.DataFrame(out).sort_values('نهاية الفترة', ascending=False) if out else pd.DataFrame()


def _score_metric(value, thresholds, reverse=False):
    """Simple transparent heuristic score 0-100; not a valuation or investment recommendation."""
    if not np.isfinite(value):
        return np.nan
    # thresholds is an ascending list of (minimum value, score)
    score = 0
    for threshold, points in thresholds:
        if value >= threshold:
            score = points
    return 100 - score if reverse else score


def build_financial_indicators(summary_df, annual_df, quarterly_df):
    if summary_df is None or summary_df.empty:
        return pd.DataFrame()
    annual = _latest_period_rows(annual_df)
    quarterly = _latest_period_rows(quarterly_df)
    rows = []
    for _, summary in summary_df.iterrows():
        symbol = str(summary.get('رمز السهم',''))
        sector = classify_sector(symbol)
        a = annual[annual['رمز السهم'].astype(str).eq(symbol)].sort_values('نهاية الفترة', ascending=False) if not annual.empty else pd.DataFrame()
        q = quarterly[quarterly['رمز السهم'].astype(str).eq(symbol)].sort_values('نهاية الفترة', ascending=False) if not quarterly.empty else pd.DataFrame()
        latest = a.iloc[0].to_dict() if not a.empty else {}
        previous = a.iloc[1].to_dict() if len(a) >= 2 else {}
        latest_q = q.iloc[0].to_dict() if not q.empty else {}
        # Revenue/profit growth only when periods are comparable and prior base is positive.
        revenue_growth = _pct_change(_num(latest,'الإيرادات / المبيعات'), _num(previous,'الإيرادات / المبيعات'))
        profit_growth = _pct_change(_num(latest,'صافي الربح'), _num(previous,'صافي الربح'))
        # Annual growth must compare separate fiscal years, not two dates from the same year.
        try:
            latest_date = pd.to_datetime(latest.get('نهاية الفترة'), errors='coerce')
            previous_date = pd.to_datetime(previous.get('نهاية الفترة'), errors='coerce')
            if pd.isna(latest_date) or pd.isna(previous_date) or (latest_date - previous_date).days < 300:
                revenue_growth = np.nan; profit_growth = np.nan
        except Exception:
            revenue_growth = np.nan; profit_growth = np.nan
        quarterly_revenue_growth = np.nan; quarterly_profit_growth = np.nan
        if not q.empty:
            try:
                q = q.copy(); q['_dt'] = pd.to_datetime(q['نهاية الفترة'], errors='coerce')
                q_latest = q.iloc[0]
                q_date = q_latest['_dt']
                comparable = q[(q['_dt'] < q_date) & ((q_date - q['_dt']).dt.days.between(330, 400))]
                if not comparable.empty:
                    q_prev = comparable.sort_values('_dt', ascending=False).iloc[0]
                    quarterly_revenue_growth = _pct_change(_num(q_latest, 'الإيرادات / المبيعات'), _num(q_prev, 'الإيرادات / المبيعات'))
                    quarterly_profit_growth = _pct_change(_num(q_latest, 'صافي الربح'), _num(q_prev, 'صافي الربح'))
            except Exception:
                pass
        revenue = _num(latest,'الإيرادات / المبيعات')
        net_income = _num(latest,'صافي الربح')
        assets = _num(latest,'إجمالي الأصول')
        liabilities = _num(latest,'إجمالي الالتزامات')
        equity = _num(latest,'حقوق الملكية')
        prev_assets = _num(previous,'إجمالي الأصول')
        prev_equity = _num(previous,'حقوق الملكية')
        avg_assets = (assets + prev_assets)/2 if np.isfinite(assets) and np.isfinite(prev_assets) and assets + prev_assets != 0 else assets
        avg_equity = (equity + prev_equity)/2 if np.isfinite(equity) and np.isfinite(prev_equity) and equity + prev_equity != 0 else equity
        margin = net_income/revenue*100 if np.isfinite(net_income) and np.isfinite(revenue) and revenue > 0 else np.nan
        roe = net_income/avg_equity*100 if np.isfinite(net_income) and np.isfinite(avg_equity) and avg_equity > 0 else np.nan
        roa = net_income/avg_assets*100 if np.isfinite(net_income) and np.isfinite(avg_assets) and avg_assets > 0 else np.nan
        leverage = liabilities/equity if np.isfinite(liabilities) and np.isfinite(equity) and equity > 0 else np.nan
        cfo = _num(latest,'التدفقات النقدية التشغيلية')
        quality = cfo/net_income if np.isfinite(cfo) and np.isfinite(net_income) and net_income > 0 else np.nan
        # A bank's leverage and conventional net margin are not scored like a non-financial company.
        if sector == 'بنوك':
            weights = {'roe': .35, 'revenue_growth': .10, 'profit_growth': .20, 'margin': .05, 'cash_quality': .10, 'coverage': .20}
        elif sector == 'عقارات':
            weights = {'roe': .15, 'revenue_growth': .15, 'profit_growth': .20, 'margin': .15, 'roa': .10, 'leverage': .10, 'cash_quality': .10, 'coverage': .05}
        elif sector == 'خدمات مالية غير مصرفية':
            weights = {'roe': .20, 'revenue_growth': .15, 'profit_growth': .20, 'margin': .10, 'roa': .10, 'leverage': .05, 'cash_quality': .10, 'coverage': .10}
        else:
            weights = {'roe': .15, 'revenue_growth': .15, 'profit_growth': .20, 'margin': .10, 'roa': .10, 'leverage': .10, 'cash_quality': .10, 'coverage': .10}
        metric_values = {
            'roe': _score_metric(roe, [(0,20),(5,40),(10,60),(15,80),(20,100)]),
            'revenue_growth': _score_metric(revenue_growth, [(-10,20),(0,35),(5,50),(10,65),(20,80),(30,100)]),
            'profit_growth': _score_metric(profit_growth, [(-10,15),(0,30),(5,45),(10,60),(20,80),(30,100)]),
            'margin': _score_metric(margin, [(0,20),(3,35),(7,50),(12,70),(20,85),(30,100)]),
            'roa': _score_metric(roa, [(0,20),(1,35),(3,55),(5,75),(8,100)]),
            'leverage': _score_metric(leverage, [(0,100),(0.5,85),(1,70),(2,50),(3,30),(5,10)], reverse=False),
            'cash_quality': _score_metric(quality, [(0,10),(0.5,35),(0.8,60),(1,80),(1.2,100)]),
        }
        # Coverage score is explicit and based on availability of the core annual fields.
        core = ['الإيرادات / المبيعات','صافي الربح','إجمالي الأصول','إجمالي الالتزامات','حقوق الملكية','التدفقات النقدية التشغيلية']
        available = sum(np.isfinite(_num(latest, f)) for f in core)
        coverage = available / len(core) * 100 if latest else 0
        metric_values['coverage'] = coverage
        valid_weight = sum(w for key,w in weights.items() if np.isfinite(metric_values.get(key,np.nan)))
        score = sum(weights[key]*metric_values[key] for key in weights if np.isfinite(metric_values.get(key,np.nan))) / valid_weight if valid_weight else np.nan
        # Do not present a score when data coverage is very low.
        if available < 3:
            score = np.nan
        status = 'بيانات محدودة — لا يُعتمد على الدرجة' if available < 3 else ('مؤشر مبدئي' if available < 5 else 'مؤشر مبدئي ببيانات أفضل')
        rows.append({
            'رمز السهم': symbol, 'القطاع المبدئي': sector, 'آخر سنة مالية': latest.get('نهاية الفترة',''),
            'نمو الإيرادات سنويًا %': revenue_growth, 'نمو صافي الربح سنويًا %': profit_growth,
            'نمو الإيرادات ربع سنويًا مقابل نفس الربع السابق %': quarterly_revenue_growth, 'نمو صافي الربح ربع سنويًا مقابل نفس الربع السابق %': quarterly_profit_growth,
            'هامش صافي الربح %': margin, 'ROE العائد على حقوق الملكية %': roe,
            'ROA العائد على الأصول %': roa, 'الالتزامات / حقوق الملكية': leverage,
            'التدفقات النقدية التشغيلية': cfo, 'جودة الأرباح CFO / صافي الربح': quality,
            'السنة المالية السابقة': previous.get('نهاية الفترة',''), 'آخر ربع متاح': latest_q.get('نهاية الفترة',''),
            'درجة القوة المالية المبدئية /100': round(score,1) if np.isfinite(score) else np.nan,
            'تغطية البيانات الأساسية %': round(coverage,1), 'حالة المؤشر': status,
            'مصدر القوائم السنوية': latest.get('مصدر البيانات المالية',''),
            'تنبيه القطاع': 'نسب الرفع المالي وهامش الربح لا تُقارن مباشرة بين القطاعات؛ أوزان البنوك مختلفة، والتصنيف آلي مبدئي.'
        })
    return pd.DataFrame(rows)


st.title('📊 الأسهم المصرية — بيانات السعر والقوائم المالية')
st.caption('مرحلة 1: السعر اليومي والقيمة الدفترية. مرحلة 2: القوائم السنوية والربع سنوية وعدد الأسهم. مرحلة 3: تدقيق جودة البيانات. مرحلة 4: مؤشرات مالية أولية مع أوزان قطاعية مختلفة.')
with st.expander('مصادر البيانات وحدود التغطية', expanded=False):
    st.markdown('''- **السعر اليومي:** آخر إغلاق يومي متاح من Yahoo Finance، مع تاريخ الشمعة.
- **القيمة الدفترية:** Mubasher ثم StockAnalysis ثم Yahoo Finance، مع إبقاء الخانة فارغة إذا لم نجد رقمًا صالحًا.
- **القوائم المالية السنوية والربع سنوية:** Yahoo Finance أولًا، مع StockAnalysis كمصدر مستقل للاستكمال والمقارنة عند توفر الجداول.
- **مصدر أولي للتحقق من الإفصاحات:** البورصة المصرية EGX؛ يفتح التطبيق صفحة البورصة الرسمية وروابط القوائم المالية في Mubasher للمراجعة اليدوية عند تعذر الاستخراج الآلي.
- **عدد الأسهم:** سلسلة عدد الأسهم التاريخية من Yahoo عند توافرها؛ وإلا عدد الأسهم الحالي مع توضيح أن تاريخه غير متاح.
- **مهم:** تغطية Yahoo للأسهم المصرية غير كاملة. الفراغ لا يعني صفرًا. الأرقام تعرض كما أعادها المصدر، ويجب التحقق من العملة ووحدة العرض قبل استخدامها في التقييم.
- **فحوص الجودة:** تكتشف القيم الناقصة والقديمة والتكرار واختلاف BVPS بين المصادر وتغير عدد الأسهم أو بند رأس المال عند توفره، وتُظهر فروق المطابقة بين حقوق الملكية/عدد الأسهم وBVPS كتنبيه للمراجعة لا كخطأ مؤكد. لا يُختار رقم متعارض تلقائيًا.''')

cset1, cset2 = st.columns([1, 2])
years = cset1.selectbox('عدد السنوات السنوية المطلوبة', [3, 4, 5], index=2)
workers = cset2.slider('عدد عمليات الجلب المتوازية', 1, 12, 5)
if st.button('🔄 جلب / تحديث البيانات', type='primary'):
    st.cache_data.clear()
    st.rerun()

symbols = get_universe()
st.info(f'عدد الرموز الفريدة داخل قائمة البرنامج: {len(symbols)} — الرموز التي لا تتوفر لها بيانات ستظل في النتائج مع توضيح الخانات الناقصة.')
if st.button('▶️ ابدأ جلب البيانات المالية', type='primary'):
    summaries, annual_rows, quarterly_rows, shares_history_rows, statement_comparisons = [], [], [], [], []
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
                shares_history_rows.extend(result.pop('_shares_history', []))
                statement_comparisons.extend(result.pop('_statement_comparisons', []))
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
    st.session_state['shares_history_results'] = pd.DataFrame(shares_history_rows)
    st.session_state['statement_comparisons'] = pd.DataFrame(statement_comparisons)

if 'summary_results' in st.session_state:
    summary_df = st.session_state['summary_results']
    annual_df = st.session_state.get('annual_results', pd.DataFrame())
    quarterly_df = st.session_state.get('quarterly_results', pd.DataFrame())
    shares_history_df = st.session_state.get('shares_history_results', pd.DataFrame())
    statement_comparisons_df = st.session_state.get('statement_comparisons', pd.DataFrame())
    quality_df = build_quality_report(summary_df, annual_df, quarterly_df, shares_history_df)
    a, b, c, d = st.columns(4)
    a.metric('إجمالي الرموز', len(summary_df))
    b.metric('أسعار يومية متاحة', int(summary_df['السعر من آخر إغلاق يومي (جنيه)'].notna().sum()))
    c.metric('أسهم لها بيانات سنوية', int(annual_df['رمز السهم'].nunique()) if not annual_df.empty else 0)
    d.metric('أسهم لها بيانات ربع سنوية', int(quarterly_df['رمز السهم'].nunique()) if not quarterly_df.empty else 0)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(['ملخص الأسهم', 'القوائم السنوية', 'القوائم ربع السنوية', 'تدقيق جودة البيانات', 'مقارنة المصادر وروابطها', 'مؤشرات التحليل المالي'])
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
    with tab4:
        if quality_df.empty:
            st.success('لم تُكتشف مشكلات وفق الفحوص الحالية، أو أن البيانات المتاحة لا تكفي لإصدار تنبيهات. عدم وجود تنبيه لا يضمن صحة كل الأرقام.')
        else:
            q1, q2, q3 = st.columns(3)
            q1.metric('إجمالي تنبيهات الجودة', len(quality_df))
            q2.metric('أسهم عليها تنبيه', quality_df['رمز السهم'].nunique())
            q3.metric('تنبيهات مرتفعة', int((quality_df['الخطورة'] == 'مرتفعة').sum()))
            sev = st.multiselect('تصفية حسب الخطورة', ['مرتفعة','متوسطة','مراجعة مطلوبة'], default=['مرتفعة','متوسطة','مراجعة مطلوبة'])
            cat = st.multiselect('تصفية حسب نوع الفحص', sorted(quality_df['نوع الفحص'].dropna().unique().tolist()), default=sorted(quality_df['نوع الفحص'].dropna().unique().tolist()))
            filtered = quality_df[quality_df['الخطورة'].isin(sev) & quality_df['نوع الفحص'].isin(cat)]
            st.dataframe(filtered, use_container_width=True, hide_index=True)
            st.download_button('⬇️ تنزيل تقرير جودة البيانات CSV', quality_df.to_csv(index=False).encode('utf-8-sig'), 'egx_data_quality_report.csv', 'text/csv')
            if not shares_history_df.empty:
                with st.expander('سجل تغير عدد الأسهم الذي أرجعه المصدر'):
                    st.dataframe(shares_history_df.sort_values(['رمز السهم','تاريخ عدد الأسهم']), use_container_width=True, hide_index=True)
                    st.download_button('⬇️ تنزيل سجل عدد الأسهم CSV', shares_history_df.to_csv(index=False).encode('utf-8-sig'), 'egx_share_count_history.csv', 'text/csv')

    with tab5:
        st.markdown('### مقارنة الأرقام بين المصادر')
        if statement_comparisons_df.empty:
            st.info('لم تُكتشف تعارضات رقمية قابلة للمقارنة في الفترات المشتركة، أو لم تتوفر بيانات متزامنة من المصدرين. هذا لا يثبت تطابق المصدرين.')
        else:
            st.warning('القيم المختلفة معروضة للمراجعة فقط. لا يختار التطبيق رقمًا تلقائيًا عند وجود تعارض.')
            st.dataframe(statement_comparisons_df, use_container_width=True, hide_index=True)
            st.download_button('⬇️ تنزيل مقارنة المصادر CSV', statement_comparisons_df.to_csv(index=False).encode('utf-8-sig'), 'egx_source_comparison.csv', 'text/csv')
        st.markdown('### روابط التحقق من أحدث الإفصاحات')
        link_rows = []
        for sym in summary_df['رمز السهم'].astype(str).str.replace('.CA','', regex=False).tolist():
            link_rows.append({'رمز السهم': sym+'.CA', 'البورصة المصرية — الأخبار والإفصاحات': 'https://beta.egx.com.eg/en',
                              'Mubasher — القوائم المالية': f'https://english.mubasher.info/markets/EGX/stocks/{sym}/financial-statements/',
                              'StockAnalysis — القوائم المالية': f'https://stockanalysis.com/quote/egx/{sym}/financials/'})
        links_df = pd.DataFrame(link_rows)
        st.dataframe(links_df, use_container_width=True, hide_index=True,
                     column_config={c: st.column_config.LinkColumn(c) for c in links_df.columns if c != 'رمز السهم'})
        st.caption('البورصة المصرية هي مرجع الإفصاح الرسمي. بعض صفحات المصادر الخارجية تعتمد على جداول تُحمّل ديناميكيًا؛ عند تعذر قراءتها آليًا، استخدم الرابط للتحقق اليدوي. لا تعتبر الخانة الفارغة صفرًا، ولا تعتبر حداثة الصفحة دليلًا وحده على صحة الرقم.')


    with tab6:
        st.markdown('### مؤشرات التحليل المالي — المرحلة الرابعة')
        st.info('المؤشرات تُحسب من أحدث فترتين سنويتين متاحتين. نمو الأرباح لا يُحسب كنسبة تقليدية إذا كانت الفترة السابقة صفرًا أو خسارة. جودة الأرباح = التدفق النقدي التشغيلي ÷ صافي الربح، وتُعرض فقط عندما يكون صافي الربح موجبًا. المؤشر والدرجة مبدئيان وليسا توصية شراء أو قيمة عادلة.')
        indicators_df = build_financial_indicators(summary_df, annual_df, quarterly_df)
        if indicators_df.empty:
            st.warning('لا توجد بيانات كافية لحساب المؤشرات. ابدأ جلب البيانات المالية أولًا.')
        else:
            ix1, ix2, ix3 = st.columns(3)
            ix1.metric('أسهم لها مؤشرات', int(indicators_df['درجة القوة المالية المبدئية /100'].notna().sum()))
            ix2.metric('أسهم ببيانات محدودة', int(indicators_df['حالة المؤشر'].str.contains('محدودة', na=False).sum()))
            ix3.metric('قطاعات مصنفة', int(indicators_df.loc[indicators_df['القطاع المبدئي'] != 'غير محدد','القطاع المبدئي'].nunique()))
            sector_filter = st.multiselect('تصفية حسب القطاع', sorted(indicators_df['القطاع المبدئي'].dropna().unique()), default=sorted(indicators_df['القطاع المبدئي'].dropna().unique()))
            view = indicators_df[indicators_df['القطاع المبدئي'].isin(sector_filter)].sort_values('درجة القوة المالية المبدئية /100', ascending=False, na_position='last')
            st.dataframe(view, use_container_width=True, hide_index=True,
                         column_config={
                             'نمو الإيرادات سنويًا %': st.column_config.NumberColumn(format='%.1f%%'),
                             'نمو صافي الربح سنويًا %': st.column_config.NumberColumn(format='%.1f%%'),
                             'هامش صافي الربح %': st.column_config.NumberColumn(format='%.2f%%'),
                             'ROE العائد على حقوق الملكية %': st.column_config.NumberColumn(format='%.2f%%'),
                             'ROA العائد على الأصول %': st.column_config.NumberColumn(format='%.2f%%'),
                             'درجة القوة المالية المبدئية /100': st.column_config.NumberColumn(format='%.1f'),
                             'تغطية البيانات الأساسية %': st.column_config.NumberColumn(format='%.1f%%'),
                         })
            st.download_button('⬇️ تنزيل مؤشرات التحليل المالي CSV', view.to_csv(index=False).encode('utf-8-sig'), 'egx_financial_indicators.csv', 'text/csv')
            with st.expander('منهجية الدرجة القطاعية المبدئية'):
                st.markdown("""- **البنوك:** وزن أعلى للعائد على حقوق الملكية ونمو الأرباح، ووزن أقل لهامش الربح، ولا تُستخدم نسبة الالتزامات/حقوق الملكية في الدرجة لأنها غير قابلة للمقارنة مباشرة مع الشركات غير المالية.
- **العقارات:** أوزان للنمو والربحية والعائد والرفع المالي والتدفقات النقدية.
- **الخدمات المالية غير المصرفية:** مزيج من النمو والعوائد وجودة الأرباح والرفع المالي.
- **الصناعة والأدوية وباقي القطاعات:** أوزان عامة أولية للنمو والربحية والعوائد والرفع المالي والتدفقات النقدية.
- القطاع المعيّن آليًا تقريبي ويحتاج مراجعة. لا تتوفر حاليًا كل مؤشرات القطاع المتخصصة (مثل NPL وCAR للبنوك أو مؤشرات التشغيل الخاصة بالعقارات)، لذلك لا تعتبر هذه الدرجة مقارنة مؤسسية نهائية.
- عند غياب أي مؤشر، لا يُعامل على أنه صفر؛ تُعاد موازنة أوزان المؤشرات المتاحة، وتظهر تغطية البيانات بوضوح.""")
