import os, math, json, hashlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import requests

# V9 engine is extracted from the user's V9.5 PRO code with its Streamlit UI removed.
from v9_engine import load_data, process as v9_process, extract_symbol_data, run_real_backtest

st.set_page_config(page_title="EGX Institutional Quant V6", page_icon="🏛️", layout="wide")

# ============================================================
# EGX INSTITUTIONAL QUANT V6
# 12 institutional upgrades + original V9 technical engine.
# ============================================================

RAW = '''COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN MPCO ELSH MEPA ODIN EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH'''.split()
STOCKS = list(dict.fromkeys(x + '.CA' for x in RAW))

BANKS=set('COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB'.split())
RE=set('PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD DCRC ARCC RMDA IDRE RREI EGREF EHDR MENA MPRC'.split())
HEALTH=set('BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH'.split())
TECH=set('ETEL MTIE RAYA EFIH UBEE DGTZ GOUR'.split())
ENERGY=set('AMOC SKPC EGAS TAQA MOIL GPIM EGAL ELSH MEPA'.split())
CONSUMER=set('DOMT EAST JUFO SUGR POUL OLFI AJWA MICH UEGC ISMA FERC'.split())
CONSTRUCTION=set('ORAS ENGC SVCE ARAB ELNA UPMS UNIT NCCW RACC PRCL AIDC'.split())
FIN=set('EFIH BTFH VALU OFH CNFN MCQE ADCI ACAP FAIT AFDI UBEE FAITA AIFI AMIA AMII ATLC BINV DIFC'.split())
INDUSTRIAL=set(x for x in RAW if x not in BANKS|RE|HEALTH|TECH|ENERGY|CONSUMER|CONSTRUCTION|FIN)

SECTOR_RULES={
'Banks':['ROE','ROA','NIM','Cost/Income','NPL','NPL Coverage','CAR','Loan Growth','Deposit Growth','Net Income Growth','P/B','P/E','Dividend Yield'],
'Real Estate':['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROE','Debt/Equity','Net Debt/EBITDA','Operating Cash Flow','FCF Margin','P/B','P/E'],
'Healthcare':['Revenue Growth','EPS Growth','Net Margin','EBITDA Margin','ROE','ROA','FCF Margin','Debt/Equity','Current Ratio','P/E','P/B'],
'Telecom & Technology':['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROIC','FCF Margin','Net Debt/EBITDA','ROE','P/E','EV/EBITDA','Dividend Yield'],
'Energy & Petrochemicals':['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROIC','FCF Margin','Debt/Equity','Net Debt/EBITDA','ROE','P/E','EV/EBITDA','Dividend Yield'],
'Consumer':['Revenue Growth','EPS Growth','Gross Margin','EBITDA Margin','Net Margin','ROE','ROIC','FCF Margin','Debt/Equity','P/E','Dividend Yield'],
'Construction & Engineering':['Revenue Growth','EBITDA Margin','Net Margin','ROE','ROIC','Operating Cash Flow','FCF Margin','Debt/Equity','Net Debt/EBITDA','P/E','P/B'],
'Industrial & Materials':['Revenue Growth','EPS Growth','Gross Margin','EBITDA Margin','Net Margin','ROE','ROIC','FCF Margin','Debt/Equity','Net Debt/EBITDA','P/E','P/B','Dividend Yield'],
'Financial Services':['Revenue Growth','Net Income Growth','ROE','ROA','Net Margin','Debt/Equity','Current Ratio','P/E','P/B','Dividend Yield'],
'General':['Revenue Growth','EPS Growth','Net Margin','ROE','ROA','ROIC','FCF Margin','Debt/Equity','Current Ratio','P/E','P/B','Dividend Yield']}
WEIGHTS={k:{m:1/len(v) for m in v} for k,v in SECTOR_RULES.items()}
WEIGHTS['Banks']={'ROE':.15,'ROA':.07,'NIM':.12,'Cost/Income':.10,'NPL':.10,'NPL Coverage':.07,'CAR':.10,'Loan Growth':.07,'Deposit Growth':.05,'Net Income Growth':.08,'P/B':.05,'P/E':.02,'Dividend Yield':.02}

@dataclass
class SourceResult:
    source: str
    ok: bool
    data: Any = None
    error: str = ''
    timestamp: str = ''


def num(x):
    try:
        x=float(x); return x if np.isfinite(x) else np.nan
    except Exception: return np.nan

def pct(x):
    x=num(x); return np.nan if pd.isna(x) else x*100

def clean_series(s):
    if s is None: return pd.Series(dtype=float)
    return pd.to_numeric(s,errors='coerce').dropna()

def last(s):
    s=clean_series(s); return num(s.iloc[0]) if len(s) else np.nan

def prev(s):
    s=clean_series(s); return num(s.iloc[1]) if len(s)>1 else np.nan

def growth_series(s):
    s=clean_series(s)
    if len(s)<2 or s.iloc[1]==0: return np.nan
    return (s.iloc[0]/s.iloc[1]-1)*100

def find(df,names):
    if df is None or df.empty:return None
    for name in names:
        if name in df.index:return pd.to_numeric(df.loc[name],errors='coerce')
    for idx in df.index:
        low=str(idx).lower()
        for name in names:
            if name.lower() in low or low in name.lower(): return pd.to_numeric(df.loc[idx],errors='coerce')
    return None

def val_at(s,i):
    s=clean_series(s); return num(s.iloc[i]) if len(s)>i else np.nan

def sector(sym,info):
    s=sym.replace('.CA','')
    groups=[(BANKS,'Banks'),(RE,'Real Estate'),(HEALTH,'Healthcare'),(TECH,'Telecom & Technology'),(ENERGY,'Energy & Petrochemicals'),(CONSUMER,'Consumer'),(CONSTRUCTION,'Construction & Engineering'),(FIN,'Financial Services'),(INDUSTRIAL,'Industrial & Materials')]
    for g,n in groups:
        if s in g:return n
    text=(str(info.get('sector',''))+' '+str(info.get('industry',''))).lower()
    if 'bank' in text:return 'Banks'
    if 'real estate' in text:return 'Real Estate'
    if any(x in text for x in ['health','medical','pharma']):return 'Healthcare'
    if any(x in text for x in ['telecom','software','technology','internet']):return 'Telecom & Technology'
    if any(x in text for x in ['oil','gas','energy','petro']):return 'Energy & Petrochemicals'
    if any(x in text for x in ['consumer','food','beverage','retail']):return 'Consumer'
    if 'construction' in text or 'engineering' in text:return 'Construction & Engineering'
    if any(x in text for x in ['financial','insurance','investment']):return 'Financial Services'
    return 'General'

