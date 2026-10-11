import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests, re, html
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="EGX BVPS + Daily Close", page_icon="📊", layout="wide")
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

def analyze_symbol(symbol):
    y=yahoo_data(symbol)
    m=mubasher_bvps(symbol)
    s=stockanalysis_bvps(symbol)
    # الأولوية للقيمة المباشرة من مباشر ثم StockAnalysis ثم Yahoo/حساب حقوق الملكية.
    options=[m,s,y]
    chosen=next((x for x in options if np.isfinite(x.get('bvps',np.nan)) and x.get('bvps',np.nan)>0),None)
    if chosen:
        bvps=float(chosen['bvps']); source=chosen.get('source','')
        status='متاحة'
    else:
        bvps=np.nan; source=''; status='غير متاحة'
    return {'رمز السهم':symbol+'.CA','السعر من آخر إغلاق يومي (جنيه)':y['price'],
            'تاريخ شمعة السعر':y['price_date'],'القيمة الدفترية للسهم (جنيه)':bvps,
            'مصدر القيمة الدفترية':source,'تاريخ القوائم المالية المتاح':y.get('period',''),
            'حالة القيمة الدفترية':status,
            'رابط مباشر':m.get('url',''),'رابط StockAnalysis':s.get('url','')}

st.title('📊 الأسهم المصرية — السعر اليومي والقيمة الدفترية فقط')
st.caption('المخرجات مقتصرة على آخر إغلاق يومي والقيمة الدفترية للسهم ومصدرها. لا يتم حساب قيمة عادلة أو مؤشرات فنية.')
with st.expander('مصادر القيمة الدفترية المستخدمة',expanded=True):
    st.markdown('''- **Mubasher**: صفحة السهم، مع تجربة النطاق الحالي والقديم.
- **StockAnalysis**: صفحة السهم في قائمة EGX.
- **Yahoo Finance**: قيمة Book Value إن توفرت، وإلا محاولة اشتقاقها من حقوق الملكية ÷ الأسهم القائمة.
- لو المصدر مش بيرجع قيمة موثوقة، الخانة تفضل غير متاحة بدل اختراع رقم.''')
if st.button('🔄 جلب / تحديث البيانات',type='primary'):
    st.cache_data.clear()
    st.rerun()

symbols=get_universe()
st.info(f'عدد الرموز الفريدة داخل قائمة البرنامج: {len(symbols)} — القائمة تشمل الرموز الثابتة ومحاولة اكتشاف رموز إضافية.')
workers=st.slider('عدد عمليات الجلب المتوازية',1,12,6)
if st.button('▶️ ابدأ جلب السعر والقيمة الدفترية'):
    rows=[]; progress=st.progress(0); status=st.empty()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(analyze_symbol,s):s for s in symbols}
        total=len(futures)
        for i,f in enumerate(as_completed(futures),1):
            sym=futures[f]
            try: rows.append(f.result())
            except Exception as e:
                rows.append({'رمز السهم':sym+'.CA','السعر من آخر إغلاق يومي (جنيه)':np.nan,'تاريخ شمعة السعر':'','القيمة الدفترية للسهم (جنيه)':np.nan,'مصدر القيمة الدفترية':'','تاريخ القوائم المالية المتاح':'','حالة القيمة الدفترية':'خطأ في الجلب','رابط مباشر':'','رابط StockAnalysis':''})
            progress.progress(i/max(total,1)); status.text(f'تم فحص {i} من {total}: {sym}')
    df=pd.DataFrame(rows).sort_values('رمز السهم').reset_index(drop=True)
    st.session_state['results']=df

if 'results' in st.session_state:
    df=st.session_state['results']
    c1,c2,c3=st.columns(3)
    c1.metric('إجمالي الرموز',len(df))
    c2.metric('أسعار يومية متاحة',int(df['السعر من آخر إغلاق يومي (جنيه)'].notna().sum()))
    c3.metric('قيم دفترية متاحة',int(df['القيمة الدفترية للسهم (جنيه)'].notna().sum()))
    st.dataframe(df,use_container_width=True,hide_index=True,
                 column_config={'رابط مباشر':st.column_config.LinkColumn('رابط مباشر'),'رابط StockAnalysis':st.column_config.LinkColumn('رابط StockAnalysis')})
    st.download_button('⬇️ تنزيل CSV',df.to_csv(index=False).encode('utf-8-sig'),'egx_price_bvps.csv','text/csv')
