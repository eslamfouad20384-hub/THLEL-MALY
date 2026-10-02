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
    sec=sector(sym,info); met=extract(info,inc,bal,cf,sec); fields=SECTOR_RULES[sec]; w=WEIGHTS[sec]
    vals=[(score_metric(m,met.get(m)),w[m]) for m in fields if pd.notna(score_metric(m,met.get(m)))]
    raw=sum(v*ww for v,ww in vals)/sum(ww for _,ww in vals) if vals else np.nan
    coverage=sum(w[m] for m in fields if pd.notna(met.get(m)))/sum(w.values())*100
    final=raw*(.55+.45*coverage/100) if pd.notna(raw) else np.nan
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'industry':info.get('industry',''),'score':final,'raw':raw,'coverage':coverage,'metrics':met}

@st.cache_data(ttl=3600,show_spinner=False)
def run_all():
    out=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        fs={ex.submit(analyze,s):s for s in STOCKS}
        for f in as_completed(fs):
            try:out.append(f.result())
            except Exception as e:out.append({'symbol':fs[f],'name':fs[f],'sector':'General','industry':'','score':np.nan,'raw':np.nan,'coverage':0,'metrics':{}})
    return out

def technical(df):
    if df is None or df.empty: return {}
    d=df.copy(); d.columns=[str(c).title() for c in d.columns]
    if 'Close' not in d.columns or len(d)<60: return {}
    close=pd.to_numeric(d['Close'],errors='coerce').dropna()
    if len(close)<60: return {}
    vol=pd.to_numeric(d.get('Volume',pd.Series(index=close.index)),errors='coerce').reindex(close.index)
    ema20=close.ewm(span=20,adjust=False).mean(); ema50=close.ewm(span=50,adjust=False).mean(); ema200=close.ewm(span=200,adjust=False).mean()
    delta=close.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean(); loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean(); rsi=100-(100/(1+gain/loss.replace(0,np.nan)))
    macd=close.ewm(span=12,adjust=False).mean()-close.ewm(span=26,adjust=False).mean(); signal=macd.ewm(span=9,adjust=False).mean()
    high=pd.to_numeric(d['High'],errors='coerce'); low=pd.to_numeric(d['Low'],errors='coerce')
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(14).mean()
    vma=vol.rolling(20).mean(); vr=vol.iloc[-1]/vma.iloc[-1] if pd.notna(vma.iloc[-1]) and vma.iloc[-1] else np.nan
    c=float(close.iloc[-1]); e20=float(ema20.iloc[-1]); e50=float(ema50.iloc[-1]); e200=float(ema200.iloc[-1]) if pd.notna(ema200.iloc[-1]) else np.nan
    flags=[c>e20,c>e50,(c>e200 if pd.notna(e200) else False),rsi.iloc[-1]>50,macd.iloc[-1]>signal.iloc[-1],(vr>=1 if pd.notna(vr) else False)]
    score=sum(flags)/len(flags)*100
    trend='صاعد قوي' if c>e20>e50 and (pd.isna(e200) or e50>e200) else 'صاعد' if c>e20 and e20>e50 else 'هابط قوي' if c<e20<e50 else 'محايد'
    return {'Technical Score':score,'Trend':trend,'RSI':float(rsi.iloc[-1]),'MACD':float(macd.iloc[-1]),'MACD Signal':float(signal.iloc[-1]),'ATR %':float(atr.iloc[-1]/c*100) if pd.notna(atr.iloc[-1]) else np.nan,'Volume Ratio':float(vr) if pd.notna(vr) else np.nan,'Distance EMA200 %':float((c/e200-1)*100) if pd.notna(e200) and e200 else np.nan,'Support':float(close.tail(20).min()),'Resistance':float(close.tail(20).max()),'52W High':float(close.tail(252).max()),'52W Low':float(close.tail(252).min()),'Price':c,'Last Date':close.index[-1].strftime('%Y-%m-%d')}