# ============================================================
# 1) MULTI-SOURCE DATA ENGINE
# ============================================================
class DataSourceManager:
    def __init__(self,ticker): self.ticker=ticker
    def yahoo(self):
        t=yf.Ticker(self.ticker)
        info=t.info or {}
        return SourceResult('Yahoo Finance',True,{'ticker':t,'info':info,'financials':t.financials,'balance':t.balance_sheet,'cashflow':t.cashflow},timestamp=pd.Timestamp.utcnow().isoformat())
    def stooq_price(self):
        # Optional market-price backup. Many EGX symbols are not covered by Stooq; failure is expected and explicit.
        sym=self.ticker.replace('.CA','').lower()+'.eg'
        url=f'https://stooq.com/q/d/l/?s={sym}&d1=20000101&i=d'
        r=requests.get(url,timeout=6,headers={'User-Agent':'Mozilla/5.0'})
        if r.ok and 'No data' not in r.text and len(r.text)>30:
            df=pd.read_csv(pd.io.common.StringIO(r.text))
            if not df.empty:return SourceResult('Stooq',True,df,timestamp=pd.Timestamp.utcnow().isoformat())
        return SourceResult('Stooq',False,error='No compatible EGX series')
    def alpha_vantage_price(self):
        key=os.getenv('ALPHAVANTAGE_API_KEY','').strip()
        if not key:return SourceResult('Alpha Vantage',False,error='API key not configured')
        url='https://www.alphavantage.co/query'
        r=requests.get(url,params={'function':'TIME_SERIES_DAILY','symbol':self.ticker,'outputsize':'compact','apikey':key},timeout=10)
        j=r.json(); ts=j.get('Time Series (Daily)')
        if not ts:return SourceResult('Alpha Vantage',False,error='No time series returned')
        rows=[{'Date':k,'Close':float(v['4. close'])} for k,v in ts.items()]
        return SourceResult('Alpha Vantage',True,pd.DataFrame(rows),timestamp=pd.Timestamp.utcnow().isoformat())
    def load(self):
        try:return self.yahoo()
        except Exception as e:return SourceResult('Yahoo Finance',False,error=str(e))


def reconcile_price(primary,backup_results):
    candidates=[('Yahoo',num(primary))]+[(x.source,num(x.data.iloc[-1]['Close']) if isinstance(x.data,pd.DataFrame) and 'Close' in x.data.columns and len(x.data) else np.nan) for x in backup_results if x.ok]
    good=[x for x in candidates if pd.notna(x[1]) and x[1]>0]
    if not good:return np.nan,'Unavailable',np.nan
    chosen=good[0]; prices=[x[1] for x in good]
    dispersion=(max(prices)-min(prices))/np.mean(prices)*100 if len(prices)>1 else 0
    return chosen[1],chosen[0],dispersion

