import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title='EGX Financial Analyzer V2', page_icon='📊', layout='wide')

# ============================================================
# V9 UNIVERSE: 248 entries -> 246 unique
# ============================================================
_RAW = '''COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN RUBX KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN LCSW MPCO ELSH MEPA ODIN EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH'''.split()
STOCKS = list(dict.fromkeys(x + '.CA' for x in _RAW))

# Manual sector overrides for EGX names. Yahoo is fallback for anything not here.
BANKS = set('COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB'.split())
FIN = set('EFIH BTFH VALU OFH CNFN MCQE ADCI ACAP FAIT AFDI UBEE FAITA AIFI AMIA AMII ATLC BINV DIFC'.split())
RE = set('PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD DCRC ARCC RMDA IDRE RREI EGREF EHDR MENA MPRC'.split())
HEALTH = set('BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH'.split())
TECH = set('ETEL MTIE RAYA EFIH UBEE DGTZ GOUR'.split())
ENERGY = set('AMOC SKPC EGAS TAQA MOIL GPIM EGAL ELSH MEPA'.split())
CONSUMER = set('DOMT EAST JUFO SUGR POUL OLFI AJWA MICH UEGC ISMA GOUR FERC'.split())
CONSTRUCTION = set('ORAS ENGC SVCE ARAB ELNA UPMS UNIT NCCW RACC PRCL AIDC'.split())
INDUSTRIAL = set('MFPC AMES INEG MBSC EGTS EGSA MHOT IFAP MPCI MOIN ISMQ AXPH CPCI SPIN KABO GSSC WCDF MFSC ACGC UEFM KZPC INFI ASCM ZEOT SMFR ETRS EDFM MILS GBCO ACTF SCTS FWRY SWDY AMOC ESRS CANA EXPA SUCE SMPP ALEX CRST GGRN GGCC IEEC NDRL EFIC TWSA ICLE MEGM EASB APSW MOED KWIN KORA SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI OBRI RKAZ SEIG SNFC TANM UTOP VERT WKOL LUTS ACRO DTPP EALR EBSC EOSB FIRE FNAR FTNS ICID KASABF KRDI LCSW MOSC OLFI SKPC AMER TALM ALUM ORWE ZMID AFMC SCEM GDWA ELEC IRON ATQA EGCH ALCN MPCO ODIN EDBM MOIL NIPH DSCW AALR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO COSG AMPI COPR'.split())

SECTOR_RULES = {
    'Banks': ['ROE','ROA','NIM','Cost/Income','NPL','NPL Coverage','CAR','Loan Growth','Deposit Growth','Net Income Growth','P/B','P/E','Dividend Yield'],
    'Real Estate': ['Revenue Growth','EBITDA Margin','Net Margin','ROE','Debt/Equity','Net Debt/EBITDA','Operating Cash Flow','FCF Margin','Cash/Assets','P/B','P/E'],
    'Healthcare': ['Revenue Growth','EPS Growth','Net Margin','EBITDA Margin','ROE','ROA','FCF Margin','Debt/Equity','Current Ratio','P/E','P/B'],
    'Telecom & Technology': ['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROIC','FCF Margin','Net Debt/EBITDA','ROE','P/E','EV/EBITDA','Dividend Yield'],
    'Energy & Petrochemicals': ['Revenue Growth','EBITDA Margin','Net Margin','ROIC','FCF Margin','Debt/Equity','Net Debt/EBITDA','ROE','P/E','EV/EBITDA','Dividend Yield'],
    'Consumer': ['Revenue Growth','EPS Growth','Gross Margin','EBITDA Margin','Net Margin','ROE','ROIC','FCF Margin','Debt/Equity','P/E','Dividend Yield'],
    'Construction & Engineering': ['Revenue Growth','EBITDA Margin','Net Margin','ROE','ROIC','Operating Cash Flow','FCF Margin','Debt/Equity','Net Debt/EBITDA','P/E','P/B'],
    'Industrial & Materials': ['Revenue Growth','EPS Growth','Gross Margin','EBITDA Margin','Net Margin','ROE','ROIC','FCF Margin','Debt/Equity','Net Debt/EBITDA','P/E','P/B','Dividend Yield'],
    'Financial Services': ['Revenue Growth','Net Income Growth','ROE','ROA','Net Margin','Debt/Equity','Current Ratio','P/E','P/B','Dividend Yield'],
    'General': ['Revenue Growth','EPS Growth','Net Margin','ROE','ROA','ROIC','FCF Margin','Debt/Equity','Current Ratio','P/E','P/B','Dividend Yield']
}
WEIGHTS = {k: {m:1/len(v) for m in v} for k,v in SECTOR_RULES.items()}
# More sensible weights for the bank engine.
WEIGHTS['Banks'] = {'ROE':.15,'ROA':.07,'NIM':.12,'Cost/Income':.10,'NPL':.10,'NPL Coverage':.07,'CAR':.10,'Loan Growth':.07,'Deposit Growth':.05,'Net Income Growth':.08,'P/B':.05,'P/E':.02,'Dividend Yield':.02}