def valuation(m,price,sec):
    if pd.isna(price) or price<=0: return {}
    eps=n(m.get('_eps')); eq=n(m.get('_equity')); fcf=n(m.get('_fcf')); mcap=n(m.get('_mcap')); shares=mcap/price if pd.notna(mcap) else np.nan
    vals=[]
    if pd.notna(eps) and eps>0: vals.append(eps*(10 if sec in ['Banks','Financial Services'] else 12))
    if pd.notna(eq) and pd.notna(shares) and shares>0: vals.append((eq/shares)*(1.3 if sec=='Banks' else 1.5))
    if pd.notna(fcf) and fcf>0 and pd.notna(shares) and shares>0: vals.append((fcf/shares)*10)
    if not vals: return {}
    lo=float(np.percentile(vals,25)); hi=float(np.percentile(vals,75)); mid=(lo+hi)/2
    return {'Fair Low':lo,'Fair Mid':mid,'Fair High':hi,'Upside %':(mid/price-1)*100,'MOS Buy':mid*.80,'Strong Buy':mid*.70}

def dividend_data(t,price):
    try:
        s=pd.to_numeric(t.dividends,errors='coerce').dropna(); s=s[s>0]
        if s.empty: return {'Dividend 12M':np.nan,'Dividend Yield %':np.nan,'Last Dividend':np.nan,'Last Dividend Date':'—','Dividend Count 3Y':0}
        now=pd.Timestamp.now(tz=s.index.tz) if getattr(s.index,'tz',None) else pd.Timestamp.now()
        d12=s[s.index>=now-pd.Timedelta(days=365)]
        d3=s[s.index>=now-pd.Timedelta(days=1095)]
        total=float(d12.sum()); last=float(s.iloc[-1])
        return {'Dividend 12M':total,'Dividend Yield %':total/price*100 if price else np.nan,'Last Dividend':last,'Last Dividend Date':s.index[-1].strftime('%Y-%m-%d'),'Dividend Count 3Y':len(d3)}
    except Exception: return {'Dividend 12M':np.nan,'Dividend Yield %':np.nan,'Last Dividend':np.nan,'Last Dividend Date':'—','Dividend Count 3Y':0}

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
    sec=sector(sym,info); met=extract(info,inc,bal,cf,sec); fields=SECTOR_RULES[sec]; w=WEIGHTS[sec]
    vals=[(score_metric(m,met.get(m)),w[m]) for m in fields if pd.notna(score_metric(m,met.get(m)))]
    raw=sum(v*ww for v,ww in vals)/sum(ww for _,ww in vals) if vals else np.nan
    coverage=sum(w[m] for m in fields if pd.notna(met.get(m)))/sum(w.values())*100
    try:
        h=t.history(period='5d',interval='1d',auto_adjust=False); price=float(h['Close'].dropna().iloc[-1]); lastdate=h['Close'].dropna().index[-1].strftime('%Y-%m-%d')
    except Exception: price=n(info.get('currentPrice')); lastdate='—'
    div=dividend_data(t,price); met['Dividend Yield']=div['Dividend Yield %']; met['_price']=price
    fair=valuation(met,price,sec)
    final=raw*(.55+.45*coverage/100) if pd.notna(raw) else np.nan
    quality=100 if coverage>=85 else 85 if coverage>=70 else 65 if coverage>=50 else 40
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'industry':info.get('industry',''),'score':final,'raw':raw,'coverage':coverage,'quality':quality,'metrics':met,'valuation':fair,'dividend':div,'lastdate':lastdate}

@st.cache_data(ttl=3600,show_spinner=False)
def run_market():
    try: return yf.download(STOCKS,period='2y',interval='1d',group_by='ticker',auto_adjust=False,threads=True,progress=False)
    except Exception: return pd.DataFrame()

def get_hist(market,sym):
    try:
        if isinstance(market.columns,pd.MultiIndex):
            if sym in market.columns.get_level_values(0): return market[sym].dropna(how='all')
            if sym in market.columns.get_level_values(1): return market.xs(sym,axis=1,level=1).dropna(how='all')
        return market
    except: return pd.DataFrame()

st.title('📊 EGX Financial Analyzer V4 PRO')
st.caption(f'Fundamental + Valuation + Dividends + Technical | {len(STOCKS)} سهم فريد | آخر إغلاق يومي + تاريخ الشمعة')
with st.sidebar:
    st.header('⚙️ الإعدادات')
    sectors=st.multiselect('القطاعات',list(SECTOR_RULES),default=list(SECTOR_RULES))
    mincov=st.slider('حد اكتمال البيانات %',0,100,50,5)
    minscore=st.slider('الحد الأدنى للدرجة',0,100,0,5)
    if st.button('🔄 تحديث البيانات'):
        run_all.clear(); run_market.clear(); st.rerun()