# ============================================================
# 2) FINANCIAL STATEMENT NORMALIZATION
# ============================================================
def normalize_financials(raw):
    info=raw.get('info',{}); inc=raw.get('financials',pd.DataFrame()); bal=raw.get('balance',pd.DataFrame()); cf=raw.get('cashflow',pd.DataFrame())
    def s(df,n): return find(df,n)
    revenue=s(inc,['Total Revenue','Operating Revenue','Revenue']); ni=s(inc,['Net Income','Net Income Common Stockholders']); equity=s(bal,['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity']); assets=s(bal,['Total Assets']); debt=s(bal,['Total Debt','Long Term Debt','Current Debt']); cash=s(bal,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']); ocf=s(cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex=s(cf,['Capital Expenditure','Capital Expenditures']); ebit=s(inc,['EBIT','Operating Income']); ebitda=s(inc,['EBITDA','Normalized EBITDA']); gross=s(inc,['Gross Profit']); eps=s(inc,['Diluted EPS','Basic EPS']); ar=s(bal,['Receivables','Accounts Receivable']); ppe=s(bal,['Net PPE','Property Plant Equipment','Net Property Plant Equipment']); dep=s(cf,['Depreciation And Amortization','Depreciation']); sgna=s(inc,['Selling General And Administration','Selling General Administrative']); ca=s(bal,['Current Assets','Current Assets Total']); cl=s(bal,['Current Liabilities','Current Liabilities Total']); retained=s(bal,['Retained Earnings']); shares_s=s(inc,['Diluted Average Shares','Basic Average Shares']); shares_b=s(bal,['Ordinary Shares Number','Share Issued']); cfo=ocf
    fcf=pd.Series(dtype=float)
    if ocf is not None and capex is not None: fcf=pd.to_numeric(ocf,errors='coerce')+pd.to_numeric(capex,errors='coerce')
    elif ocf is not None: fcf=pd.to_numeric(ocf,errors='coerce')
    price=num(info.get('currentPrice')); mcap=num(info.get('marketCap')); shares=mcap/price if pd.notna(mcap) and pd.notna(price) and price else last(shares_s if shares_s is not None else shares_b)
    if pd.isna(shares): shares=num(info.get('sharesOutstanding'))
    metrics={
        'Revenue':last(revenue),'Revenue Prior':prev(revenue),'Net Income':last(ni),'Net Income Prior':prev(ni),'Equity':last(equity),'Equity Prior':prev(equity),'Assets':last(assets),'Assets Prior':prev(assets),'Debt':last(debt),'Debt Prior':prev(debt),'Cash':last(cash),'Cash Prior':prev(cash),'Operating Cash Flow':last(ocf),'Operating Cash Flow Prior':prev(ocf),'Capex':last(capex),'FCF':last(fcf),'FCF Prior':prev(fcf),'EBIT':last(ebit),'EBITDA':last(ebitda),'Gross Profit':last(gross),'Gross Profit Prior':prev(gross),'EPS':last(eps),'EPS Prior':prev(eps),'Receivables':last(ar),'Receivables Prior':prev(ar),'Current Assets':last(ca),'Current Assets Prior':prev(ca),'Current Liabilities':last(cl),'Current Liabilities Prior':prev(cl),'Retained Earnings':last(retained),'Retained Earnings Prior':prev(retained),'Market Cap':mcap,'Price':price,'Shares':shares,
        'Revenue Growth':growth_series(revenue),'Net Income Growth':growth_series(ni),'EPS Growth':growth_series(eps),
    }
    R=metrics['Revenue']; NI=metrics['Net Income']; EQ=metrics['Equity']; AS=metrics['Assets']; D=metrics['Debt']; C=metrics['Cash']; OCF=metrics['Operating Cash Flow']; FCF=metrics['FCF']; EBIT=metrics['EBIT']; EBITDA=metrics['EBITDA']; GP=metrics['Gross Profit']
    metrics.update({'Gross Margin':GP/R*100 if pd.notna(GP) and R else np.nan,'EBITDA Margin':EBITDA/R*100 if pd.notna(EBITDA) and R else np.nan,'Net Margin':NI/R*100 if pd.notna(NI) and R else np.nan,'ROE':NI/EQ*100 if pd.notna(NI) and pd.notna(EQ) and EQ else pct(info.get('returnOnEquity')),'ROA':NI/AS*100 if pd.notna(NI) and pd.notna(AS) and AS else pct(info.get('returnOnAssets')),'ROIC':EBIT/(EQ+D-C)*100 if pd.notna(EBIT) and pd.notna(EQ) and pd.notna(D) and pd.notna(C) and (EQ+D-C)!=0 else np.nan,'FCF Margin':FCF/R*100 if pd.notna(FCF) and pd.notna(R) and R else np.nan,'Debt/Equity':D/EQ if pd.notna(D) and pd.notna(EQ) and EQ else num(info.get('debtToEquity'))/100 if pd.notna(num(info.get('debtToEquity'))) else np.nan,'Net Debt/EBITDA':(D-C)/EBITDA if pd.notna(D) and pd.notna(C) and pd.notna(EBITDA) and EBITDA else np.nan,'Current Ratio':num(info.get('currentRatio')) if pd.notna(num(info.get('currentRatio'))) else (metrics['Current Assets']/metrics['Current Liabilities'] if pd.notna(metrics['Current Assets']) and pd.notna(metrics['Current Liabilities']) and metrics['Current Liabilities'] else np.nan),'P/E':num(info.get('trailingPE')),'P/B':num(info.get('priceToBook')),'EV/EBITDA':num(info.get('enterpriseToEbitda'))})
    # Historical arrays retained for forensic models.
    metrics['_series']={'revenue':revenue,'ni':ni,'eps':eps,'assets':assets,'equity':equity,'debt':debt,'cash':cash,'ocf':ocf,'fcf':fcf,'gross':gross,'receivables':ar,'ppe':ppe,'dep':dep,'sgna':sgna,'current_assets':ca,'current_liabilities':cl,'retained':retained,'ebit':ebit,'ebitda':ebitda,'shares':shares_s if shares_s is not None else shares_b}
    return metrics,inc,bal,cf,info

# ============================================================
# 3) PIOTROSKI F-SCORE
# ============================================================
def piotroski_full(m):
    s=m['_series']; points=0; checks=[]
    ni0,ni1=val_at(s['ni'],0),val_at(s['ni'],1); cfo0,cfo1=val_at(s['ocf'],0),val_at(s['ocf'],1); a0,a1=val_at(s['assets'],0),val_at(s['assets'],1); e0,e1=val_at(s['equity'],0),val_at(s['equity'],1); d0,d1=val_at(s['debt'],0),val_at(s['debt'],1); ca0,ca1=val_at(s['current_assets'],0),val_at(s['current_assets'],1); cl0,cl1=val_at(s['current_liabilities'],0),val_at(s['current_liabilities'],1); gp0,gp1=val_at(s['gross'],0),val_at(s['gross'],1); r0,r1=val_at(s['revenue'],0),val_at(s['revenue'],1); sh0,sh1=val_at(s['shares'],0),val_at(s['shares'],1)
    roa0=ni0/a0 if pd.notna(ni0) and pd.notna(a0) and a0 else np.nan; roa1=ni1/a1 if pd.notna(ni1) and pd.notna(a1) and a1 else np.nan; cr0=ca0/cl0 if pd.notna(ca0) and pd.notna(cl0) and cl0 else np.nan; cr1=ca1/cl1 if pd.notna(ca1) and pd.notna(cl1) and cl1 else np.nan; gm0=gp0/r0 if pd.notna(gp0) and pd.notna(r0) and r0 else np.nan; gm1=gp1/r1 if pd.notna(gp1) and pd.notna(r1) and r1 else np.nan; at0=r0/a0 if pd.notna(r0) and pd.notna(a0) and a0 else np.nan; at1=r1/a1 if pd.notna(r1) and pd.notna(a1) and a1 else np.nan
    tests=[('Net income positive',ni0>0,pd.notna(ni0)),('CFO positive',cfo0>0,pd.notna(cfo0)),('ROA improving',roa0>roa1,pd.notna(roa0) and pd.notna(roa1)),('CFO > Net income',cfo0>ni0,pd.notna(cfo0) and pd.notna(ni0)),('Leverage improving',d0/e0<d1/e1 if all(pd.notna(x) for x in [d0,e0,d1,e1]) and e0 and e1 else False,all(pd.notna(x) for x in [d0,e0,d1,e1])),('Current ratio improving',cr0>cr1,pd.notna(cr0) and pd.notna(cr1)),('No share dilution',sh0<=sh1,pd.notna(sh0) and pd.notna(sh1)),('Gross margin improving',gm0>gm1,pd.notna(gm0) and pd.notna(gm1)),('Asset turnover improving',at0>at1,pd.notna(at0) and pd.notna(at1))]
    for n,c,av in tests: points+=int(c) if av else 0; checks.append({'test':n,'pass':bool(c) if av else None,'available':bool(av)})
    available=sum(int(t[2]) for t in tests)
    return {'score':points,'checks':checks,'available':available,'coverage':available/9*100}

# ============================================================
# 4) BENEISH M-SCORE (full when two periods exist)
# ============================================================
def beneish_full(m):
    s=m['_series']
    def ratio(a,b): return a/b if pd.notna(a) and pd.notna(b) and b!=0 else np.nan
    ar0,ar1=val_at(s['receivables'],0),val_at(s['receivables'],1); rev0,rev1=val_at(s['revenue'],0),val_at(s['revenue'],1)
    gp0,gp1=val_at(s['gross'],0),val_at(s['gross'],1); ass0,ass1=val_at(s['assets'],0),val_at(s['assets'],1); ca0,ca1=val_at(s['current_assets'],0),val_at(s['current_assets'],1)
    ppe0,ppe1=val_at(s['ppe'],0),val_at(s['ppe'],1); dep0,dep1=abs(val_at(s['dep'],0)),abs(val_at(s['dep'],1)); sg0,sg1=abs(val_at(s['sgna'],0)),abs(val_at(s['sgna'],1))
    debt0,debt1=val_at(s['debt'],0),val_at(s['debt'],1); ocf0=val_at(s['ocf'],0); ni0=val_at(s['ni'],0)
    dsri=ratio(ar0/rev0,ar1/rev1)
    gmi=ratio(gp1/rev1,gp0/rev0)
    aqi=ratio(1-ca0/ass0,1-ca1/ass1) if all(pd.notna(x) for x in [ca0,ass0,ca1,ass1]) and ass0 and ass1 else np.nan
    sgi=ratio(rev0,rev1)
    depi=ratio(dep1/(dep1+ppe1),dep0/(dep0+ppe0)) if all(pd.notna(x) for x in [dep0,ppe0,dep1,ppe1]) and (dep0+ppe0) and (dep1+ppe1) else np.nan
    sgai=ratio(sg0/rev0,sg1/rev1) if all(pd.notna(x) for x in [sg0,sg1,rev0,rev1]) and rev0 and rev1 else np.nan
    lvgi=ratio((debt0/ass0) if pd.notna(debt0) and pd.notna(ass0) and ass0 else np.nan,(debt1/ass1) if pd.notna(debt1) and pd.notna(ass1) and ass1 else np.nan)
    tata=ratio(ni0-ocf0,ass0)
    vals={'DSRI':dsri,'GMI':gmi,'AQI':aqi,'SGI':sgi,'DEPI':depi,'SGAI':sgai,'LVGI':lvgi,'TATA':tata}
    required=list(vals.values()); avail=sum(pd.notna(x) for x in required)
    if avail<8:return {'score':np.nan,'status':'بيانات غير كافية لـ Beneish الكامل','components':vals,'coverage':avail/8*100,'risk_flags':np.nan}
    mscore=-4.84+0.92*dsri+0.528*gmi+0.404*aqi+0.892*sgi+0.115*depi-0.172*sgai+4.679*tata-0.327*lvgi
    return {'score':mscore,'status':'إشارة مخاطر محاسبية' if mscore>-1.78 else 'لا توجد إشارة حسب الحد التقليدي','components':vals,'coverage':100.0,'risk_flags':int(mscore>-1.78)}

# ============================================================
# 5) ALTMAN Z + earnings/ROIC quality
# ============================================================
def altman_z(m,sec):
    if sec=='Banks': return {'score':np.nan,'status':'غير مناسب للبنوك','coverage':0}
    A=(m.get('Current Assets',np.nan)-m.get('Current Liabilities',np.nan))/m.get('Assets',np.nan) if pd.notna(m.get('Assets',np.nan)) and m.get('Assets') else np.nan
    B=m.get('Retained Earnings',np.nan)/m.get('Assets',np.nan) if pd.notna(m.get('Retained Earnings',np.nan)) and m.get('Assets') else np.nan
    C=m.get('EBIT',np.nan)/m.get('Assets',np.nan) if pd.notna(m.get('EBIT',np.nan)) and m.get('Assets') else np.nan
    D=m.get('Market Cap',np.nan)/m.get('Debt',np.nan) if pd.notna(m.get('Market Cap',np.nan)) and pd.notna(m.get('Debt',np.nan)) and m.get('Debt') else np.nan
    E=m.get('Revenue',np.nan)/m.get('Assets',np.nan) if pd.notna(m.get('Revenue',np.nan)) and m.get('Assets') else np.nan
    xs=[A,B,C,D,E]; cov=sum(pd.notna(x) for x in xs)/5*100
    if cov<100:return {'score':np.nan,'status':'بيانات غير كافية','coverage':cov}
    z=1.2*A+1.4*B+3.3*C+0.6*D+1.0*E
    return {'score':z,'status':'خطر مرتفع' if z<1.8 else 'منطقة مراقبة' if z<3 else 'منطقة سليمة','coverage':cov}

def earnings_quality(m):
    ni,ocf,fcf=m.get('Net Income'),m.get('Operating Cash Flow'),m.get('FCF'); scores=[]
    if pd.notna(ni) and ni!=0 and pd.notna(ocf): scores.append(np.clip(50+50*(ocf/abs(ni)),0,100))
    if pd.notna(ni) and ni!=0 and pd.notna(fcf): scores.append(np.clip(50+50*(fcf/abs(ni)),0,100))
    if pd.notna(ni) and pd.notna(ocf): scores.append(100 if ocf>=ni else 30)
    if pd.notna(m.get('Net Income Growth')) and pd.notna(m.get('FCF Margin')): scores.append(np.clip(50+m.get('Net Income Growth')*.5+m.get('FCF Margin'),0,100))
    accrual=(ocf-ni)/abs(ni) if pd.notna(ni) and ni and pd.notna(ocf) else np.nan
    return {'score':float(np.mean(scores)) if scores else np.nan,'accrual_ratio':accrual,'coverage':len(scores)/4*100}

def roic_quality(m):
    roic=m.get('ROIC'); fcfm=m.get('FCF Margin'); rg=m.get('Revenue Growth'); nd=m.get('Net Debt/EBITDA')
    parts=[]
    if pd.notna(roic):parts.append(np.clip(roic*2.5,0,100))
    if pd.notna(fcfm):parts.append(np.clip(50+fcfm*2,0,100))
    if pd.notna(rg):parts.append(np.clip(50+rg,0,100))
    if pd.notna(nd):parts.append(np.clip(100-nd*20,0,100))
    return float(np.mean(parts)) if parts else np.nan

# ============================================================
# 6) DCF/FCFF REAL + sector relative valuation
# ============================================================
def cost_of_equity(info,beta_default=1.0):
    beta=num(info.get('beta')); beta=beta if pd.notna(beta) else beta_default
    rf=0.16  # explicit conservative EGP nominal assumption; user can override in UI
    mrp=0.08
    return rf+beta*mrp

def dcf_fcff_real(m,info,years=5,rf=0.16,mrp=0.08,tg=0.04):
    ebit=num(m.get('EBIT')); da=abs(num(val_at(m['_series'].get('dep'),0))); capex=num(m.get('Capex')); ca0=num(m.get('Current Assets')); cl0=num(m.get('Current Liabilities')); ca1=val_at(m['_series'].get('current_assets'),1); cl1=val_at(m['_series'].get('current_liabilities'),1)
    debt=num(m.get('Debt')); cash=num(m.get('Cash')); shares=num(m.get('Shares')); mcap=num(m.get('Market Cap')); tax=num(info.get('effectiveTaxRate')); tax=tax if pd.notna(tax) and 0<=tax<=0.60 else 0.22; beta=num(info.get('beta')); beta=beta if pd.notna(beta) else 1.0
    if pd.notna(ebit) and pd.notna(da) and pd.notna(capex):
        nwc0=(ca0-cl0) if pd.notna(ca0) and pd.notna(cl0) else np.nan; nwc1=(ca1-cl1) if pd.notna(ca1) and pd.notna(cl1) else np.nan; dnwc=(nwc0-nwc1) if pd.notna(nwc0) and pd.notna(nwc1) else 0.0
        base_fcff=ebit*(1-tax)+da+capex-dnwc
    else:
        base_fcff=num(m.get('FCF'));
    if pd.isna(base_fcff) or base_fcff<=0 or pd.isna(shares) or shares<=0:return {'value':np.nan,'status':'FCFF غير متاح/غير موجب','wacc':np.nan,'base_fcff':base_fcff}
    ke=rf+beta*mrp; d=max(debt,0) if pd.notna(debt) else 0; wacc=ke if pd.isna(mcap) or mcap<=0 else ke*(mcap/(mcap+d))+0.12*(1-tax)*(d/(mcap+d)); wacc=max(wacc,tg+0.02)
    g0=np.clip(num(m.get('Revenue Growth'))/100 if pd.notna(m.get('Revenue Growth')) else 0.06,-0.05,0.20); pv=0; cur=base_fcff
    for i in range(1,years+1):
        g=g0*(1-(i-1)/years)+tg*(i-1)/years; cur*=1+g; pv+=cur/(1+wacc)**i
    terminal=cur*(1+tg)/(wacc-tg); ev=pv+terminal/(1+wacc)**years; eq=ev-(debt if pd.notna(debt) else 0)+(cash if pd.notna(cash) else 0); value=eq/shares
    return {'value':value,'status':'OK','wacc':wacc,'ke':ke,'terminal_growth':tg,'enterprise_value':ev,'base_fcff':base_fcff,'tax_rate':tax}

def sector_relative(m,sec,peers):
    p=m.get('Price'); eps=m.get('EPS'); bv=m.get('Equity'); shares=m.get('Shares'); ebitda=m.get('EBITDA'); debt=m.get('Debt'); cash=m.get('Cash');
    vals=[]
    for x in peers:
        for metric,key in [('P/E','pe'),('P/B','pb'),('EV/EBITDA','ev')]:
            z=num(x.get(metric))
            if pd.notna(z) and z>0 and z<100: x[key]=z
    pe_med=np.nanmedian([x['pe'] for x in peers if 'pe' in x]); pb_med=np.nanmedian([x['pb'] for x in peers if 'pb' in x]); ev_med=np.nanmedian([x['ev'] for x in peers if 'ev' in x])
    if pd.notna(pe_med) and pd.notna(eps) and eps>0: vals.append(eps*pe_med)
    if pd.notna(pb_med) and pd.notna(bv) and pd.notna(shares) and shares>0: vals.append((bv/shares)*pb_med)
    if pd.notna(ev_med) and pd.notna(ebitda) and pd.notna(shares) and shares>0: vals.append((ebitda*ev_med-(debt if pd.notna(debt) else 0)+(cash if pd.notna(cash) else 0))/shares)
    return {'value':float(np.nanmedian(vals)) if vals else np.nan,'pe_median':pe_med,'pb_median':pb_med,'ev_ebitda_median':ev_med,'methods':len(vals)}

# ============================================================
# 7) DIVIDEND SUSTAINABILITY
# ============================================================
def dividend_engine(t,price,m):
    try:
        s=pd.to_numeric(t.dividends,errors='coerce').dropna(); s=s[s>0]
        if s.empty:return {'yield':np.nan,'last':np.nan,'count3y':0,'sustainability':np.nan,'cagr':np.nan,'payout':np.nan,'fcf_payout':np.nan}
        now=pd.Timestamp.now(tz=s.index.tz) if getattr(s.index,'tz',None) else pd.Timestamp.now(); d12=s[s.index>=now-pd.Timedelta(days=365)]; d3=s[s.index>=now-pd.Timedelta(days=1095)]; total=float(d12.sum()); y=total/price*100 if price else np.nan
        annual=[]
        for yr in range(3):
            z=s[(s.index>=now-pd.Timedelta(days=365*(yr+1)))&(s.index<now-pd.Timedelta(days=365*yr))].sum(); annual.append(float(z))
        cagr=(annual[0]/annual[-1])**(1/2)-1 if len(annual)>=3 and annual[-1]>0 and annual[0]>0 else np.nan
        ni=m.get('Net Income'); fcf=m.get('FCF'); payout=annual[0]/ni if ni and pd.notna(ni) and ni>0 else np.nan; fpayout=annual[0]/fcf if fcf and pd.notna(fcf) and fcf>0 else np.nan
        sustainability=np.nanmean([np.clip(100-abs((payout*100 if pd.notna(payout) else 50)-50),0,100),np.clip(100-abs((fpayout*100 if pd.notna(fpayout) else 50)-50),0,100),np.clip(50+(cagr*100 if pd.notna(cagr) else 0),0,100),80 if len(d3)>=3 else 40])
        return {'yield':y,'last':float(s.iloc[-1]),'date':s.index[-1].strftime('%Y-%m-%d'),'count3y':len(d3),'sustainability':sustainability,'cagr':cagr*100 if pd.notna(cagr) else np.nan,'payout':payout*100 if pd.notna(payout) else np.nan,'fcf_payout':fpayout*100 if pd.notna(fpayout) else np.nan}
    except Exception:return {'yield':np.nan,'last':np.nan,'count3y':0,'sustainability':np.nan,'cagr':np.nan,'payout':np.nan,'fcf_payout':np.nan}

# ============================================================
# 8) FINANCIAL / QUALITY SCORING
# ============================================================
def financial_score(sec,m):
    vals=[]; rules=SECTOR_RULES.get(sec,SECTOR_RULES['General']); weights=WEIGHTS.get(sec,WEIGHTS['General'])
    for k in rules:
        x=num(m.get(k))
        if pd.isna(x):continue
        if k in ['Revenue Growth','Net Income Growth','EPS Growth']: z=np.clip(50+x*1.5,0,100)
        elif k in ['ROE','ROIC']: z=np.clip(x*3,0,100)
        elif k=='ROA': z=np.clip(x*15,0,100)
        elif k in ['Gross Margin','EBITDA Margin','Net Margin','FCF Margin']: z=np.clip(x*2,0,100)
        elif k=='Debt/Equity': z=np.clip(100-max(x,0)*40,0,100)
        elif k=='Net Debt/EBITDA': z=np.clip(100-max(x,0)*18,0,100)
        elif k=='Current Ratio': z=np.clip(x*50,0,100)
        elif k=='Dividend Yield': z=np.clip(x*12,0,100)
        elif k=='P/E': z=np.clip(100-abs(x-12)*4,0,100) if x>0 else np.nan
        elif k=='P/B': z=np.clip(100-abs(x-1.4)*35,0,100) if x>0 else np.nan
        elif k=='NPL': z=np.clip(100-x*15,0,100)
        elif k=='NPL Coverage': z=np.clip(x,0,100)
        elif k=='Cost/Income': z=np.clip(100-x,0,100)
        else:z=50
        if np.isfinite(z):vals.append((z,weights[k]))
    return sum(a*b for a,b in vals)/sum(b for _,b in vals) if vals else np.nan

# ============================================================
# 9) STABILITY + FINAL SCORE + DATA QUALITY GATE
# ============================================================
def stability_score(bt,wfo):
    vals=[]
    if pd.notna(wfo.get('stability')): vals.append(wfo['stability'])
    if bt.get('trades',0)>=5:
        vals += [np.clip(100-bt.get('max_dd',50)*2,0,100), np.clip(50+bt.get('expectancy',0)*5,0,100), np.clip(bt.get('pf',1)*25,0,100)]
    return float(np.mean(vals)) if vals else np.nan

def final_score(fin,quality,val,tech,evidence,stability,data_quality):
    parts=[(fin,.25),(quality,.15),(val,.15),(tech,.15),(evidence,.15),(stability,.10),(data_quality,.05)]
    parts=[x for x in parts if pd.notna(x[0])]
    return sum(v*w for v,w in parts)/sum(w for _,w in parts) if parts else np.nan

def evidence_score(bt,wfo):
    vals=[]
    if bt.get('trades',0)>=5: vals += [np.clip(50+bt.get('expectancy',0)*5,0,100),np.clip(bt.get('pf',1)*25,0,100),np.clip(100-bt.get('max_dd',50)*2,0,100),bt.get('mc_profit_prob',50)]
    if pd.notna(wfo.get('score')): vals.append(wfo['score'])
    if pd.notna(wfo.get('oos_return')): vals.append(np.clip(50+wfo['oos_return'],0,100))
    return float(np.mean(vals)) if vals else np.nan

# ============================================================
# 10) ONE-STOCK ANALYSIS
# ============================================================
@st.cache_data(ttl=1800,show_spinner=False)
def analyze_one(sym,period_d,period_w,period_m,run_bt,backtest_bars,commission,slippage,mc_runs,rf,mrp,tg):
    ds=DataSourceManager(sym).load()
    if not ds.ok:return {'symbol':sym,'error':ds.error}
    raw=ds.data; m,inc,bal,cf,info=normalize_financials(raw); sec=sector(sym,info)
    # Price freshness and optional backup reconciliation.
    backups=[]
    try: backups.append(DataSourceManager(sym).stooq_price())
    except Exception: pass
    try: backups.append(DataSourceManager(sym).alpha_vantage_price())
    except Exception: pass
    primary=num(info.get('currentPrice')); price,price_source,disp=reconcile_price(primary,backups)
    if pd.notna(price):m['Price']=price
    # V9 multi-timeframe engine — original V9 logic retained.
    daily=load_data([sym],period_d,'1d'); weekly=load_data([sym],period_w,'1wk'); monthly=load_data([sym],period_m,'1mo')
    try:
        v9=v9_process(sym,daily,weekly,monthly,100000,2.0,0.0,False,backtest_bars)
    except Exception as e:v9={'السهم':sym.replace('.CA',''),'الحالة':f'V9 error: {str(e)[:100]}'}
    hist=extract_symbol_data(daily,sym)
    bt=run_real_backtest(hist,max_bars=backtest_bars,commission_pct=commission,slippage_pct=slippage,monte_carlo_runs=mc_runs) if run_bt and not hist.empty else {'trades':0}
    # WFO is executed by the V9 engine through its real implementation when available.
    try:
        wfo={'score': v9.get('Walk Forward Score %', v9.get('walk_forward_score', bt.get('walk_forward_score', bt.get('validation_score', np.nan)))), 'oos_return': v9.get('OOS Return %', v9.get('oos_return_pct', bt.get('oos_return_pct', np.nan))), 'stability': v9.get('WFO Stability %', v9.get('wfo_stability', bt.get('wfo_stability', np.nan))), 'folds': v9.get('WFO Folds', v9.get('wfo_folds', bt.get('wfo_folds', 0))), 'oos_trades': v9.get('OOS Trades', v9.get('oos_trades', bt.get('oos_trades', 0))), 'oos_pf': v9.get('OOS Profit Factor', v9.get('oos_profit_factor', bt.get('oos_profit_factor', np.nan))), 'oos_dd': v9.get('OOS Max DD %', v9.get('oos_max_dd_pct', bt.get('oos_max_dd_pct', np.nan)))}
    except Exception:wfo={'score':np.nan,'oos_return':np.nan,'stability':np.nan,'folds':0}
    # Forensic models.
    pi=piotroski_full(m); bene=beneish_full(m); alt=altman_z(m,sec); eq=earnings_quality(m); rq=roic_quality(m); div=dividend_engine(raw['ticker'],price,m)
    m['Dividend Yield']=div.get('yield')
    dcf=dcf_fcff_real(m,info,years=5,rf=rf,mrp=mrp,tg=tg)
    # Relative valuation is filled after peer universe is known.
    rel={'value':np.nan,'methods':0,'pe_median':np.nan,'pb_median':np.nan,'ev_ebitda_median':np.nan}
    technical_score=num(v9.get('التقييم',v9.get('Technical Score',np.nan)))
    if pd.isna(technical_score):
        technical_score=num(v9.get('score',np.nan))
    coverage_fields=[m.get(k) for k in ['Revenue','Net Income','Equity','Assets','Debt','Cash','Operating Cash Flow','FCF','EBIT','EBITDA','EPS','Price','P/E','P/B','EV/EBITDA','ROE','ROA','ROIC','FCF Margin']]
    dq=float(np.mean([pd.notna(x) for x in coverage_fields])*100)
    quality=float(np.nanmean([pi['score']/9*100 if pi['coverage']>=55 else np.nan,100-bene['risk_flags']*35 if pd.notna(bene['risk_flags']) else np.nan,alt['score']*25 if pd.notna(alt['score']) else np.nan,eq['score'],rq]))
    evidence=evidence_score(bt,wfo); stability=stability_score(bt,wfo)
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'industry':info.get('industry',''),'metrics':m,'info':info,'piotroski':pi,'beneish':bene,'altman':alt,'earnings_quality':eq,'roic_quality':rq,'dividend':div,'dcf':dcf,'relative':rel,'v9':v9,'backtest':bt,'wfo':wfo,'technical_score':technical_score,'data_quality':dq,'price_source':price_source,'price_dispersion':disp,'last_date':v9.get('تاريخ آخر شمعة Close',v9.get('last_date','—')),'quality_score':quality,'evidence_score':evidence,'stability_score':stability}

