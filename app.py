import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Any, Optional

st.set_page_config(page_title='EGX Institutional V5', page_icon='🏛️', layout='wide')

# ============================================================
# EGX INSTITUTIONAL V5
# Data -> Normalization -> Financial Quality -> Valuation ->
# Dividends -> V9 Technical -> Backtest/WFO/OOS/Monte Carlo ->
# Stability -> Final Investment Score
# ============================================================

RAW = '''COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN MPCO ELSH MEPA ODIN EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH'''.split()
STOCKS = list(dict.fromkeys(x + '.CA' for x in RAW))

BANKS=set('COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB'.split())
RE=set('PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD DCRC ARCC RMDA IDRE RREI EGREF EHDR MENA MPRC'.split())
HEALTH=set('BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH'.split())
TECH=set('ETEL MTIE RAYA EFIH UBEE DGTZ GOUR'.split())
ENERGY=set('AMOC SKPC EGAS TAQA MOIL GPIM EGAL ELSH MEPA'.split())
CONSUMER=set('DOMT EAST JUFO SUGR POUL OLFI AJWA MICH UEGC ISMA GOUR FERC'.split())
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


def num(x):
    try:
        x=float(x); return x if np.isfinite(x) else np.nan
    except Exception: return np.nan

def pct(x):
    x=num(x); return np.nan if pd.isna(x) else x*100

def last(s):
    if s is None: return np.nan
    s=pd.to_numeric(s,errors='coerce').dropna()
    return num(s.iloc[0]) if len(s) else np.nan

def growth(s):
    if s is None: return np.nan
    s=pd.to_numeric(s,errors='coerce').dropna()
    if len(s)<2 or s.iloc[-1]==0: return np.nan
    return (s.iloc[0]/s.iloc[-1]-1)*100

def find(df,names):
    if df is None or df.empty:return None
    for name in names:
        if name in df.index:return pd.to_numeric(df.loc[name],errors='coerce')
    for idx in df.index:
        low=str(idx).lower()
        for name in names:
            if name.lower() in low or low in name.lower():return pd.to_numeric(df.loc[idx],errors='coerce')
    return None

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

# ---------------- Multi-source data layer ----------------
@dataclass
class SourceResult:
    source:str; ok:bool; data:Any=None; error:str=''

class DataSourceManager:
    """Primary Yahoo; architecture-ready adapters for official/company filings and backups."""
    def __init__(self, ticker): self.ticker=ticker
    def yahoo(self):
        t=yf.Ticker(self.ticker)
        return SourceResult('Yahoo Finance',True,{'ticker':t,'info':t.info or {},'financials':t.financials,'balance':t.balance_sheet,'cashflow':t.cashflow})
    def load(self):
        try:return self.yahoo()
        except Exception as e:return SourceResult('Yahoo Finance',False,error=str(e))

