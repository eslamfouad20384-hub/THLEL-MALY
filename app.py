# -*- coding: utf-8 -*-
"""EGX Banks Financial Intelligence PRO v1.3
Bank-focused fundamentals, source lineage, annual/quarterly trends, and explicit blanks.
Public-source limitations are shown rather than silently inventing data.
"""
import math, re, time
from datetime import datetime, date, time as dt_time
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup

APP_VERSION = "1.3 Bank Metrics + Lineage"
CACHE_TTL = 1800
CAIRO_TZ = ZoneInfo("Africa/Cairo")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EGXFinancialResearch/1.0)"}

st.set_page_config(page_title="EGX Banks Financial Intelligence PRO", page_icon="🏦", layout="wide", initial_sidebar_state="collapsed")

BANKS = (
    {"symbol":"COMI.CA", "name":"البنك التجاري الدولي - CIB", "short":"CIB", "official":"https://www.cibeg.com/"},
    {"symbol":"HDBK.CA", "name":"بنك التعمير والإسكان", "short":"HDBK", "official":"https://www.hdb-egy.com/"},
    {"symbol":"ADIB.CA", "name":"مصرف أبوظبي الإسلامي - مصر", "short":"ADIB", "official":"https://www.adib.eg/"},
    {"symbol":"CIEB.CA", "name":"بنك قناة السويس", "short":"CIEB", "official":"https://www.scbank.com.eg/"},
    {"symbol":"QNBA.CA", "name":"بنك قطر الوطني الأهلي", "short":"QNBA", "official":"https://www.qnbalahli.com/"},
    {"symbol":"FAIT.CA", "name":"بنك فيصل الإسلامي المصري", "short":"FAIT", "official":"https://www.faisalbank.com.eg/"},
    {"symbol":"EXPA.CA", "name":"البنك المصري لتنمية الصادرات", "short":"EXPA", "official":"https://www.ebank.com.eg/"},
    {"symbol":"EGBE.CA", "name":"البنك المصري الخليجي", "short":"EGBE", "official":"https://www.eg-bank.com/"},
    {"symbol":"SAUD.CA", "name":"بنك الشركة المصرفية العربية الدولية", "short":"SAUD", "official":"https://www.saib.com.eg/"},
    # Kept visible but marked for symbol verification rather than silently removed.
    {"symbol":"CANA.CA", "name":"رمز CANA — يحتاج تحققًا من البورصة", "short":"CANA", "official":"https://www.cbe.org.eg/"},
)

# ---------- helpers ----------
def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else np.nan
    except (TypeError, ValueError):
        return np.nan

def div(a,b):
    a,b=num(a),num(b)
    return a/b if np.isfinite(a) and np.isfinite(b) and b != 0 else np.nan

def first_row(df, candidates, col=None):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty: return np.nan
    lookup = {str(i).strip().lower(): i for i in df.index}
    for cand in candidates:
        if cand.lower() in lookup:
            row = lookup[cand.lower()]
            try: return num(df.loc[row, col if col is not None else df.columns[0]])
            except Exception: pass
    # Match when Yahoo appends labels such as "Net Income From Continuing..."
    for cand in candidates:
        for label, original in lookup.items():
            if cand.lower() in label:
                try: return num(df.loc[original, col if col is not None else df.columns[0]])
                except Exception: pass
    return np.nan

def find_row(df, candidates):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty: return None
    lookup = {str(i).strip().lower(): i for i in df.index}
    for cand in candidates:
        if cand.lower() in lookup: return lookup[cand.lower()]
    for cand in candidates:
        for label, original in lookup.items():
            if cand.lower() in label: return original
    return None

def series_values(df, candidates, limit=5):
    row = find_row(df, candidates)
    if row is None: return []
    out=[]
    for col in list(df.columns)[:limit]:
        out.append((str(pd.Timestamp(col).date()) if not isinstance(col,str) else col, num(df.loc[row,col])))
    return out