# ============================================================
# 11) UNIVERSE + SECTOR RELATIVE + FINAL INVESTMENT SCORE
# ============================================================
def analyze_universe(symbols,period_d,period_w,period_m,run_bt,backtest_bars,commission,slippage,mc_runs,rf,mrp,tg,workers):
    out=[]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs={ex.submit(analyze_one,s,period_d,period_w,period_m,run_bt,backtest_bars,commission,slippage,mc_runs,rf,mrp,tg):s for s in symbols}
        for f in as_completed(fs):
            try:out.append(f.result())
            except Exception as e:out.append({'symbol':fs[f],'error':str(e)})
    # Sector peer medians.
    for r in out:
        if r.get('error'):continue
        peers=[x['metrics'] for x in out if not x.get('error') and x.get('sector')==r.get('sector')]
        r['relative']=sector_relative(r['metrics'],r['sector'],peers)
        fv=[r['dcf'].get('value'),r['relative'].get('value')]
        fv=[x for x in fv if pd.notna(x) and x>0]
        r['fair_value']=float(np.nanmedian(fv)) if fv else np.nan
        p=r['metrics'].get('Price'); r['upside']=(r['fair_value']/p-1)*100 if pd.notna(r['fair_value']) and pd.notna(p) and p else np.nan
        val_score=np.clip(50+(r['upside'] if pd.notna(r['upside']) else 0)*0.5,0,100)
        fin_score=financial_score(r['sector'],r['metrics'])
        technical=r['technical_score']
        if pd.isna(technical):technical=50
        final=final_score(fin_score,r['quality_score'],val_score,technical,r['evidence_score'],r['stability_score'],r['data_quality'])
        r['scores']={'financial':fin_score,'quality':r['quality_score'],'valuation':val_score,'technical':technical,'evidence':r['evidence_score'],'stability':r['stability_score'],'data_quality':r['data_quality'],'final':final}
    return out