with st.spinner('جاري تحليل القوائم المالية والسوق...'):
    results=run_all(); market=run_market()
tech={r['symbol']:technical(get_hist(market,r['symbol'])) for r in results}
rows=[]
for r in results:
    if r['sector'] not in sectors or r['coverage']<mincov or (pd.notna(r['score']) and r['score']<minscore): continue
    m=r['metrics']; v=r['valuation']; d=r['dividend']; tt=tech.get(r['symbol'],{}); fs=n(r['score']); ts=n(tt.get('Technical Score')); final=fs*.65+ts*.35 if pd.notna(fs) and pd.notna(ts) else fs
    rows.append({'Rank':0,'السهم':r['symbol'].replace('.CA',''),'الشركة':r['name'],'القطاع':r['sector'],'المالي':fs,'الفني':ts,'النهائي':final,'السعر الحالي':n(tt.get('Price',m.get('_price'))),'القيمة العادلة':v.get('Fair Mid',np.nan),'الصعود المحتمل %':v.get('Upside %',np.nan),'شراء قوي':v.get('Strong Buy',np.nan),'عائد التوزيع %':d.get('Dividend Yield %',np.nan),'اكتمال البيانات %':r['coverage'],'جودة البيانات':r['quality'],'الاتجاه':tt.get('Trend','—'),'آخر شمعة':tt.get('Last Date',r['lastdate'])})
df=pd.DataFrame(rows)
if not df.empty:
    df=df.sort_values(['النهائي','المالي'],ascending=False,na_position='last').reset_index(drop=True); df['Rank']=np.arange(1,len(df)+1)
st.subheader('🏆 الترتيب الاحترافي')
if df.empty: st.warning('لا توجد نتائج وفق الفلاتر الحالية.')
else:
    st.dataframe(df.style.format({c:'{:.1f}' for c in df.columns if c not in ['Rank','السهم','الشركة','القطاع','الاتجاه','آخر شمعة','جودة البيانات']},na_rep='—'),use_container_width=True,hide_index=True)
    st.download_button('⬇️ تنزيل CSV',df.to_csv(index=False,encoding='utf-8-sig').encode('utf-8-sig'),'EGX_V4_PRO.csv','text/csv')
st.subheader('🏭 تحليل القطاعات')
srows=[]
for sec in SECTOR_RULES:
    rr=[x for x in results if x['sector']==sec and x['coverage']>=mincov and pd.notna(x['score'])]
    if rr:srows.append({'القطاع':sec,'عدد الأسهم':len(rr),'متوسط المالي':np.mean([x['score'] for x in rr]),'متوسط الاكتمال':np.mean([x['coverage'] for x in rr]),'متوسط الجودة':np.mean([x['quality'] for x in rr])})