def safe_history(symbol):
    now=datetime.now(CAIRO_TZ)
    try:
        h=yf.Ticker(symbol).history(period="1mo", interval="1d", auto_adjust=False, actions=False, raise_errors=False)
        if h is None or h.empty or "Close" not in h: return {"price":np.nan,"price_date":None,"price_source":"Yahoo Finance daily OHLC/Close","price_status":"فشل تحميل الشموع اليومية"}
        h=h[pd.to_numeric(h["Close"],errors="coerce").gt(0)]
        eligible=[]
        for ix,row in h.iterrows():
            d=pd.Timestamp(ix).date()
            if d==now.date() and now.time()<dt_time(15,0): continue
            eligible.append((d,num(row["Close"])))
        if not eligible: return {"price":np.nan,"price_date":None,"price_source":"Yahoo Finance daily OHLC/Close","price_status":"لا توجد شمعة مكتملة متاحة"}
        d,p=max(eligible,key=lambda x:x[0]); age=(now.date()-d).days
        return {"price":p,"price_date":d.isoformat(),"price_source":"Yahoo Finance — Daily OHLC / Close","price_status":"آخر إغلاق يومي متاح" if age<=5 else f"تحذير: الشمعة أقدم من {age} يومًا"}
    except Exception as e:
        return {"price":np.nan,"price_date":None,"price_source":"Yahoo Finance daily OHLC/Close","price_status":f"خطأ: {type(e).__name__}"}

def statement_periods(df):
    if df is None or not isinstance(df,pd.DataFrame) or df.empty: return []
    return [str(pd.Timestamp(c).date()) if not isinstance(c,str) else c for c in df.columns]