# ============================================================
# 12) UI / AUDITABLE REPORTING
# ============================================================
st.title('🏛️ EGX Institutional Quant V6')
st.caption('12 ترقية مؤسسية + محرك EGX AI PRO MAX V9.5 الأصلي: Data Integrity → Valuation → Forensic → Multi-Timeframe → Backtest → WFO/OOS → Monte Carlo → Stability → Final Score')

with st.sidebar:
    st.header('⚙️ Institutional Controls')
    period_d=st.selectbox('البيانات اليومية',['1y','2y','3y','5y','max'],index=2)
    period_w=st.selectbox('البيانات الأسبوعية',['3y','5y','10y','max'],index=2)
    period_m=st.selectbox('البيانات الشهرية',['10y','15y','20y','max'],index=1)
    workers=st.slider('Workers',2,16,8)
    top_n=st.number_input('أفضل N سهم',5,100,20)
    min_cov=st.slider('Data Quality Gate %',0,100,60,5)
    run_bt=st.checkbox('Backtest + WFO/OOS + Monte Carlo',True)
    backtest_bars=st.slider('Backtest bars',200,1200,600,50)
    commission=st.number_input('Commission % / side',0.0,2.0,0.15,0.01)
    slippage=st.number_input('Slippage % / side',0.0,2.0,0.10,0.01)
    mc_runs=st.selectbox('Monte Carlo runs',[250,500,1000,2000],index=2)
    st.markdown('### DCF Assumptions')
    rf=st.slider('Risk-free %',5.0,30.0,16.0,0.5)/100
    mrp=st.slider('Market Risk Premium %',3.0,15.0,8.0,0.5)/100
    tg=st.slider('Terminal Growth %',1.0,6.0,4.0,0.25)/100
    if st.button('🔄 مسح الكاش وإعادة التحليل',use_container_width=True):
        analyze_one.clear(); st.cache_data.clear(); st.rerun()