# ---------------- Financial normalization ----------------
def normalize_financials(raw):
    info=raw.get('info',{}); inc=raw.get('financials',pd.DataFrame()); bal=raw.get('balance',pd.DataFrame()); cf=raw.get('cashflow',pd.DataFrame())
    R,NI,EQ,AS,D,C,OCF,CAPEX,EBIT,EBITDA,GROSS=map(last,[find(inc,['Total Revenue','Operating Revenue','Revenue']),find(inc,['Net Income','Net Income Common Stockholders']),find(bal,['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity']),find(bal,['Total Assets']),find(bal,['Total Debt','Long Term Debt']),find(bal,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']),find(cf,['Operating Cash Flow','Total Cash From Operating Activities']),find(cf,['Capital Expenditure','Capital Expenditures']),find(inc,['EBIT','Operating Income']),find(inc,['EBITDA','Normalized EBITDA']),find(inc,['Gross Profit'])])
    fcf=OCF+CAPEX if pd.notna(OCF) and pd.notna(CAPEX) and CAPEX<0 else (OCF-CAPEX if pd.notna(OCF) and pd.notna(CAPEX) else np.nan)
    price=num(info.get('currentPrice')); mcap=num(info.get('marketCap')); shares=mcap/price if pd.notna(mcap) and pd.notna(price) and price else np.nan
    eps=last(find(inc,['Diluted EPS','Basic EPS']))
    metrics={'Revenue':R,'Net Income':NI,'Equity':EQ,'Assets':AS,'Debt':D,'Cash':C,'Operating Cash Flow':OCF,'Capex':CAPEX,'FCF':fcf,'EBIT':EBIT,'EBITDA':EBITDA,'Gross Profit':GROSS,'EPS':eps,'Shares':shares,'Market Cap':mcap,'Price':price,
    'Revenue Growth':growth(find(inc,['Total Revenue','Operating Revenue','Revenue'])),'Net Income Growth':growth(find(inc,['Net Income','Net Income Common Stockholders'])),'EPS Growth':growth(find(inc,['Diluted EPS','Basic EPS']))}
    metrics.update({'Gross Margin':GROSS/R*100 if pd.notna(GROSS) and R else np.nan,'EBITDA Margin':EBITDA/R*100 if pd.notna(EBITDA) and R else np.nan,'Net Margin':NI/R*100 if pd.notna(NI) and R else np.nan,'ROE':NI/EQ*100 if pd.notna(NI) and pd.notna(EQ) and EQ else pct(info.get('returnOnEquity')),'ROA':NI/AS*100 if pd.notna(NI) and pd.notna(AS) and AS else pct(info.get('returnOnAssets')),'ROIC':EBIT/(EQ+D-(C if pd.notna(C) else 0))*100 if pd.notna(EBIT) and pd.notna(EQ) and pd.notna(D) and EQ+D-(C if pd.notna(C) else 0) else np.nan,'FCF Margin':fcf/R*100 if pd.notna(fcf) and pd.notna(R) and R else np.nan,'Debt/Equity':D/EQ if pd.notna(D) and pd.notna(EQ) and EQ else num(info.get('debtToEquity'))/100 if pd.notna(num(info.get('debtToEquity'))) else np.nan,'Net Debt/EBITDA':(D-C)/EBITDA if pd.notna(D) and pd.notna(C) and pd.notna(EBITDA) and EBITDA else np.nan,'Current Ratio':num(info.get('currentRatio')),'P/E':num(info.get('trailingPE')),'P/B':num(info.get('priceToBook')),'EV/EBITDA':num(info.get('enterpriseToEbitda')),'Dividend Yield':pct(info.get('dividendYield'))})
    return metrics,inc,bal,cf,info

# ---------------- Forensic quality models ----------------
def piotroski(m,inc,bal,cf):
    points=0
    tests=[]
    roe=num(m.get('ROE')); ocf=num(m.get('Operating Cash Flow')); NI=num(m.get('Net Income')); debt=num(m.get('Debt')); margin=num(m.get('Net Margin')); rev=num(m.get('Revenue')); fcf=num(m.get('FCF'))
    checks=[('صافي الربح موجب',NI>0),('التدفق التشغيلي موجب',ocf>0),('ROE موجب',roe>0),('FCF موجب',fcf>0),('هامش صافي موجب',margin>0),('الدين/حقوق الملكية تحت السيطرة',num(m.get('Debt/Equity'))<1.5),('نمو الإيرادات موجب',num(m.get('Revenue Growth'))>0),('نمو صافي الربح موجب',num(m.get('Net Income Growth'))>0),('نمو EPS موجب',num(m.get('EPS Growth'))>0)]
    for n,c in checks: points+=int(bool(c)); tests.append((n,int(bool(c))))
    return min(points,9),tests

def beneish(m):
    # Conservative screening score; unavailable components are not fabricated.
    components={'DSRI':np.nan,'GMI':np.nan,'AQI':np.nan,'SGI':np.nan,'DEPI':np.nan,'SGAI':np.nan,'LVGI':np.nan,'TATA':np.nan}
    # Use a transparent proxy only when normalized current/prior data exists.
    risk=0; available=0
    if pd.notna(num(m.get('Revenue Growth'))):
        available+=1
        if num(m.get('Revenue Growth'))>80:risk+=1
    if pd.notna(num(m.get('Net Margin'))):
        available+=1
        if num(m.get('Net Margin'))<0:risk+=1
    if pd.notna(num(m.get('Debt/Equity'))):
        available+=1
        if num(m.get('Debt/Equity'))>2:risk+=1
    if pd.notna(num(m.get('FCF Margin'))):
        available+=1
        if num(m.get('FCF Margin'))<0:risk+=1
    return {'risk_flags':risk,'available':available,'components':components,'status':'مبدئي — يحتاج 2 سنوات كاملة من بنود القوائم' if available<4 else 'Screening'}

def altman(m,sec):
    A=num(m.get('Working Capital'))/num(m.get('Assets')) if pd.notna(num(m.get('Working Capital'))) and pd.notna(num(m.get('Assets'))) and num(m.get('Assets')) else np.nan
    B=num(m.get('Retained Earnings'))/num(m.get('Assets')) if pd.notna(num(m.get('Retained Earnings'))) and pd.notna(num(m.get('Assets'))) and num(m.get('Assets')) else np.nan
    C=num(m.get('EBIT'))/num(m.get('Assets')) if pd.notna(num(m.get('EBIT'))) and pd.notna(num(m.get('Assets'))) and num(m.get('Assets')) else np.nan
    D=num(m.get('Market Cap'))/num(m.get('Debt')) if pd.notna(num(m.get('Market Cap'))) and pd.notna(num(m.get('Debt'))) and num(m.get('Debt')) else np.nan
    E=num(m.get('Revenue'))/num(m.get('Assets')) if pd.notna(num(m.get('Revenue'))) and pd.notna(num(m.get('Assets'))) and num(m.get('Assets')) else np.nan
    if any(pd.isna(x) for x in [A,B,C,D,E]): return {'score':np.nan,'status':'بيانات غير كافية'}
    z=1.2*A+1.4*B+3.3*C+0.6*D+1.0*E
    return {'score':z,'status':'منطقة خطر مرتفعة' if z<1.8 else 'منطقة مراقبة' if z<3 else 'منطقة سليمة'}

def earnings_quality(m):
    ocf=num(m.get('Operating Cash Flow')); ni=num(m.get('Net Income')); fcf=num(m.get('FCF')); roe=num(m.get('ROE'))
    accrual=(ocf-ni)/abs(ni) if pd.notna(ocf) and pd.notna(ni) and ni else np.nan
    score=50
    if pd.notna(accrual):score+=np.clip(-accrual*25,-25,25)
    if pd.notna(fcf) and pd.notna(ni):score+=15 if fcf>ni else -15
    if pd.notna(roe):score+=np.clip(roe-10,-20,20)
    return float(np.clip(score,0,100)),accrual

def roic_quality(m):
    roic=num(m.get('ROIC')); fcfm=num(m.get('FCF Margin')); growthv=num(m.get('Revenue Growth'))
    score=np.nanmean([np.clip(roic*2.5,0,100) if pd.notna(roic) else np.nan,np.clip(fcfm*2,0,100) if pd.notna(fcfm) else np.nan,np.clip(50+growthv,0,100) if pd.notna(growthv) else np.nan])
    return float(score) if np.isfinite(score) else np.nan

def dividend_engine(t,price):
    try:
        s=pd.to_numeric(t.dividends,errors='coerce').dropna(); s=s[s>0]
        if s.empty:return {'yield':np.nan,'last':np.nan,'count3y':0,'sustainability':np.nan}
        now=pd.Timestamp.now(tz=s.index.tz) if getattr(s.index,'tz',None) else pd.Timestamp.now(); d12=s[s.index>=now-pd.Timedelta(days=365)]; d3=s[s.index>=now-pd.Timedelta(days=1095)]
        total=float(d12.sum()); y=total/price*100 if price else np.nan
        sustainability=np.clip(100-abs(y-4)*8,0,100) if pd.notna(y) else np.nan
        return {'yield':y,'last':float(s.iloc[-1]),'date':s.index[-1].strftime('%Y-%m-%d'),'count3y':len(d3),'sustainability':sustainability}
    except Exception:return {'yield':np.nan,'last':np.nan,'count3y':0,'sustainability':np.nan}

# ---------------- Valuation ----------------
def dcf_fcff(m,years=5,wacc=0.14,tg=0.04):
    fcf=num(m.get('FCF')); rev=num(m.get('Revenue')); g=num(m.get('Revenue Growth')); shares=num(m.get('Shares')); debt=num(m.get('Debt')); cash=num(m.get('Cash'))
    if pd.isna(fcf) or fcf<=0 or pd.isna(shares) or shares<=0:return {'value':np.nan,'status':'FCFF غير متاح'}
    g0=np.clip(0 if pd.isna(g) else g/100, -0.10, 0.25); growths=[max(tg,g0*(1-i*0.12)) for i in range(years)]
    pv=0; cur=fcf
    for i,gr in enumerate(growths,1):
        cur*=1+gr; pv+=cur/(1+wacc)**i
    terminal=cur*(1+tg)/(wacc-tg); ev=pv+terminal/(1+wacc)**years; eq=ev-(debt if pd.notna(debt) else 0)+(cash if pd.notna(cash) else 0)
    return {'value':eq/shares,'enterprise':ev,'status':'FCFF DCF'}

def relative_valuation(m,sector):
    pe=num(m.get('P/E')); pb=num(m.get('P/B')); price=num(m.get('Price')); eps=num(m.get('EPS')); bv=(num(m.get('Equity'))/num(m.get('Shares'))) if pd.notna(num(m.get('Equity'))) and pd.notna(num(m.get('Shares'))) and num(m.get('Shares')) else np.nan
    # Sector benchmark ranges are conservative reference multiples, not live peer medians.
    pe_ref={'Banks':10,'Financial Services':11,'Real Estate':12,'Healthcare':15,'Telecom & Technology':14,'Energy & Petrochemicals':9,'Consumer':13,'Construction & Engineering':11,'Industrial & Materials':11}.get(sector,12)
    pb_ref=1.4 if sector=='Banks' else 1.5
    vals=[]
    if pd.notna(eps) and eps>0:vals.append(eps*pe_ref)
    if pd.notna(bv) and bv>0:vals.append(bv*pb_ref)
    return {'value':float(np.nanmedian(vals)) if vals else np.nan,'pe_ref':pe_ref,'pb_ref':pb_ref,'methods':len(vals)}

def valuation_engine(m,sector):
    d=dcf_fcff(m); r=relative_valuation(m,sector); price=num(m.get('Price')); vals=[x for x in [d.get('value'),r.get('value')] if pd.notna(x) and x>0]
    fair=float(np.nanmedian(vals)) if vals else np.nan
    return {'DCF/FCFF':d.get('value'),'Relative':r.get('value'),'Fair Value':fair,'Buy 20% MOS':fair*.8 if pd.notna(fair) else np.nan,'Strong Buy 30% MOS':fair*.7 if pd.notna(fair) else np.nan,'Upside %':(fair/price-1)*100 if pd.notna(fair) and pd.notna(price) and price else np.nan}

# ---------------- V9-style technical + evidence ----------------
def technical(df):
    if df is None or df.empty or 'Close' not in df or len(df)<220:return {}
    d=df.copy(); close=pd.to_numeric(d['Close'],errors='coerce').dropna(); high=pd.to_numeric(d['High'],errors='coerce').reindex(close.index); low=pd.to_numeric(d['Low'],errors='coerce').reindex(close.index); vol=pd.to_numeric(d['Volume'],errors='coerce').reindex(close.index)
    ema20=close.ewm(span=20,adjust=False).mean(); ema50=close.ewm(span=50,adjust=False).mean(); ema200=close.ewm(span=200,adjust=False).mean()
    delta=close.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean(); loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean(); rsi=100-100/(1+gain/loss.replace(0,np.nan))
    macd=close.ewm(span=12,adjust=False).mean()-close.ewm(span=26,adjust=False).mean(); sig=macd.ewm(span=9,adjust=False).mean()
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(14).mean(); vr=vol.iloc[-1]/vol.rolling(20).mean().iloc[-1] if pd.notna(vol.rolling(20).mean().iloc[-1]) and vol.rolling(20).mean().iloc[-1] else np.nan
    c=float(close.iloc[-1]); e20=float(ema20.iloc[-1]); e50=float(ema50.iloc[-1]); e200=float(ema200.iloc[-1]); flags=[c>e20,c>e50,c>e200,rsi.iloc[-1]>50,macd.iloc[-1]>sig.iloc[-1],vr>=1 if pd.notna(vr) else False]; score=sum(flags)/6*100
    support=float(close.tail(20).min()); resistance=float(close.tail(20).max()); stop=max(support,c-(atr.iloc[-1]*2 if pd.notna(atr.iloc[-1]) else c*.08)); target= max(resistance,c*1.05)
    return {'score':score,'price':c,'rsi':float(rsi.iloc[-1]),'macd':float(macd.iloc[-1]),'signal':float(sig.iloc[-1]),'atr_pct':float(atr.iloc[-1]/c*100) if pd.notna(atr.iloc[-1]) else np.nan,'volume_ratio':float(vr) if pd.notna(vr) else np.nan,'ema20':e20,'ema50':e50,'ema200':e200,'support':support,'resistance':resistance,'stop':stop,'target1':target,'last_date':close.index[-1].strftime('%Y-%m-%d')}

def backtest(df,commission=.0015,slippage=.001,mc_runs=500):
    if df is None or len(df)<260:return {'trades':0,'status':'بيانات غير كافية'}
    t=technical(df.iloc[:-1].copy()); close=pd.to_numeric(df['Close'],errors='coerce').dropna(); ema=close.ewm(span=20,adjust=False).mean(); rsi=100-100/(1+(close.diff().clip(lower=0).ewm(alpha=1/14).mean()/(-close.diff().clip(upper=0).ewm(alpha=1/14).mean()).replace(0,np.nan)))
    returns=[]; in_pos=False; entry=0
    for i in range(220,len(close)):
        c=close.iloc[i]
        if not in_pos and c>ema.iloc[i] and rsi.iloc[i]>52:
            entry=float(c)*(1+slippage+commission); in_pos=True
        elif in_pos and (c<ema.iloc[i] or rsi.iloc[i]<48):
            exitp=float(c)*(1-slippage-commission); returns.append(exitp/entry-1); in_pos=False
    if in_pos:returns.append(float(close.iloc[-1])/entry-1)
    r=np.array(returns,float); trades=len(r)
    if not trades:return {'trades':0,'status':'لا توجد صفقات'}
    curve=np.cumprod(1+r); peak=np.maximum.accumulate(curve); dd=(peak-curve)/peak*100
    win=float((r>0).mean()*100); profit=float((curve[-1]-1)*100); pf=float(r[r>0].sum()/abs(r[r<0].sum())) if (r<0).any() else np.inf; exp=float(r.mean()*100); sharpe=float(r.mean()/r.std()*np.sqrt(trades)) if r.std()>0 else np.nan
    rng=np.random.default_rng(42); terminals=[]; dds=[]
    for _ in range(mc_runs):
        s=rng.choice(r,size=trades,replace=True); c=np.cumprod(1+s); p=np.maximum.accumulate(c); terminals.append((c[-1]-1)*100); dds.append(np.max((p-c)/p)*100)
    return {'trades':trades,'win_rate':win,'return':profit,'max_dd':float(dd.max()),'pf':pf,'expectancy':exp,'sharpe':sharpe,'mc5':float(np.percentile(terminals,5)),'mc50':float(np.percentile(terminals,50)),'mc95':float(np.percentile(terminals,95)),'mc_profit_prob':float(np.mean(np.array(terminals)>0)*100),'mc_dd95':float(np.percentile(dds,95)),'status':'تم'}

def wfo_score(df):
    if df is None or len(df)<600:return {'score':np.nan,'oos_return':np.nan,'stability':np.nan,'folds':0}
    n=len(df); fold=int(n/4); scores=[]; returns=[]
    for k in range(3):
        test=df.iloc[fold*(k+1):fold*(k+2)] if fold*(k+2)<=n else df.iloc[-fold:]
        bt=backtest(test,mc_runs=100)
        if bt.get('trades',0)>=3:scores.append(np.clip(50+bt['return'],0,100)); returns.append(bt['return'])
    return {'score':float(np.mean(scores)) if scores else np.nan,'oos_return':float(np.mean(returns)) if returns else np.nan,'stability':float(100-np.std(returns)*2) if len(returns)>1 else (50 if returns else np.nan),'folds':len(scores)}

# ---------------- Institutional scoring ----------------
def score_stock(fin,forensic,val,tech,bt,wfo,div):
    fscore=[]; rules=SECTOR_RULES[fin['sector']]; w=WEIGHTS[fin['sector']]
    for k in rules:
        x=num(fin['metrics'].get(k));
        if pd.isna(x):continue
        if k in ['Revenue Growth','Net Income Growth','EPS Growth']:s=np.clip(50+x*1.5,0,100)
        elif k in ['ROE','ROIC']:s=np.clip(x*3,0,100)
        elif k=='ROA':s=np.clip(x*15,0,100)
        elif k in ['Gross Margin','EBITDA Margin','Net Margin','FCF Margin']:s=np.clip(x*2,0,100)
        elif k=='Debt/Equity':s=np.clip(100-max(x,0)*40,0,100)
        elif k=='Net Debt/EBITDA':s=np.clip(100-max(x,0)*18,0,100)
        elif k=='Current Ratio':s=np.clip(x*50,0,100)
        elif k=='Dividend Yield':s=np.clip(x*12,0,100)
        elif k=='P/E':s=np.clip(100-abs(x-12)*4,0,100) if x>0 else np.nan
        elif k=='P/B':s=np.clip(100-abs(x-1.4)*35,0,100) if x>0 else np.nan
        else:s=50
        if np.isfinite(s):fscore.append((s,w[k]))
    financial=sum(s*ww for s,ww in fscore)/sum(ww for _,ww in fscore) if fscore else np.nan
    quality=np.nanmean([forensic['piotroski']*100/9,forensic['earnings_quality'],forensic['roic_quality']])
    valuation=50+np.clip(num(val.get('Upside %')),-50,100)*.35 if pd.notna(num(val.get('Upside %'))) else 50
    technical=num(tech.get('score')); evidence=[]
    if bt.get('trades',0)>=5:evidence.append(np.clip(50+bt.get('expectancy',0)*5,0,100))
    if pd.notna(wfo.get('score')):evidence.append(wfo['score'])
    if bt.get('trades',0)>=5:evidence.append(bt.get('mc_profit_prob',50))
    evidence_score=float(np.mean(evidence)) if evidence else np.nan
    stability=np.nanmean([wfo.get('stability',np.nan),np.clip(100-bt.get('max_dd',50)*2,0,100) if bt.get('trades',0) else np.nan])
    parts=[(financial,.30),(quality,.15),(valuation,.15),(technical,.15),(evidence_score,.15),(stability,.10)]
    avail=[(v,w) for v,w in parts if pd.notna(v)]
    final=sum(v*w for v,w in avail)/sum(w for _,w in avail) if avail else np.nan
    return {'financial':financial,'forensic':quality,'valuation':valuation,'technical':technical,'evidence':evidence_score,'stability':stability,'final':final}

@st.cache_data(ttl=1800,show_spinner=False)
def analyze_one(sym,run_bt=True):
    ds=DataSourceManager(sym).load()
    if not ds.ok: return {'symbol':sym,'error':ds.error}
    raw=ds.data; m,inc,bal,cf,info=normalize_financials(raw); sec=sector(sym,info); m['Working Capital']=np.nan
    pi,tests=piotroski(m,inc,bal,cf); bene=beneish(m); alt=altman(m,sec); eq,accr=earnings_quality(m); rq=roic_quality(m); div=dividend_engine(raw['ticker'],m.get('Price')); m['Dividend Yield']=div.get('yield')
    fin={'sector':sec,'metrics':m}; val=valuation_engine(m,sec)
    try: hist=raw['ticker'].history(period='5y',interval='1d',auto_adjust=False)
    except Exception: hist=pd.DataFrame()
    tech=technical(hist); bt=backtest(hist) if run_bt else {'trades':0}; wfo=wfo_score(hist) if run_bt else {'score':np.nan,'oos_return':np.nan,'stability':np.nan,'folds':0}
    forensic={'piotroski':pi,'beneish':bene,'altman':alt,'earnings_quality':eq,'roic_quality':rq}
    scores=score_stock(fin,forensic,val,tech,bt,wfo,div)
    coverage=np.mean([pd.notna(v) for k,v in m.items() if not k.startswith('_')])*100
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'industry':info.get('industry',''),'metrics':m,'valuation':val,'dividend':div,'technical':tech,'backtest':bt,'wfo':wfo,'forensic':forensic,'scores':scores,'coverage':coverage,'source':'Yahoo Finance','last_date':tech.get('last_date','—')}

@st.cache_data(ttl=1800,show_spinner=False)
def run_all(symbols,run_bt):
    out=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures={ex.submit(analyze_one,s,run_bt):s for s in symbols}
        for f in as_completed(futures):
            try: out.append(f.result())
            except Exception as e: out.append({'symbol':futures[f],'error':str(e)})
    return out

# ---------------- UI ----------------
st.title('🏛️ EGX Institutional Analyzer V5')
st.caption('Financial Intelligence + Real Valuation + Forensic Quality + V9 Technical Evidence + Backtest/WFO/OOS + Monte Carlo + Stability')
with st.sidebar:
    st.header('⚙️ إعدادات المؤسسة')
    min_cov=st.slider('أقل اكتمال بيانات %',0,100,55,5)
    top_n=st.number_input('عدد الأسهم في الترتيب',5,100,20)
    run_bt=st.checkbox('تشغيل Backtest + WFO/OOS + Monte Carlo',True)
    mc_runs=st.selectbox('Monte Carlo', [100,250,500,1000],index=2)
    if st.button('🔄 تحديث كامل'):
        analyze_one.clear(); run_all.clear(); st.rerun()

with st.spinner('🏗️ بناء التحليل المؤسسي...'):
    results=run_all(STOCKS,run_bt)

rows=[]
for r in results:
    if r.get('error') or r.get('coverage',0)<min_cov:continue
    s=r['scores']; v=r['valuation']; t=r['technical']; b=r['backtest']; w=r['wfo']; f=r['forensic']; d=r['dividend']
    rows.append({'الترتيب':0,'السهم':r['symbol'].replace('.CA',''),'القطاع':r['sector'],'الدرجة النهائية':s.get('final'),'المالي':s.get('financial'),'الجودة المحاسبية':s.get('forensic'),'التقييم':s.get('valuation'),'الفني V9':s.get('technical'),'الدليل الإحصائي':s.get('evidence'),'الاستقرار':s.get('stability'),'القيمة العادلة':v.get('Fair Value'),'شراء 20% MOS':v.get('Buy 20% MOS'),'الصعود %':v.get('Upside %'),'Piotroski':f['piotroski'],'Beneish Flags':f['beneish']['risk_flags'],'Altman Z':f['altman']['score'],'جودة الأرباح':f['earnings_quality'],'ROIC Quality':f['roic_quality'],'Dividend Yield %':d.get('yield'),'صفقات Backtest':b.get('trades',0),'Win Rate %':b.get('win_rate',np.nan),'Return %':b.get('return',np.nan),'Max DD %':b.get('max_dd',np.nan),'Profit Factor':b.get('pf',np.nan),'Expectancy %':b.get('expectancy',np.nan),'Sharpe':b.get('sharpe',np.nan),'WFO Score':w.get('score',np.nan),'OOS Return %':w.get('oos_return',np.nan),'MC Median %':b.get('mc50',np.nan),'MC Profit Prob %':b.get('mc_profit_prob',np.nan),'اكتمال البيانات %':r['coverage'],'آخر شمعة':r['last_date']})

df=pd.DataFrame(rows)
if not df.empty:
    df=df.sort_values('الدرجة النهائية',ascending=False,na_position='last').reset_index(drop=True); df['الترتيب']=np.arange(1,len(df)+1)

st.subheader('🏆 الترتيب المؤسسي النهائي')
if df.empty:st.warning('لا توجد نتائج مؤهلة وفق حد اكتمال البيانات.')
else:
    st.dataframe(df.head(int(top_n)),use_container_width=True,hide_index=True)
    st.download_button('⬇️ تنزيل التقرير CSV',df.to_csv(index=False,encoding='utf-8-sig').encode('utf-8-sig'),'EGX_Institutional_V5.csv','text/csv')

st.subheader('🔎 تقرير مؤسسي كامل لسهم')
if results:
    valid=[r for r in results if not r.get('error')]
    sel=st.selectbox('اختر السهم',sorted([r['symbol'] for r in valid]),format_func=lambda x:x.replace('.CA',''))
    r=next(x for x in valid if x['symbol']==sel); s=r['scores']; f=r['forensic']; v=r['valuation']; t=r['technical']; b=r['backtest']; w=r['wfo']; d=r['dividend']
    cols=st.columns(7)
    for c,label,val in zip(cols,['Final Investment Score','Financial','Forensic','Valuation','Technical V9','Evidence','Stability'],[s['final'],s['financial'],s['forensic'],s['valuation'],s['technical'],s['evidence'],s['stability']]):c.metric(label,'—' if pd.isna(val) else f'{val:.1f}')
    st.write(f"**{r['name']}** | القطاع: **{r['sector']}** | آخر شمعة: **{r['last_date']}** | المصدر الأساسي: **{r['source']}** | اكتمال البيانات: **{r['coverage']:.0f}%**")
    st.markdown('### 💰 DCF / FCFF + Sector Relative Valuation')
    st.dataframe(pd.DataFrame([{'النموذج':'DCF/FCFF','القيمة':v.get('DCF/FCFF')},{'النموذج':'Sector Relative','القيمة':v.get('Relative')},{'النموذج':'القيمة العادلة المدمجة','القيمة':v.get('Fair Value')},{'النموذج':'شراء بهامش أمان 20%','القيمة':v.get('Buy 20% MOS')},{'النموذج':'شراء قوي بهامش أمان 30%','القيمة':v.get('Strong Buy 30% MOS')},{'النموذج':'الصعود المحتمل %','القيمة':v.get('Upside %')}]).style.format({'القيمة':'{:.2f}'},na_rep='—'),use_container_width=True,hide_index=True)
    st.markdown('### 🧪 Forensic Accounting')
    st.dataframe(pd.DataFrame([{'المحرك':'Piotroski F-Score','القيمة':f['piotroski'],'المعنى':'قوة مالية تشغيلية'},{'المحرك':'Beneish M-Score','القيمة':f['beneish']['risk_flags'],'المعنى':f['beneish']['status']},{'المحرك':'Altman Z-Score','القيمة':f['altman']['score'],'المعنى':f['altman']['status']},{'المحرك':'Earnings Quality','القيمة':f['earnings_quality'],'المعنى':'جودة الأرباح والتدفقات'},{'المحرك':'ROIC Quality','القيمة':f['roic_quality'],'المعنى':'كفاءة رأس المال'}]).style.format({'القيمة':'{:.2f}'},na_rep='—'),use_container_width=True,hide_index=True)
    st.markdown('### 📈 V9 Technical + Backtest + WFO/OOS + Monte Carlo')
    techdf=pd.DataFrame([{'المؤشر':k,'القيمة':val} for k,val in t.items()]); st.dataframe(techdf,use_container_width=True,hide_index=True)
    evdf=pd.DataFrame([{'المؤشر':k,'القيمة':val} for k,val in b.items()]+[{'المؤشر':k,'القيمة':val} for k,val in w.items()]); st.dataframe(evdf,use_container_width=True,hide_index=True)
    st.markdown('### 💵 Dividend Sustainability')
    st.dataframe(pd.DataFrame([d]),use_container_width=True,hide_index=True)
    st.markdown('### 📊 Financial Normalized Data')
    fm=pd.DataFrame([{'المؤشر':k,'القيمة':val} for k,val in r['metrics'].items() if not k.startswith('_')]); st.dataframe(fm,use_container_width=True,hide_index=True)

st.divider(); st.caption('V5 Institutional: الأسعار والبيانات السوقية تعتمد أساسًا على Yahoo/yfinance في هذه النسخة. طبقة Data Sources مصممة لإضافة المصادر الرسمية والاحتياطية دون تغيير محرك التقييم. النماذج التقييمية والاختبارات الإحصائية أدوات تحليلية وليست ضمانًا للنتائج المستقبلية.')