def crawl_official_report_links(url, limit=15):
    """Discover PDF links from a bank's public official homepage only; does not assert the PDF is parsed/audited."""
    try:
        resp=requests.get(url,headers=HEADERS,timeout=12)
        if resp.status_code>=400: return []
        soup=BeautifulSoup(resp.text,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            href=urljoin(url,a["href"]); label=" ".join(a.get_text(" ",strip=True).split())
            if ".pdf" in href.lower() or any(k in (label+" "+href).lower() for k in ["annual report","financial statement","financial results","investor relations","القوائم المالية","التقرير السنوي","نتائج الأعمال"]):
                if href.startswith("http") and href not in links: links.append(href)
        return links[:limit]
    except Exception: return []

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def analyze_one(bank_tuple, cost_equity):
    b=dict(bank_tuple); symbol=b["symbol"]
    rec={"symbol":symbol,"name":b["name"],"short":b["short"],"official_home":b.get("official",""),"currency":"", "price":np.nan,"price_date":None,"price_source":"Yahoo Finance — Daily OHLC / Close","price_status":"لم يتم التحميل", "market_cap":np.nan,"book_value_per_share":np.nan,"roe":np.nan,"roa":np.nan,"dividend_yield":np.nan,"trailing_pe":np.nan,"price_to_book":np.nan,"total_revenue":np.nan,"net_income":np.nan,"total_assets":np.nan,"total_equity":np.nan,"total_debt":np.nan,"data_notes":[],"error":""}
    rec.update(safe_history(symbol))
    try:
        t=yf.Ticker(symbol)
        try: info=t.get_info() or {}
        except Exception:
            try: info=t.info or {}
            except Exception: info={}
        mapinfo={"currency":"currency","market_cap":"marketCap","book_value_per_share":"bookValue","roe":"returnOnEquity","roa":"returnOnAssets","dividend_yield":"dividendYield","trailing_pe":"trailingPE","price_to_book":"priceToBook","total_revenue":"totalRevenue","net_income":"netIncomeToCommon","total_assets":"totalAssets","total_equity":"totalStockholderEquity","total_debt":"totalDebt"}
        for out,key in mapinfo.items():
            val=info.get(key)
            if out=="currency": rec[out]=str(val) if val else ""
            else: rec[out]=num(val)
        # statements: retain raw tables for calculations/trends and record their period ends
        try: income=t.income_stmt
        except Exception: income=pd.DataFrame()
        if income is None or income.empty:
            try: income=t.financials
            except Exception: income=pd.DataFrame()
        try: qincome=t.quarterly_income_stmt
        except Exception: qincome=pd.DataFrame()
        try: balance=t.balance_sheet
        except Exception: balance=pd.DataFrame()
        try: qbalance=t.quarterly_balance_sheet
        except Exception: qbalance=pd.DataFrame()
        try: cash=t.cashflow
        except Exception: cash=pd.DataFrame()
        try: qcash=t.quarterly_cashflow
        except Exception: qcash=pd.DataFrame()
        rec["income_periods"]="; ".join(statement_periods(income))
        rec["quarter_periods"]="; ".join(statement_periods(qincome))
        rec["balance_periods"]="; ".join(statement_periods(balance))
        rec["cashflow_periods"]="; ".join(statement_periods(cash))
        # Current-period statement fallbacks
        if not np.isfinite(rec["total_revenue"]): rec["total_revenue"]=first_row(income,["Total Revenue","Operating Revenue","Revenue"])
        if not np.isfinite(rec["net_income"]): rec["net_income"]=first_row(income,["Net Income","Net Income Common Stockholders","Net Income From Continuing Operation Net Minority Interest"])
        if not np.isfinite(rec["total_assets"]): rec["total_assets"]=first_row(balance,["Total Assets"])
        if not np.isfinite(rec["total_equity"]): rec["total_equity"]=first_row(balance,["Stockholders Equity","Total Stockholder Equity","Common Stock Equity"])
        if not np.isfinite(rec["total_debt"]): rec["total_debt"]=first_row(balance,["Total Debt","Long Term Debt","Current Debt"])
        # Bank metric raw components, if provider's statement labels expose them
        rec["loans_gross"]=first_row(balance,["Loans","Loans Receivable","Gross Loans","Loans and Receivables","Loans And Advances To Customers"])
        rec["deposits"]=first_row(balance,["Deposits","Customer Deposits","Deposits by Customers","Due to Customers"])
        rec["npl_amount"]=first_row(balance,["Non Performing Loans","Nonperforming Loans","Impaired Loans","Stage 3 Loans"])
        rec["loan_loss_allowance"]=first_row(balance,["Allowance for Credit Losses","Allowance for Loan Losses","Loan Loss Reserves","Impairment Allowance","Loss Allowance"])
        rec["interest_income"]=first_row(income,["Interest Income","Interest And Similar Income"])
        rec["interest_expense"]=first_row(income,["Interest Expense","Interest And Similar Expense"])
        rec["noninterest_income"]=first_row(income,["Non Interest Income","Noninterest Income","Fee And Commission Income","Net Fee And Commission Income"])
        rec["operating_expenses"]=first_row(income,["Operating Expenses","Non Interest Expense","Noninterest Expense","Total Operating Expenses"])
        rec["cash_from_operations"]=first_row(cash,["Operating Cash Flow","Cash Flow From Continuing Operating Activities","Operating Cash Flow"])
        rec["capital_expenditure"]=first_row(cash,["Capital Expenditure","Capital Expenditures"])
        # Annual and quarterly series (the order comes from Yahoo; preserve period labels)
        rec["annual_revenue_series"]=series_values(income,["Total Revenue","Operating Revenue","Revenue"],5)
        rec["annual_profit_series"]=series_values(income,["Net Income","Net Income Common Stockholders","Net Income From Continuing Operation Net Minority Interest"],5)
        rec["quarter_revenue_series"]=series_values(qincome,["Total Revenue","Operating Revenue","Revenue"],8)
        rec["quarter_profit_series"]=series_values(qincome,["Net Income","Net Income Common Stockholders","Net Income From Continuing Operation Net Minority Interest"],8)
        rec["annual_loans_series"]=series_values(balance,["Loans","Loans Receivable","Gross Loans","Loans and Receivables","Loans And Advances To Customers"],5)
        rec["annual_deposits_series"]=series_values(balance,["Deposits","Customer Deposits","Deposits by Customers","Due to Customers"],5)
        rec["quarter_loans_series"]=series_values(qbalance,["Loans","Loans Receivable","Gross Loans","Loans and Receivables","Loans And Advances To Customers"],8)
        rec["quarter_deposits_series"]=series_values(qbalance,["Deposits","Customer Deposits","Deposits by Customers","Due to Customers"],8)
        # Source metadata: Yahoo provides statement period-end columns, but not a dependable filing publication date.
        rec["yahoo_source"]="Yahoo Finance (yfinance: info + financial statements)"
        rec["financial_period_end"]=(statement_periods(income) or statement_periods(balance) or [None])[0]
        rec["publication_date"]="غير متاح من Yahoo Finance"
        # Derived ratios only if their raw inputs are available and compatible
        rec["LDR"]=div(rec["loans_gross"],rec["deposits"])
        rec["NPL_ratio"]=div(rec["npl_amount"],rec["loans_gross"])
        rec["provision_coverage"]=div(rec["loan_loss_allowance"],rec["npl_amount"])
        rec["cost_income"]=div(rec["operating_expenses"], rec["interest_income"]-rec["interest_expense"]+rec["noninterest_income"])
        # NIM proxy: net interest income / average total assets, not average earning assets. Explicitly labelled proxy.
        prev_assets=num(balance.iloc[balance.index.get_loc(find_row(balance,["Total Assets"])) ,1]) if False else np.nan
        assets_series=series_values(balance,["Total Assets"],2)
        avg_assets=np.mean([v for _,v in assets_series[:2] if np.isfinite(v)]) if sum(np.isfinite(v) for _,v in assets_series[:2])>=2 else np.nan
        rec["NIM_proxy"]=div(rec["interest_income"]-rec["interest_expense"],avg_assets)
        # Cash flow-to-profit indicator; banks' cash flow is volatile and not directly comparable to non-financial firms.
        rec["CFO_to_profit"]=div(rec["cash_from_operations"],rec["net_income"])
        # Official/regulatory ratios are NOT safely inferable from generic balance sheets; leave blank until parsed from official reports.
        for k in ["NIM_official","NPL_official","provision_coverage_official","CAR","LCR","cost_income_official","official_revenue","official_net_income","official_loans","official_deposits"]: rec[k]=np.nan
        rec["official_report_date"]="غير مستخرج تلقائيًا"
        rec["official_report_source"]="الموقع الرسمي للبنك؛ راجع رابط المصدر أدناه"
        rec["official_match_status"]="لم تتم مطابقة رقمية آلية لملف رسمي"
        if not np.isfinite(rec["loans_gross"]): rec["data_notes"].append("القروض غير متاحة بوضوح في قوائم Yahoo؛ LDR سيظل فارغًا")
        if not np.isfinite(rec["deposits"]): rec["data_notes"].append("الودائع غير متاحة بوضوح في قوائم Yahoo؛ LDR سيظل فارغًا")
        if not np.isfinite(rec["npl_amount"]): rec["data_notes"].append("NPL غالبًا يحتاج إفصاحًا رسميًا؛ لم يتم اختلاقه")
    except Exception as e:
        rec["error"]=f"{type(e).__name__}: تعذر تحميل بعض البيانات المالية"
        rec["data_notes"].append("تعذر تحميل القوائم المالية من Yahoo Finance")
    # Valuation retained, with bank-model caveats
    price,bvps,roe,ni,mc=[num(rec.get(k)) for k in ["price","book_value_per_share","roe","net_income","market_cap"]]
    shares=div(mc,price); eps=div(ni,shares)
    pbj=np.clip(roe/cost_equity,0.25,2.5) if np.isfinite(roe) and cost_equity>0 else np.nan
    growth=float(np.clip(roe*0.35,0,0.08)) if np.isfinite(roe) else np.nan
    ri=np.nan
    if np.isfinite(bvps) and bvps>0 and np.isfinite(roe) and np.isfinite(growth) and cost_equity>growth:
        ri=max(0,bvps+((roe-cost_equity)*bvps)/(cost_equity-growth))
    pbv=pbj*bvps if np.isfinite(pbj) and np.isfinite(bvps) and bvps>0 else np.nan
    pev=eps*7 if np.isfinite(eps) and eps>0 else np.nan
    vals=[x for x in [ri,pbv,pev] if np.isfinite(x) and x>0]
    fair=float(np.median(vals)) if vals else np.nan
    rec.update({"eps_estimated":eps,"justified_pb":pbj,"pb_value":pbv,"residual_income_value":ri,"pe_value":pev,"fair_value":fair,"fair_low":float(np.percentile(vals,25)) if len(vals)>=2 else fair*0.85 if np.isfinite(fair) else np.nan,"fair_high":float(np.percentile(vals,75)) if len(vals)>=2 else fair*1.15 if np.isfinite(fair) else np.nan,"buy_10":fair*.9 if np.isfinite(fair) else np.nan,"buy_20":fair*.8 if np.isfinite(fair) else np.nan,"buy_30":fair*.7 if np.isfinite(fair) else np.nan,"upside_pct":div(fair,price)-1 if np.isfinite(fair) and np.isfinite(price) and price>0 else np.nan,"valuation_methods":len(vals)})
    roe,roa,dy,pb,up=[num(rec.get(k)) for k in ["roe","roa","dividend_yield","price_to_book","upside_pct"]]
    components=[]; weights=[]
    for value,den,w in [(roe,.20,25),(roa,.025,15),(dy,.08,10)]:
        if np.isfinite(value): components.append(float(np.clip(value/den,0,1))*w); weights.append(w)
    if np.isfinite(pb) and pb>0: components.append(float(np.clip(1.5/pb,0,1))*15); weights.append(15)
    if np.isfinite(up): components.append(float(np.clip((up+.2)/.6,0,1))*20); weights.append(20)
    qfields=["price","book_value_per_share","roe","roa","trailing_pe","price_to_book","total_revenue","net_income","total_assets","total_equity","dividend_yield","loans_gross","deposits","interest_income","interest_expense"]
    available=sum(np.isfinite(num(rec.get(k))) for k in qfields); q=round(100*available/len(qfields),1); rec["data_quality"]=q
    if weights: raw=sum(components)*75/sum(weights)+15*q/100
    else: raw=15*q/100
    rec["score"]=round(float(np.clip(raw*(.55+.45*q/100),0,100)),1)
    if not np.isfinite(price): rec["recommendation"]="لا يوجد سعر يومي موثوق"
    elif not np.isfinite(fair): rec["recommendation"]="بيانات غير كافية للتقييم"
    elif fair/price>=1.25: rec["recommendation"]="قيمة محتملة — راجع البيانات"
    elif fair/price>=1.05: rec["recommendation"]="مراقبة / تقييم مقبول"
    elif fair/price<.90: rec["recommendation"]="السعر أعلى من القيمة المقدرة"
    else: rec["recommendation"]="محايد"
    # Scenarios: assumptions only
    ra=float(np.clip(roe if np.isfinite(roe) else .12,.05,.25)); g=float(np.clip((ra-.10)*.30,-.02,.06)) if np.isfinite(fair) else np.nan
    rec["target_3y_bear"]=fair*((1+min(g,.01))**3)*.8 if np.isfinite(fair) else np.nan
    rec["target_3y_base"]=fair*((1+g)**3) if np.isfinite(fair) else np.nan
    rec["target_3y_bull"]=fair*((1+max(g+.04,.03))**3)*1.15 if np.isfinite(fair) else np.nan
    return rec

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_all(bank_defs, cost_equity):
    results=[]; errors=[]
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs={pool.submit(analyze_one,tuple(sorted(dict(b).items())),float(cost_equity)):b for b in bank_defs}
        for f in as_completed(futs):
            b=futs[f]
            try: results.append(f.result())
            except Exception as e: errors.append({"symbol":b.get("symbol","?"),"error":type(e).__name__})
    return results,errors

def fmt(v, dec=2):
    x=num(v); return "" if not np.isfinite(x) else round(x,dec)
def pct(v):
    x=num(v); return "" if not np.isfinite(x) else round(x*100,2)
def series_text(x):
    if not x: return ""
    return " | ".join(f"{p}: {v:,.0f}" for p,v in x if np.isfinite(v))
def growth_latest(series):
    """Latest period versus immediately previous period (annual YoY for annual series; quarterly QoQ for quarterly series)."""
    vals=[(p,num(v)) for p,v in series if np.isfinite(num(v))]
    if len(vals)<2 or vals[1][1]==0: return np.nan
    return vals[0][1]/vals[1][1]-1

def growth_quarter_yoy(series):
    """Latest quarter versus the same quarter about one year earlier, if at least five quarters exist."""
    vals=[(p,num(v)) for p,v in series if np.isfinite(num(v))]
    if len(vals)<5 or vals[4][1]==0: return np.nan
    return vals[0][1]/vals[4][1]-1

def build_table(records):
    rows=[]
    for r in records:
        ar=r.get("annual_revenue_series",[]); ap=r.get("annual_profit_series",[]); qr=r.get("quarter_revenue_series",[]); qp=r.get("quarter_profit_series",[])
        al=r.get("annual_loans_series",[]); ad=r.get("annual_deposits_series",[]); ql=r.get("quarter_loans_series",[]); qd=r.get("quarter_deposits_series",[])
        rows.append({
          "الترتيب":0,"البنك":r.get("name"),"الرمز":r.get("symbol"),"السعر - إغلاق يومي":r.get("price"),"تاريخ الشمعة":r.get("price_date"),"حالة السعر":r.get("price_status"),
          "القيمة العادلة التقديرية":r.get("fair_value"),"شراء بخصم 20%":r.get("buy_20"),"العائد المحتمل %":pct(r.get("upside_pct")),"النتيجة /100":r.get("score"),"جودة البيانات %":r.get("data_quality"),
          "NIM منشور %":pct(r.get("NIM_official")),"NIM تقديري بديل %":pct(r.get("NIM_proxy")),"LDR %":pct(r.get("LDR")),"NPL %":pct(r.get("NPL_ratio")),"قيمة القروض المتعثرة":r.get("npl_amount"),"مخصصات خسائر الائتمان":r.get("loan_loss_allowance"),"تغطية المخصصات لـNPL %":pct(r.get("provision_coverage")),"CAR كفاية رأس المال %":pct(r.get("CAR")),"LCR تغطية السيولة %":pct(r.get("LCR")),"Cost-to-Income %":pct(r.get("cost_income")),
          "القروض الحالية":r.get("loans_gross"),"الودائع الحالية":r.get("deposits"),"تطور القروض سنويًا":series_text(al),"تطور الودائع سنويًا":series_text(ad),"تطور القروض ربع سنويًا":series_text(ql),"تطور الودائع ربع سنويًا":series_text(qd),
          "الإيرادات الحالية":r.get("total_revenue"),"نمو الإيرادات سنوي %":pct(growth_latest(ar)),"نمو الإيرادات ربع مقابل السابق %":pct(growth_latest(qr)),"نمو الإيرادات ربع سنوي مقابل نفس الربع العام السابق %":pct(growth_quarter_yoy(qr)),"صافي الربح الحالي":r.get("net_income"),"نمو الربح سنوي %":pct(growth_latest(ap)),"نمو الربح ربع مقابل السابق %":pct(growth_latest(qp)),"نمو الربح ربع سنوي مقابل نفس الربع العام السابق %":pct(growth_quarter_yoy(qp)),"التدفق النقدي التشغيلي":r.get("cash_from_operations"),"التدفق التشغيلي/صافي الربح %":pct(r.get("CFO_to_profit")),
          "نهاية الفترة المالية":r.get("financial_period_end"),"تاريخ نشر القائمة":r.get("publication_date"),"مصدر البيانات الخام":r.get("yahoo_source"),"المصدر الرسمي للبنك":r.get("official_home"),"بوابة إفصاحات البورصة المصرية":"https://www.egx.com.eg/","تاريخ التقرير الرسمي":r.get("official_report_date"),"حالة المطابقة الرسمية":r.get("official_match_status"),"التوصيف":r.get("recommendation"),"ملاحظات": "؛ ".join(r.get("data_notes",[]))
        })
    df=pd.DataFrame(rows)
    if df.empty: return df
    for c in ["النتيجة /100","جودة البيانات %"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.sort_values(["النتيجة /100","جودة البيانات %"],ascending=[False,False],na_position="last").reset_index(drop=True)
    df["الترتيب"]=np.arange(1,len(df)+1)
    return df

# ---------- UI ----------
st.markdown("""<style>html,body,[class*='css']{direction:rtl;text-align:right}.block-container{padding-top:1rem;max-width:1800px}.hero{padding:1rem 1.3rem;border-radius:15px;background:linear-gradient(120deg,#102a43,#176b87);color:#fff;margin-bottom:1rem}.hero h1{color:#fff;margin:0}.small{font-size:.85rem;color:#64748b}</style><div class='hero'><h1>🏦 EGX Banks Financial Intelligence PRO</h1><p>تحليل مالي للبنوك + نسب مخاطر + اتجاهات سنوية وربع سنوية + مصدر وتاريخ لكل رقم متاح</p></div>""",unsafe_allow_html=True)
st.warning("مهم: الحقول غير المتاحة تظهر فارغة، ولا يتم اختلاق نسب رقابية مثل CAR وLCR أو NPL. بيانات Yahoo ليست بديلًا عن القوائم الرسمية، والمقارنة الرسمية الرقمية لا تعتبر مكتملة إلا عند استخراج التقرير والتحقق منه.")
with st.expander("⚙️ إعدادات",expanded=False):
    ce=st.slider("تكلفة حقوق الملكية المفترضة %",15,35,25,1)/100
    if st.button("🔄 مسح الكاش وتحديث البيانات"): st.cache_data.clear(); st.rerun()
    st.caption("NIM البديل محسوب على متوسط إجمالي الأصول عند توفر سنتين، وليس متوسط الأصول المدرة للفائدة؛ لذلك يُعرض منفصلًا عن NIM المنشور.")
if st.button("🚀 تحميل وتحليل البنوك",type="primary",use_container_width=True): st.session_state["run_scan"]=True
if st.session_state.get("run_scan"):
    with st.spinner("تحميل الأسعار والقوائم السنوية والربع سنوية المتاحة..."):
        records,errors=load_all(BANKS,ce)
        # official home page link discovery is deliberately separate and rate-limited
        for r in records:
            r["official_links"]=crawl_official_report_links(r.get("official_home",""),10)
        st.session_state["records"]=records; st.session_state["errors"]=errors; st.session_state["table"]=build_table(records)
if "table" not in st.session_state:
    st.info("اضغط «تحميل وتحليل البنوك» لبدء جلب البيانات.")
else:
    df=st.session_state["table"].copy(); records=st.session_state["records"]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("عدد الرموز",len(df)); c2.metric("سعر يومي متاح",int(df["السعر - إغلاق يومي"].apply(lambda x:np.isfinite(num(x))).sum())); c3.metric("قروض وودائع متاحة",int((df["القروض الحالية"].notna() & df["الودائع الحالية"].notna()).sum())); c4.metric("متوسط جودة الحقول",f"{df['جودة البيانات %'].mean():.1f}%" if len(df) else "—")
    st.subheader("📊 الجدول المالي الشامل — الحقول غير المتاحة تظل فارغة")
    st.caption("استخدم شريط التمرير الأفقي لرؤية كل الأعمدة. نسب CAR وLCR وNPL المنشورة لا تُستنتج من الميزانية العامة؛ تظل فارغة ما لم يتوفر مصدر رسمي موثوق.")
    st.dataframe(df,use_container_width=True,hide_index=True,height=650)
    st.download_button("⬇️ تنزيل الجدول الشامل CSV",df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),file_name=f"EGX_Banks_Full_Analysis_{date.today().isoformat()}.csv",mime="text/csv",use_container_width=True)
    st.subheader("🔎 تفاصيل البنك ومصادره")
    options={f"{r.get('name')} ({r.get('symbol')})":r for r in records}
    r=options[st.selectbox("اختر البنك",list(options))]
    st.markdown(f"**الموقع الرسمي:** {r.get('official_home','')}")
    st.markdown(f"**مصدر البيانات الخام:** {r.get('yahoo_source','Yahoo Finance')}")
    st.write(f"**نهاية الفترة المالية من القوائم المتاحة:** {r.get('financial_period_end','') or 'غير متاحة'}")
    st.write(f"**تاريخ نشر القائمة:** {r.get('publication_date','غير متاح من Yahoo Finance')} — هذا التاريخ لا يساوي نهاية الفترة المالية.")
    st.write(f"**حالة المقارنة الرسمية:** {r.get('official_match_status','')}")
    links=r.get("official_links",[])
    if links:
        st.markdown("**روابط ملفات/صفحات مرشحة من الموقع الرسمي (تحتاج فتحًا والتحقق من كونها أحدث قوائم مالية):**")
        for link in links: st.markdown(f"- [{link}]({link})")
    else: st.info("لم يتم اكتشاف رابط تقرير PDF آليًا من الصفحة الرئيسية. افتح الموقع الرسمي وابحث عن Investor Relations / Financial Statements.")
    st.markdown("#### اتجاهات الإيرادات والأرباح")
    trend=[]
    for label,key in [("إيرادات سنوية","annual_revenue_series"),("أرباح سنوية","annual_profit_series"),("إيرادات ربع سنوية","quarter_revenue_series"),("أرباح ربع سنوية","quarter_profit_series"),("قروض سنوية","annual_loans_series"),("ودائع سنوية","annual_deposits_series"),("قروض ربع سنوية","quarter_loans_series"),("ودائع ربع سنوية","quarter_deposits_series")]:
        vals=r.get(key,[])
        if vals:
            for period,value in vals: trend.append({"السلسلة":label,"الفترة":period,"القيمة":value})
    st.dataframe(pd.DataFrame(trend) if trend else pd.DataFrame(columns=["السلسلة","الفترة","القيمة"]),use_container_width=True,hide_index=True)
    st.markdown("#### منهجية وحدود مهمة")
    st.markdown("""
- **NIM البديل** = صافي دخل الفوائد ÷ متوسط إجمالي الأصول، عند توفر المدخلات. هذا ليس NIM الرسمي لأنه يحتاج الأصول المدرة للفائدة.
- **LDR** = القروض المتاحة ÷ الودائع المتاحة. إذا كانت تسميات Yahoo غير واضحة أو الحقول ناقصة، يظل فارغًا.
- **NPL ونسبة تغطية المخصصات** يحتاجان قيمة القروض المتعثرة والمخصصات المتوافقة في التعريف والفترة؛ لا تُحسب النسبة من إجمالي القروض أو إجمالي الديون كبديل.
- **CAR وLCR** نسب رقابية تتطلب إفصاحات رسمية/رقابية، ولا يمكن استنتاجها بأمان من القوائم العامة.
- **Cost-to-Income** تقديري فقط إذا أمكن تحديد المصروفات التشغيلية ودخل التشغيل بتسميات متوافقة؛ راجع تعريف البنك قبل المقارنة.
- **نمو سنوي/ربع سنوي:** نمو القوائم السنوية يقارن أحدث سنتين؛ وتظهر القوائم الربع سنوية نمو الربع مقابل الربع السابق، وكذلك مقابل نفس الربع قبل سنة إذا توفرت خمسة أرباع على الأقل.
- **التدفقات النقدية** معروضة كما ينشرها المزود، لكن التدفق النقدي التشغيلي للبنوك قد يتذبذب بسبب طبيعة الودائع والقروض، فلا يكفي منفردًا للحكم على استدامة الأرباح.
- **المصدر الرسمي:** التطبيق يحاول اكتشاف روابط من الصفحة الرئيسية للبنك، لكنه لا يدّعي أنه قرأ أو طابق محتوى كل PDF تلقائيًا. حقول المقارنة الرسمية تظل فارغة حتى يتوفر استخراج موثوق.
- **تاريخ النشر:** Yahoo Finance لا يوفر دائمًا تاريخ نشر القائمة بشكل موثوق؛ لذلك يظهر «غير متاح» بدل استخدام نهاية الفترة المالية كأنها تاريخ نشر.
""")
    if st.session_state.get("errors"):
        with st.expander("أخطاء تحميل عامة"): st.dataframe(pd.DataFrame(st.session_state["errors"]),use_container_width=True,hide_index=True)
st.markdown(f"<p class='small'>EGX Banks Financial Intelligence PRO · {APP_VERSION} · البيانات العامة قد تكون ناقصة أو متأخرة.</p>",unsafe_allow_html=True)