if 'results' not in st.session_state:
    st.session_state.results=None
if st.button('🚀 تشغيل V6 Institutional Scan',type='primary',use_container_width=True) or st.session_state.results is None:
    with st.spinner(f'جاري تحليل {len(STOCKS)} سهم عبر V6 + V9...'):
        st.session_state.results=analyze_universe(STOCKS,period_d,period_w,period_m,run_bt,backtest_bars,commission,slippage,mc_runs,rf,mrp,tg,workers)
results=st.session_state.results
valid=[r for r in results if not r.get('error') and r.get('data_quality',0)>=min_cov]

rows=[]
for r in valid:
    s=r['scores']; b=r['backtest']; w=r['wfo']; f=r['piotroski']; be=r['beneish']; al=r['altman']; d=r['dividend']; m=r['metrics']
    rows.append({'الترتيب':0,'السهم':r['symbol'].replace('.CA',''),'القطاع':r['sector'],'Final Investment Score':s['final'],'Confidence / Data Quality':r['data_quality'],'Financial':s['financial'],'Quality':s['quality'],'Valuation':s['valuation'],'Technical V9':s['technical'],'Evidence':s['evidence'],'Stability':s['stability'],'السعر':m.get('Price'),'القيمة العادلة':r.get('fair_value'),'الصعود %':r.get('upside'),'Piotroski':f['score'],'Beneish M':be.get('score'),'Altman Z':al.get('score'),'Earnings Quality':r['earnings_quality']['score'],'ROIC Quality':r['roic_quality'],'Dividend Sustainability':d.get('sustainability'),'Dividend Yield %':d.get('yield'),'BT Trades':b.get('trades',0),'Win Rate %':b.get('win_rate',np.nan),'BT Return %':b.get('return',np.nan),'Max DD %':b.get('max_dd',np.nan),'Profit Factor':b.get('pf',np.nan),'Expectancy %':b.get('expectancy',np.nan),'Sharpe':b.get('sharpe',np.nan),'Sortino':b.get('sortino',np.nan),'Calmar':b.get('calmar',np.nan),'WFO Score':w.get('score',np.nan),'OOS Return %':w.get('oos_return',np.nan),'WFO Stability %':w.get('stability',np.nan),'MC 5%':b.get('monte_carlo_5pct',np.nan),'MC Median':b.get('monte_carlo_median',np.nan),'MC 95%':b.get('monte_carlo_95pct',np.nan),'MC Profit Probability %':b.get('monte_carlo_profit_probability',np.nan),'MC 95% Max DD %':b.get('monte_carlo_max_dd_95pct',np.nan),'Price Source':r['price_source'],'Source Dispersion %':r['price_dispersion'],'Last Candle':r['last_date']})