def n(x):
    try:
        x=float(x); return x if np.isfinite(x) else np.nan
    except: return np.nan

def pct(x):
    x=n(x); return np.nan if pd.isna(x) else x*100

def last(s):
    if s is None: return np.nan
    s=pd.to_numeric(s,errors='coerce').dropna()
    return n(s.iloc[0]) if len(s) else np.nan

def growth(s):
    if s is None: return np.nan
    s=pd.to_numeric(s,errors='coerce').dropna()
    if len(s)<2 or s.iloc[-1]==0: return np.nan
    return (s.iloc[0]/s.iloc[-1]-1)*100

def find(df,names):
    if df is None or df.empty: return None
    for name in names:
        if name in df.index: return pd.to_numeric(df.loc[name],errors='coerce')
    low={str(i).lower():i for i in df.index}
    for name in names:
        for k,orig in low.items():
            if name.lower() in k or k in name.lower(): return pd.to_numeric(df.loc[orig],errors='coerce')
    return None

def sector(sym,info):
    s=sym.replace('.CA','')
    if s in BANKS:return 'Banks'
    if s in RE:return 'Real Estate'
    if s in HEALTH:return 'Healthcare'
    if s in TECH:return 'Telecom & Technology'
    if s in ENERGY:return 'Energy & Petrochemicals'
    if s in CONSUMER:return 'Consumer'
    if s in CONSTRUCTION:return 'Construction & Engineering'
    if s in FIN:return 'Financial Services'
    if s in INDUSTRIAL:return 'Industrial & Materials'
    t=(str(info.get('sector',''))+' '+str(info.get('industry',''))).lower()
    if 'bank' in t:return 'Banks'
    if 'real estate' in t or 'reit' in t:return 'Real Estate'
    if any(x in t for x in ['health','medical','pharma']):return 'Healthcare'
    if any(x in t for x in ['telecom','software','technology','internet']):return 'Telecom & Technology'
    if any(x in t for x in ['oil','gas','energy','petro']):return 'Energy & Petrochemicals'
    if any(x in t for x in ['consumer','food','beverage','retail']):return 'Consumer'
    if any(x in t for x in ['construction','engineering']):return 'Construction & Engineering'
    if any(x in t for x in ['financial','insurance','investment']):return 'Financial Services'
    return 'General'