if srows: st.dataframe(pd.DataFrame(srows).style.format({'متوسط المالي':'{:.1f}','متوسط الاكتمال':'{:.0f}','متوسط الجودة':'{:.0f}'}),use_container_width=True,hide_index=True)
st.subheader('🔎 تقرير سهم كامل')
if results:
    sel=st.selectbox('السهم',sorted([r['symbol'] for r in results]),format_func=lambda x:x.replace('.CA','')); r=next(x for x in results if x['symbol']==sel); m=r['metrics']; v=r['valuation']; d=r['dividend']; tt=tech.get(sel,{})
    fs=n(r['score']); ts=n(tt.get('Technical Score')); final=fs*.65+ts*.35 if pd.notna(fs) and pd.notna(ts) else fs; price=n(tt.get('Price',m.get('_price')))
    a,b,c,e,f,g=st.columns(6); a.metric('المالي','—' if pd.isna(fs) else f'{fs:.1f}'); b.metric('الفني','—' if pd.isna(ts) else f'{ts:.1f}'); c.metric('النهائي','—' if pd.isna(final) else f'{final:.1f}'); e.metric('السعر','—' if pd.isna(price) else f'{price:.2f} EGP'); f.metric('القيمة العادلة','—' if pd.isna(v.get('Fair Mid',np.nan)) else f"{v['Fair Mid']:.2f}"); g.metric('اكتمال البيانات',f"{r['coverage']:.0f}%")
    st.write(f"**{r['name']}** | **القطاع:** {r['sector']} | **الصناعة:** {r['industry'] or 'غير متاحة'} | **آخر شمعة:** {tt.get('Last Date',r['lastdate'])}")
    st.markdown('### 💰 القيمة العادلة وسعر الشراء')
    val=pd.DataFrame([{'المؤشر':'القيمة العادلة الدنيا','القيمة':v.get('Fair Low',np.nan)},{'المؤشر':'القيمة العادلة الوسطى','القيمة':v.get('Fair Mid',np.nan)},{'المؤشر':'القيمة العادلة العليا','القيمة':v.get('Fair High',np.nan)},{'المؤشر':'الصعود المحتمل %','القيمة':v.get('Upside %',np.nan)},{'المؤشر':'شراء بهامش أمان 20%','القيمة':v.get('MOS Buy',np.nan)},{'المؤشر':'شراء قوي بهامش أمان 30%','القيمة':v.get('Strong Buy',np.nan)}]); st.dataframe(val.style.format({'القيمة':'{:.2f}'},na_rep='—'),use_container_width=True,hide_index=True)
    st.markdown('### 💵 التوزيعات')
    dv=pd.DataFrame([{'آخر توزيعة':d.get('Last Dividend',np.nan),'تاريخ آخر توزيعة':d.get('Last Dividend Date','—'),'توزيعات 12 شهر':d.get('Dividend 12M',np.nan),'عائد التوزيع %':d.get('Dividend Yield %',np.nan),'عدد توزيعات 3 سنوات':d.get('Dividend Count 3Y',0)}]); st.dataframe(dv.style.format({'آخر توزيعة':'{:.3f}','توزيعات 12 شهر':'{:.3f}','عائد التوزيع %':'{:.2f}'},na_rep='—'),use_container_width=True,hide_index=True)
    st.markdown('### 📈 التحليل الفني')
    st.dataframe(pd.DataFrame([{'المؤشر':k,'القيمة':val} for k,val in tt.items() if k!='Technical Score']),use_container_width=True,hide_index=True)
    st.markdown('### 📊 المؤشرات المالية')
    fields=SECTOR_RULES[r['sector']]; detail=[{'المؤشر':x,'القيمة':m.get(x,np.nan),'Score':score_metric(x,m.get(x)),'متاح':'✅' if pd.notna(m.get(x)) else '❌'} for x in fields]; st.dataframe(pd.DataFrame(detail).style.format({'القيمة':'{:.2f}','Score':'{:.1f}'},na_rep='—'),use_container_width=True,hide_index=True)
    st.markdown('### 🎯 أهداف 3 سنوات — 3 سيناريوهات')
    eps=n(m.get('_eps')); gg=n(m.get('EPS Growth'))
    if pd.notna(price) and pd.notna(eps) and eps>0:
        g=max(0,min(30,0 if pd.isna(gg) else gg)); scenarios=[]
        for name,gr,pe in [('محافظ',max(0,g-8),9),('أساسي',g,12),('متفائل',min(35,g+8),15)]: scenarios.append({'السيناريو':name,'نمو EPS سنوي %':gr,'P/E':pe,'هدف 3 سنوات':eps*((1+gr/100)**3)*pe})
        st.dataframe(pd.DataFrame(scenarios).style.format({'نمو EPS سنوي %':'{:.1f}','P/E':'{:.1f}','هدف 3 سنوات':'{:.2f}'}),use_container_width=True,hide_index=True)
    else: st.info('لا توجد بيانات EPS كافية لبناء أهداف 3 سنوات كمية.')
    st.markdown('### 🧪 جودة البيانات')
    st.progress(min(max(r['coverage']/100,0),1),text=f"اكتمال البيانات: {r['coverage']:.0f}% | جودة: {r['quality']}/100")
    st.caption('القيمة العادلة والأهداف نماذج تقديرية وليست ضمانًا. Yahoo/yfinance قد يفتقد أو يؤخر بعض بيانات EGX، لذلك يظهر اكتمال البيانات وتاريخ آخر شمعة.')
st.divider(); st.info('V4 PRO يحافظ على منطق التقييم القطاعي، ويضيف السعر الحديث، التوزيعات، القيمة العادلة، التحليل الفني، جودة البيانات، ودمجًا 65% مالي + 35% فني. البيانات الناقصة لا تتحول إلى صفر.')