df=pd.DataFrame(rows)
if not df.empty:
    df=df.sort_values('Final Investment Score',ascending=False,na_position='last').reset_index(drop=True); df['الترتيب']=np.arange(1,len(df)+1)

st.subheader('🏆 Institutional Ranking')
if df.empty: st.warning('لا توجد أسهم اجتازت Data Quality Gate.')
else:
    st.dataframe(df.head(int(top_n)),use_container_width=True,hide_index=True)
    st.download_button('⬇️ CSV كامل',df.to_csv(index=False,encoding='utf-8-sig').encode('utf-8-sig'),'EGX_Institutional_V6.csv','text/csv')

st.subheader('🔎 Deep Institutional Report')
if results:
    choices=sorted([r['symbol'] for r in valid])
    if choices:
        sel=st.selectbox('اختر سهم',choices,format_func=lambda x:x.replace('.CA',''))
        r=next(x for x in valid if x['symbol']==sel); s=r['scores']; m=r['metrics']; f=r['piotroski']; be=r['beneish']; al=r['altman']; eq=r['earnings_quality']; rq=r['roic_quality']; d=r['dividend']; b=r['backtest']; w=r['wfo']
        cols=st.columns(8)
        for c,label,val in zip(cols,['Final','Financial','Quality','Valuation','Technical V9','Evidence','Stability','Data Quality'],[s['final'],s['financial'],s['quality'],s['valuation'],s['technical'],s['evidence'],s['stability'],r['data_quality']]):c.metric(label,'—' if pd.isna(val) else f'{val:.1f}')
        st.write(f"**{r['name']}** | {r['sector']} | السعر: **{m.get('Price',np.nan):.2f}** | آخر شمعة: **{r['last_date']}** | المصدر: **{r['price_source']}** | اختلاف المصادر: **{r['price_dispersion']:.2f}%**")
        tabs=st.tabs(['💰 Valuation','🧪 Forensic','📊 Financial Quality','📈 V9 Technical','🧪 Backtest/WFO/OOS','🎲 Monte Carlo','💵 Dividend','🛡️ Data Integrity'])
        with tabs[0]:
            st.dataframe(pd.DataFrame([{'Model':'DCF / FCFF','Value':r['dcf'].get('value'),'WACC':r['dcf'].get('wacc'),'Status':r['dcf'].get('status')},{'Model':'Sector Relative','Value':r['relative'].get('value'),'P/E Median':r['relative'].get('pe_median'),'P/B Median':r['relative'].get('pb_median'),'EV/EBITDA Median':r['relative'].get('ev_ebitda_median')},{'Model':'Blended Fair Value','Value':r.get('fair_value')},{'Model':'Buy 20% MOS','Value':r.get('fair_value')*.8 if pd.notna(r.get('fair_value')) else np.nan},{'Model':'Buy 30% MOS','Value':r.get('fair_value')*.7 if pd.notna(r.get('fair_value')) else np.nan},{'Model':'Upside %','Value':r.get('upside')}]),use_container_width=True,hide_index=True)
        with tabs[1]:
            st.dataframe(pd.DataFrame([{'Model':'Piotroski F-Score','Score':f['score'],'Coverage %':f['coverage']},{'Model':'Beneish M-Score','Score':be.get('score'),'Risk Flags':be.get('risk_flags'),'Coverage %':be.get('coverage'),'Status':be.get('status')},{'Model':'Altman Z','Score':al.get('score'),'Coverage %':al.get('coverage'),'Status':al.get('status')}]),use_container_width=True,hide_index=True)
            st.json({'Piotroski Checks':f['checks'],'Beneish Components':be.get('components')})
        with tabs[2]:
            st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in m.items() if not k.startswith('_')]),use_container_width=True,hide_index=True)
            st.metric('Earnings Quality',f"{eq['score']:.1f}" if pd.notna(eq['score']) else '—'); st.metric('ROIC Quality',f"{rq:.1f}" if pd.notna(rq) else '—')
        with tabs[3]:
            st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in r['v9'].items()]),use_container_width=True,hide_index=True)
        with tabs[4]:
            st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in b.items()]),use_container_width=True,hide_index=True); st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in w.items()]),use_container_width=True,hide_index=True)
        with tabs[5]:
            st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in b.items() if 'monte' in k.lower() or 'mc_' in k.lower()]),use_container_width=True,hide_index=True)
        with tabs[6]:
            st.dataframe(pd.DataFrame([d]),use_container_width=True,hide_index=True)
        with tabs[7]:
            st.write({'Data Quality %':r['data_quality'],'Primary Price Source':r['price_source'],'Price Dispersion %':r['price_dispersion'],'Last Candle':r['last_date'],'Yahoo Freshness':'current fetch','V9 Status':r['v9'].get('الحالة','OK')})

st.divider(); st.caption('V6 Institutional Quant — الأدوات والنماذج تحليلية وليست ضمانًا للنتائج. Beneish/Altman قد يكونان غير مناسبين أو ناقصي البيانات لبعض القطاعات، ويظهر ذلك صراحة بدل اختلاق قيم.')