def extract(info,inc,bal,cf,sec):
    rev=find(inc,['Total Revenue','Operating Revenue','Revenue']); ni=find(inc,['Net Income','Net Income Common Stockholders']); eps=find(inc,['Diluted EPS','Basic EPS'])
    gross=find(inc,['Gross Profit']); ebit=find(inc,['EBIT','Operating Income']); ebitda=find(inc,['EBITDA','Normalized EBITDA']); nii=find(inc,['Net Interest Income']); opex=find(inc,['Operating Expense','Operating Expenses','Total Operating Expenses'])
    assets=find(bal,['Total Assets']); equity=find(bal,['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity']); debt=find(bal,['Total Debt','Long Term Debt And Capital Lease Obligation','Long Term Debt']); cash=find(bal,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial'])
    ca=find(bal,['Current Assets']); cl=find(bal,['Current Liabilities']); loans=find(bal,['Net Loan And Lease Receivables','Loans Receivable','Net Loans']); deposits=find(bal,['Deposits','Total Deposits']); nplrow=find(bal,['Non Performing Assets','Nonperforming Loans','Non Performing Loans']); allowance=find(bal,['Allowance For Credit Losses','Credit Losses'])
    ocf=find(cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex=find(cf,['Capital Expenditure','Capital Expenditures'])
    R,NI,EQ,AS,D,C,O,E,I,EB,EBIT=map(last,[rev,ni,equity,assets,debt,cash,ocf,capex,nii,ebitda,ebit])
    fcf=np.nan if pd.isna(O) or pd.isna(E) else O+E if E<0 else O-E
    mcap=n(info.get('marketCap')); price=n(info.get('currentPrice'))
    pe=n(info.get('trailingPE')); pb=n(info.get('priceToBook')); ev_ebitda=n(info.get('enterpriseToEbitda')); dy=pct(info.get('dividendYield'))
    roe=pct(info.get('returnOnEquity')); roa=pct(info.get('returnOnAssets')); margin=pct(info.get('profitMargins')); gm=pct(info.get('grossMargins')); de=n(info.get('debtToEquity')); cr=n(info.get('currentRatio'))
    if pd.isna(roe) and pd.notna(NI) and pd.notna(EQ) and EQ: roe=NI/EQ*100
    if pd.isna(roa) and pd.notna(NI) and pd.notna(AS) and AS: roa=NI/AS*100
    if pd.isna(margin) and pd.notna(NI) and pd.notna(R) and R: margin=NI/R*100
    if pd.isna(gm) and pd.notna(last(gross)) and R: gm=last(gross)/R*100
    if pd.isna(de) and pd.notna(D) and pd.notna(EQ) and EQ: de=D/EQ*100
    if pd.isna(cr) and pd.notna(last(ca)) and pd.notna(last(cl)) and last(cl): cr=last(ca)/last(cl)
    em=np.nan if pd.isna(EB) or pd.isna(R) or not R else EB/R*100
    fcfm=np.nan if pd.isna(fcf) or pd.isna(R) or not R else fcf/R*100
    nde=np.nan if pd.isna(D) or pd.isna(C) or pd.isna(EB) or not EB else (D-C)/EB
    cashassets=np.nan if pd.isna(C) or pd.isna(AS) or not AS else C/AS*100
    roic=np.nan if pd.isna(EBIT) or pd.isna(D) or pd.isna(EQ) else EBIT/(D+EQ-(C if pd.notna(C) else 0))*100
    nim=np.nan if pd.isna(I) or pd.isna(AS) or not AS else I/AS*100
    ci=np.nan if pd.isna(last(opex)) or pd.isna(I) or not I else abs(last(opex))/abs(I)*100
    npl=np.nan if pd.isna(last(nplrow)) or pd.isna(last(loans)) or not last(loans) else last(nplrow)/last(loans)*100
    nplcov=np.nan if pd.isna(last(allowance)) or pd.isna(last(nplrow)) or not last(nplrow) else last(allowance)/last(nplrow)*100
    car=n(info.get('capitalAdequacyRatio'))
    return {'Revenue Growth':growth(rev),'Net Income Growth':growth(ni),'EPS Growth':growth(eps),'Gross Margin':gm,'EBITDA Margin':em,'Net Margin':margin,'ROE':roe,'ROA':roa,'ROIC':roic,'FCF Margin':fcfm,'Operating Cash Flow':O,'Debt/Equity':de,'Net Debt/EBITDA':nde,'Current Ratio':cr,'Cash/Assets':cashassets,'P/E':pe,'P/B':pb,'EV/EBITDA':ev_ebitda,'Dividend Yield':dy,'NIM':nim,'Cost/Income':ci,'NPL':npl,'NPL Coverage':nplcov,'CAR':car,'Loan Growth':growth(loans),'Deposit Growth':growth(deposits),'_price':price,'_mcap':mcap}

def score_metric(m,x):
    x=n(x)
    if pd.isna(x):return np.nan
    if m in ['Revenue Growth','Net Income Growth','EPS Growth','Loan Growth','Deposit Growth']:return np.clip(50+x*1.5,0,100)
    if m=='ROE':return np.clip(x*3,0,100)
    if m=='ROA':return np.clip(x*15,0,100)
    if m=='ROIC':return np.clip(x*3,0,100)
    if m in ['Gross Margin','EBITDA Margin','Net Margin','FCF Margin']:return np.clip(x*2,0,100)
    if m=='NIM':return np.clip(x*12,0,100)
    if m=='NPL Coverage':return np.clip(x/1.5,0,100)
    if m=='CAR':return np.clip((x-5)*6,0,100)
    if m=='Current Ratio':return np.clip(x*50,0,100)
    if m=='Cash/Assets':return np.clip(x*2.5,0,100)
    if m=='Dividend Yield':return np.clip(x*12,0,100)
    if m=='Debt/Equity':return np.clip(100-max(x,0)*.7,0,100)
    if m=='Net Debt/EBITDA':return np.clip(100-max(x,0)*18,0,100)
    if m=='Cost/Income':return np.clip(100-x*1.25,0,100)
    if m=='NPL':return np.clip(100-x*10,0,100)
    if m=='P/E':return np.nan if x<=0 else np.clip(100-abs(x-12)*4,0,100)
    if m=='P/B':return np.nan if x<=0 else np.clip(100-abs(x-1.4)*35,0,100)
    if m=='EV/EBITDA':return np.nan if x<=0 else np.clip(100-abs(x-8)*5,0,100)
    return np.nan

def analyze(sym):
    t=yf.Ticker(sym)
    try: info=t.info or {}
    except: info={}
    try: inc=t.financials
    except: inc=pd.DataFrame()
    try: bal=t.balance_sheet
    except: bal=pd.DataFrame()
    try: cf=t.cashflow
    except: cf=pd.DataFrame()

    # توزيعات الأرباح: نستخدم تاريخ توزيعات Yahoo كطبقة سوقية، ونحسب TTM و3 سنوات.
    dividends = pd.Series(dtype=float)
    try:
        dividends = t.dividends
        if dividends is None: dividends = pd.Series(dtype=float)
        dividends = pd.to_numeric(dividends, errors='coerce').dropna()
    except Exception:
        dividends = pd.Series(dtype=float)
    today = pd.Timestamp.utcnow().tz_localize(None)
    ttm_start = today - pd.Timedelta(days=365)
    three_y_start = today - pd.Timedelta(days=365*3)
    div_ttm = float(dividends[dividends.index.tz_localize(None) >= ttm_start].sum()) if len(dividends) else np.nan
    div_3y = float(dividends[dividends.index.tz_localize(None) >= three_y_start].sum()) if len(dividends) else np.nan
    last_div = float(dividends.iloc[-1]) if len(dividends) else np.nan
    last_div_date = dividends.index[-1].date().isoformat() if len(dividends) else ''

    sec=sector(sym,info); met=extract(info,inc,bal,cf,sec);
    if pd.isna(met.get('Dividend Yield')) and pd.notna(div_ttm) and pd.notna(met.get('_price')) and met.get('_price') > 0:
        met['Dividend Yield'] = div_ttm / met['_price'] * 100
    met.update({'Dividend TTM': div_ttm, 'Dividend 3Y': div_3y, 'Last Dividend': last_div, 'Last Dividend Date': last_div_date, 'Dividend Data Source': 'Yahoo Finance / yfinance'})

    # اكتمال البيانات الأساسية: لا نعاقب السهم على غياب مؤشر غير مناسب لقطاعه.
    core_fields = ['Revenue Growth','Net Income Growth','EPS Growth','ROE','ROA','Net Margin','Debt/Equity','P/E','P/B','Dividend Yield','Operating Cash Flow','_price','_mcap']
    available_core = sum(pd.notna(met.get(x)) for x in core_fields)
    completeness = available_core / len(core_fields) * 100
    met['Data Completeness'] = completeness
    fields=SECTOR_RULES[sec]; w=WEIGHTS[sec]
    vals=[(score_metric(m,met.get(m)),w[m]) for m in fields if pd.notna(score_metric(m,met.get(m)))]
    raw=sum(v*ww for v,ww in vals)/sum(ww for _,ww in vals) if vals else np.nan
    coverage=sum(w[m] for m in fields if pd.notna(met.get(m)))/sum(w.values())*100
    final=raw*(.55+.45*coverage/100) if pd.notna(raw) else np.nan
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'industry':info.get('industry',''),'score':final,'raw':raw,'coverage':coverage,'completeness':completeness,'metrics':met}

@st.cache_data(ttl=3600,show_spinner=False)
def run_all():
    out=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        fs={ex.submit(analyze,s):s for s in STOCKS}
        for f in as_completed(fs):
            try:out.append(f.result())
            except Exception as e:out.append({'symbol':fs[f],'name':fs[f],'sector':'General','industry':'','score':np.nan,'raw':np.nan,'coverage':0,'completeness':0,'metrics':{}})
    return out

st.title('📊 EGX Financial Analyzer V2')
st.caption(f'Sector-Aware Fundamental Engine — {len(STOCKS)} سهم فريد من Universe V9')
with st.sidebar:
    st.header('⚙️ الفلاتر')
    sectors=st.multiselect('القطاعات',list(SECTOR_RULES),default=list(SECTOR_RULES))
    mincov=st.slider('Minimum Data Coverage %',0,100,40,5)
    if st.button('🔄 تحديث البيانات'):
        run_all.clear(); st.rerun()

with st.spinner('جاري تحميل القوائم المالية وتحليل الأسهم...'):
    results=run_all()

rows=[]
for r in results:
    if r['sector'] in sectors and r['coverage']>=mincov:
        m=r['metrics']; rows.append({'Rank':0,'السهم':r['symbol'],'الشركة':r['name'],'القطاع':r['sector'],'Financial Score':r['score'],'Data Coverage %':r['coverage'],'نسبة اكتمال البيانات %':r.get('completeness',0),'Revenue Growth %':m.get('Revenue Growth',np.nan),'Net Income Growth %':m.get('Net Income Growth',np.nan),'EPS Growth %':m.get('EPS Growth',np.nan),'ROE %':m.get('ROE',np.nan),'ROIC %':m.get('ROIC',np.nan),'Net Margin %':m.get('Net Margin',np.nan),'P/E':m.get('P/E',np.nan),'P/B':m.get('P/B',np.nan),'Dividend Yield %':m.get('Dividend Yield',np.nan),'توزيعات آخر 12 شهر':m.get('Dividend TTM',np.nan),'توزيعات 3 سنوات':m.get('Dividend 3Y',np.nan)})
df=pd.DataFrame(rows)
if not df.empty:
    df=df.sort_values('Financial Score',ascending=False,na_position='last').reset_index(drop=True); df['Rank']=np.arange(1,len(df)+1)
st.subheader('🏆 الترتيب المالي')
if df.empty: st.warning('لا توجد نتائج حسب الفلاتر.')
else: st.dataframe(df.style.format({c:'{:.1f}' for c in df.columns if c not in ['Rank','السهم','الشركة','القطاع']},na_rep='—'),use_container_width=True,hide_index=True)

st.subheader('🏭 ملخص القطاعات')
srows=[]
for sec in SECTOR_RULES:
    rr=[r for r in results if r['sector']==sec and r['coverage']>=mincov and pd.notna(r['score'])]
    if rr:srows.append({'القطاع':sec,'عدد الأسهم':len(rr),'متوسط Score':np.mean([r['score'] for r in rr]),'متوسط Coverage':np.mean([r['coverage'] for r in rr]),'متوسط اكتمال البيانات':np.mean([r.get('completeness',0) for r in rr])})
if srows:st.dataframe(pd.DataFrame(srows).style.format({'متوسط Score':'{:.1f}','متوسط Coverage':'{:.0f}','متوسط اكتمال البيانات':'{:.0f}'}),use_container_width=True,hide_index=True)

st.subheader('🔎 تحليل سهم بالتفصيل')
syms=[r['symbol'] for r in results]
if syms:
    sel=st.selectbox('السهم',sorted(syms)); r=next(x for x in results if x['symbol']==sel); m=r['metrics']; fields=SECTOR_RULES[r['sector']]
    a,b,c,d=st.columns(4); a.metric('Financial Score','—' if pd.isna(r['score']) else f"{r['score']:.1f}"); b.metric('Raw Score','—' if pd.isna(r['raw']) else f"{r['raw']:.1f}"); c.metric('Data Coverage',f"{r['coverage']:.0f}%"); d.metric('السعر', '—' if pd.isna(m.get('_price')) else f"{m['_price']:.2f} EGP")
    st.write(f"**القطاع:** {r['sector']} | **الصناعة:** {r['industry'] or 'غير متاحة'} | **اكتمال البيانات:** {r.get('completeness',0):.0f}%")
    st.write(f"**توزيعات آخر 12 شهر:** {m.get('Dividend TTM',np.nan):.2f} | **توزيعات آخر 3 سنوات:** {m.get('Dividend 3Y',np.nan):.2f} | **آخر توزيع:** {m.get('Last Dividend',np.nan):.2f} ({m.get('Last Dividend Date') or 'غير متاح'}) | **مصدر التوزيعات:** {m.get('Dividend Data Source','غير متاح')}")
    detail=[]
    for x in fields: detail.append({'المؤشر':x,'القيمة':m.get(x,np.nan),'Score':score_metric(x,m.get(x)),'متاح':'✅' if pd.notna(m.get(x)) else '❌'})
    st.dataframe(pd.DataFrame(detail).style.format({'القيمة':'{:.2f}','Score':'{:.1f}'},na_rep='—'),use_container_width=True,hide_index=True)

st.divider(); st.info('الـScore لا يعامل البيانات الناقصة كصفر ولا يسمح بتقييم مرتفع مع تغطية منخفضة. مؤشرات البنوك مختلفة عن العقار والصناعة والطاقة والرعاية الصحية والاتصالات والخدمات المالية.')
