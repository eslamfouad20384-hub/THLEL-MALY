import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
EGX100 = ['COMI.CA', 'MFPC.CA', 'PHDC.CA', 'ORAS.CA', 'HDBK.CA', 'EFIH.CA', 'AMES.CA', 'INEG.CA', 'BTFH.CA', 'BIOC.CA', 'CLHO.CA', 'MBSC.CA', 'MTIE.CA', 'EGTS.CA', 'EGSA.CA', 'MHOT.CA', 'EGBE.CA', 'IFAP.CA', 'PRDC.CA', 'MIPH.CA', 'MPCI.CA', 'MOIN.CA', 'ISMQ.CA', 'AXPH.CA', 'PHTV.CA', 'CPCI.CA', 'NINH.CA', 'SPIN.CA', 'ENGC.CA', 'CNFN.CA', 'SVCE.CA', 'KABO.CA', 'OFH.CA', 'GSSC.CA', 'WCDF.CA', 'MFSC.CA', 'SAIB.CA', 'ACGC.CA', 'UEFM.CA', 'KZPC.CA', 'ADCI.CA', 'INFI.CA', 'ASCM.CA', 'VALU.CA', 'ZEOT.CA', 'SMFR.CA', 'ETRS.CA', 'CIRA.CA', 'QNBE.CA', 'EDFM.CA', 'MILS.CA', 'GBCO.CA', 'ACTF.CA', 'SCTS.CA', 'HRHO.CA', 'TMGH.CA', 'FWRY.CA', 'SWDY.CA', 'ETEL.CA', 'AMOC.CA', 'HELI.CA', 'EAST.CA', 'EFID.CA', 'JUFO.CA', 'ABUK.CA', 'ESRS.CA', 'EMFD.CA', 'CCAP.CA', 'ACAP.CA', 'CICH.CA', 'OCDI.CA', 'ORHD.CA', 'MASR.CA', 'AIHC.CA', 'ADIB.CA', 'SAUD.CA', 'CIEB.CA', 'FAIT.CA', 'AFDI.CA', 'CANA.CA', 'EXPA.CA', 'ARCC.CA', 'AJWA.CA', 'MICH.CA', 'SUGR.CA', 'POUL.CA', 'DOMT.CA', 'ISMA.CA', 'UEGC.CA', 'FERC.CA', 'UBEE.CA', 'FAITA.CA', 'MNHD.CA', 'SUCE.CA', 'SMPP.CA', 'ALEX.CA', 'CRST.CA', 'DCRC.CA', 'DIFC.CA', 'MAAL.CA', 'GGRN.CA', 'GGCC.CA', 'IEEC.CA', 'NDRL.CA', 'EFIC.CA', 'GPIM.CA', 'RTVC.CA', 'RUBX.CA', 'PRMH.CA', 'UNIP.CA', 'TWSA.CA', 'ICLE.CA', 'MEGM.CA', 'EASB.CA', 'APSW.CA', 'MOED.CA', 'KWIN.CA', 'RUBX.CA', 'KORA.CA', 'RMDA.CA', 'OIH.CA', 'NAPR.CA', 'BONY.CA', 'SPHT.CA', 'SDTI.CA', 'GTWL.CA', 'CFGH.CA', 'NAHO.CA', 'ACAMD.CA', 'NARE.CA', 'CEFM.CA', 'ASPI.CA', 'SCFM.CA', 'CERA.CA', 'DEIN.CA', 'MBEG.CA', 'SIPC.CA', 'NHPS.CA', 'ROTO.CA', 'TYCN.CA', 'RAKT.CA', 'EEII.CA', 'CCRS.CA', 'AREH.CA', 'EPCO.CA', 'FCMD.CA', 'GRCA.CA', 'GIHD.CA', 'ELWA.CA', 'MMAT.CA', 'NEDA.CA', 'EPPK.CA', 'GMCI.CA', 'CPME.CA', 'VLMR.CA', 'GPPL.CA', 'ADPC.CA', 'ADRI.CA', 'AIDC.CA', 'OBRI.CA', 'RREI.CA', 'RKAZ.CA', 'SEIG.CA', 'SNFC.CA', 'TANM.CA', 'UPMS.CA', 'UTOP.CA', 'VERT.CA', 'WKOL.CA', 'LUTS.CA', 'AIFI.CA', 'AMIA.CA', 'AMII.CA', 'ACRO.CA', 'DGTZ.CA', 'DTPP.CA', 'EALR.CA', 'EBSC.CA', 'EGREF.CA', 'EHDR.CA', 'ELNA.CA', 'EOSB.CA', 'FIRE.CA', 'FNAR.CA', 'FTNS.CA', 'GOUR.CA', 'ICID.CA', 'IDRE.CA', 'KASABF.CA', 'KRDI.CA', 'LCSW.CA', 'MOSC.CA', 'TAQA.CA', 'OLFI.CA', 'SKPC.CA', 'AMER.CA', 'TALM.CA', 'ALUM.CA', 'ORWE.CA', 'SPMD.CA', 'ZMID.CA', 'MENA.CA', 'DAPH.CA', 'RAYA.CA', 'EGAL.CA', 'ECAP.CA', 'MPRC.CA', 'AFMC.CA', 'NCCW.CA', 'SCEM.CA', 'ARAB.CA', 'GDWA.CA', 'ELEC.CA', 'IRON.CA', 'ATQA.CA', 'EGCH.CA', 'ALCN.CA', 'LCSW.CA', 'MPCO.CA', 'ELSH.CA', 'MEPA.CA', 'ODIN.CA', 'EGAS.CA', 'RACC.CA', 'PRCL.CA', 'BINV.CA', 'EDBM.CA', 'MCQE.CA', 'MOIL.CA', 'NIPH.CA', 'ISPH.CA', 'DSCW.CA', 'AALR.CA', 'UNIT.CA', 'PHAR.CA', 'TRTO.CA', 'CAED.CA', 'CSAG.CA', 'ICFC.CA', 'ELKA.CA', 'PHGC.CA', 'NCGC.CA', 'MCRO.CA', 'ATLC.CA', 'COSG.CA', 'AMPI.CA', 'COPR.CA', 'OCPH.CA']
EGX_UNIVERSE = list(dict.fromkeys(EGX100))
TOTAL_STOCKS = len(EGX_UNIVERSE)
EGX100 = EGX_UNIVERSE
MIN_DAILY_ROWS = 60
MIN_WEEKLY_ROWS = 80
MIN_MONTHLY_ROWS = 36
DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 2
EMA200_REQUIRED_ROWS = 200
PIVOT_RADIUS = 3
LIQUIDITY_LOOKBACK = 20
RS_LOOKBACK = 20
DEFAULT_MAX_POSITION_PCT = 20.0

@st.cache_data(ttl=21600, show_spinner=False)
def load_data(symbols, period, interval):
    # Same data/logic as the original loader, but cached for 6 hours and
    # downloaded as one batch per timeframe. threads=False avoids nested
    # threading because scan_universe already parallelizes the stock analysis.
    if not symbols:
        return pd.DataFrame()
    symbols = tuple(dict.fromkeys(symbols))
    last_error = None
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            data = yf.download(tickers=list(symbols), period=period, interval=interval, group_by='ticker', threads=False, auto_adjust=True, progress=False, timeout=30)
            if data is not None and (not data.empty):
                return data
            last_error = 'Yahoo returned empty data'
        except Exception as e:
            last_error = str(e)
        if attempt < DOWNLOAD_RETRIES - 1:
            time.sleep(DOWNLOAD_RETRY_DELAY * (attempt + 1))
    return pd.DataFrame()

def extract_symbol_data(data, symbol):
    try:
        if data is None or data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            level0 = data.columns.get_level_values(0)
            level1 = data.columns.get_level_values(1)
            if symbol in level0:
                df = data[symbol].copy()
            elif symbol in level1:
                df = data.xs(symbol, axis=1, level=1).copy()
            else:
                return pd.DataFrame()
        else:
            df = data.copy()
        df.columns = [str(c).strip() for c in df.columns]
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all((c in df.columns for c in required)):
            return pd.DataFrame()
        df = df[required].copy()
        for col in required:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        df['Volume'] = df['Volume'].fillna(0)
        df = df[(df['High'] >= df['Low']) & (df['Close'] > 0) & (df['Open'] > 0)]
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='last')]
        return df
    except Exception:
        return pd.DataFrame()

def calculate_data_quality(df):
    if df is None or df.empty:
        return {'quality': 0.0, 'missing': 100.0, 'rows': 0}
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    total_cells = len(df) * len(required)
    missing_cells = int(df[required].isna().sum().sum())
    missing_pct = missing_cells / total_cells * 100 if total_cells > 0 else 100
    quality = max(0.0, 100.0 - missing_pct)
    if len(df) < 50:
        quality *= len(df) / 50
    return {'quality': round(quality, 2), 'missing': round(missing_pct, 2), 'rows': len(df)}

def atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

def adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm_raw = high.diff()
    minus_dm_raw = -low.diff()
    plus_dm = np.where((plus_dm_raw > minus_dm_raw) & (plus_dm_raw > 0), plus_dm_raw, 0.0)
    minus_dm = np.where((minus_dm_raw > plus_dm_raw) & (minus_dm_raw > 0), minus_dm_raw, 0.0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr_val = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / (atr_val + 1e-09)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / (atr_val + 1e-09)
    dx = abs(plus_di - minus_di) / (plus_di + minus_di + 1e-09) * 100
    return dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

def linear_slope(series, window=10):
    if len(series) < window:
        return np.nan
    values = series.iloc[-window:].values.astype(float)
    if not np.all(np.isfinite(values)):
        return np.nan
    x = np.arange(window)
    try:
        slope = np.polyfit(x, values, 1)[0]
        return float(slope)
    except Exception:
        return np.nan

def add_indicators(df):
    df = df.copy()
    if len(df) < 30:
        return df
    close = df['Close']
    high = df['High']
    low = df['Low']
    vol = df['Volume']
    df['ema20'] = close.ewm(span=20, adjust=False).mean()
    df['ema50'] = close.ewm(span=50, adjust=False).mean()
    if len(df) >= EMA200_REQUIRED_ROWS:
        df['ema200'] = close.ewm(span=200, adjust=False, min_periods=200).mean()
        df['ema200_complete'] = True
    else:
        df['ema200'] = np.nan
        df['ema200_complete'] = False
    df['rsi'] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    macd_obj = ta.trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    df['macd'] = macd_obj.macd()
    df['macd_signal'] = macd_obj.macd_signal()
    df['macd_hist'] = macd_obj.macd_diff()
    df['vol_ma'] = vol.rolling(20, min_periods=10).mean()
    df['volume_ratio'] = vol / (df['vol_ma'] + 1e-09)
    try:
        df['obv'] = ta.volume.OnBalanceVolumeIndicator(close=close, volume=vol).on_balance_volume()
        df['obv_ma'] = df['obv'].rolling(20, min_periods=10).mean()
        df['obv_slope'] = df['obv'] - df['obv'].shift(5)
    except Exception:
        df['obv'] = np.nan
        df['obv_ma'] = np.nan
        df['obv_slope'] = np.nan
    try:
        df['mfi'] = ta.volume.MFIIndicator(high=high, low=low, close=close, volume=vol, window=14).money_flow_index()
    except Exception:
        df['mfi'] = np.nan
    try:
        stoch = ta.momentum.StochRSIIndicator(close=close, window=14, smooth1=3, smooth2=3)
        df['stoch_rsi'] = stoch.stochrsi()
        df['stoch_rsi_k'] = stoch.stochrsi_k()
        df['stoch_rsi_d'] = stoch.stochrsi_d()
        df['stoch_rsi_k_slope'] = df['stoch_rsi_k'] - df['stoch_rsi_k'].shift(1)
    except Exception:
        df['stoch_rsi'] = np.nan
        df['stoch_rsi_k'] = np.nan
        df['stoch_rsi_d'] = np.nan
        df['stoch_rsi_k_slope'] = np.nan
    try:
        typical_price = (high + low + close) / 3
        cumulative_volume = vol.cumsum()
        df['vwap'] = (typical_price * vol).cumsum() / (cumulative_volume + 1e-09)
        df['vwap_distance'] = (close - df['vwap']) / (close + 1e-09)
    except Exception:
        df['vwap'] = np.nan
        df['vwap_distance'] = np.nan
    df['atr'] = atr(df, 14)
    df['atr_pct'] = df['atr'] / (close + 1e-09)
    df['adx'] = adx(df, 14)
    df['support'] = low.rolling(20, min_periods=10).min()
    df['resistance'] = high.rolling(20, min_periods=10).max()
    df['previous_support'] = low.rolling(20, min_periods=10).min().shift(1)
    df['previous_resistance'] = high.rolling(20, min_periods=10).max().shift(1)
    df['swing_high_20'] = high.rolling(20, min_periods=10).max().shift(1)
    df['swing_low_20'] = low.rolling(20, min_periods=10).min().shift(1)
    df['swing_high_60'] = high.rolling(60, min_periods=20).max().shift(1)
    df['swing_low_60'] = low.rolling(60, min_periods=20).min().shift(1)
    swing_high = high.rolling(60, min_periods=20).max()
    swing_low = low.rolling(60, min_periods=20).min()
    fib_range = swing_high - swing_low
    df['fib_236'] = swing_high - fib_range * 0.236
    df['fib_382'] = swing_high - fib_range * 0.382
    df['fib_500'] = swing_high - fib_range * 0.5
    df['fib_618'] = swing_high - fib_range * 0.618
    df['fib_786'] = swing_high - fib_range * 0.786
    df['fib_ext_1272'] = swing_low + fib_range * 1.272
    df['fib_ext_1618'] = swing_low + fib_range * 1.618
    df['fib_ext_2000'] = swing_low + fib_range * 2.0
    df['ema20_slope'] = (df['ema20'] - df['ema20'].shift(5)) / (df['Close'] + 1e-09)
    df['ema50_slope'] = (df['ema50'] - df['ema50'].shift(5)) / (df['Close'] + 1e-09)
    candle_range = (high - low).replace(0, np.nan)
    df['body_pct'] = abs(close - df['Open']) / candle_range
    df['bullish_candle'] = close > df['Open']
    df['atr_expansion'] = df['atr'] / (df['atr'].rolling(20, min_periods=10).mean() + 1e-09)
    previous_resistance = high.rolling(20, min_periods=10).max().shift(1)
    close_above_resistance = close > previous_resistance
    breakout_volume = df['volume_ratio'] >= 1.3
    breakout_volume_strong = df['volume_ratio'] >= 1.5
    atr_is_healthy = df['atr_pct'] >= 0.015
    atr_not_extreme = df['atr_pct'] <= 0.12
    candle_quality = df['body_pct'] >= 0.45
    bullish_candle = df['bullish_candle']
    trend_breakout = (close > df['ema20']) & (df['ema20'] > df['ema50'])
    df['breakout'] = close_above_resistance & breakout_volume & atr_is_healthy & atr_not_extreme & candle_quality & bullish_candle & trend_breakout
    distance_ema20 = abs(close - df['ema20']) / (close + 1e-09)
    distance_ema50 = abs(close - df['ema50']) / (close + 1e-09)
    near_ema20 = distance_ema20 <= 0.025
    near_ema50 = distance_ema50 <= 0.035
    trend_bullish = (close > df['ema50']) & (df['ema20'] > df['ema50']) & (df['ema20_slope'] > 0)
    support_near = abs(close - df['previous_support']) / (close + 1e-09) <= 0.04
    fib_support_near = (abs(close - df['fib_382']) / (close + 1e-09) <= 0.025) | (abs(close - df['fib_500']) / (close + 1e-09) <= 0.025) | (abs(close - df['fib_618']) / (close + 1e-09) <= 0.025)
    close_location = (close - low) / (candle_range + 1e-09)
    selling_pressure_reduced = (df['volume_ratio'] <= 1.3) & (close_location >= 0.45)
    bullish_confirmation = bullish_candle & (body := df['body_pct']).ge(0.35) | (close > df['ema20'])
    pullback_score = trend_bullish.astype(int) * 2 + (near_ema20 | near_ema50).astype(int) * 2 + support_near.astype(int) + fib_support_near.astype(int) + selling_pressure_reduced.astype(int) + bullish_confirmation.astype(int)
    df['pullback_quality_score'] = pullback_score
    df['pullback'] = (pullback_score >= 6) & trend_bullish
    w = PIVOT_RADIUS * 2 + 1
    ph_candidate = high.eq(high.rolling(w, center=True, min_periods=w).max())
    pl_candidate = low.eq(low.rolling(w, center=True, min_periods=w).min())
    df['confirmed_swing_high_raw'] = high.where(ph_candidate).shift(PIVOT_RADIUS)
    df['confirmed_swing_low_raw'] = low.where(pl_candidate).shift(PIVOT_RADIUS)
    df['confirmed_swing_high'] = df['confirmed_swing_high_raw'].ffill()
    df['confirmed_swing_low'] = df['confirmed_swing_low_raw'].ffill()
    idx_num = pd.Series(np.arange(len(df), dtype=float), index=df.index)
    df['confirmed_high_idx'] = idx_num.where(ph_candidate).shift(PIVOT_RADIUS).ffill()
    df['confirmed_low_idx'] = idx_num.where(pl_candidate).shift(PIVOT_RADIUS).ffill()
    bull_leg = df['confirmed_low_idx'].notna() & df['confirmed_high_idx'].notna() & (df['confirmed_low_idx'] < df['confirmed_high_idx'])
    fib_hi = df['confirmed_swing_high']
    fib_lo = df['confirmed_swing_low']
    fib_range_confirmed = (fib_hi - fib_lo).where(bull_leg)
    for ratio, col in [(0.236, 'fib_236'), (0.382, 'fib_382'), (0.5, 'fib_500'), (0.618, 'fib_618'), (0.786, 'fib_786')]:
        df[col] = (fib_hi - fib_range_confirmed * ratio).where(fib_range_confirmed > 0)
    df['fib_ext_1272'] = (fib_hi + fib_range_confirmed * 0.272).where(fib_range_confirmed > 0)
    df['fib_ext_1618'] = (fib_hi + fib_range_confirmed * 0.618).where(fib_range_confirmed > 0)
    df['fib_ext_2000'] = (fib_hi + fib_range_confirmed * 1.0).where(fib_range_confirmed > 0)
    df['turnover'] = close * vol
    df['turnover_ma20'] = df['turnover'].rolling(LIQUIDITY_LOOKBACK, min_periods=10).median()
    df['liquidity_ratio'] = df['turnover'] / (df['turnover_ma20'] + 1e-09)
    df['return_20d'] = close.pct_change(RS_LOOKBACK)
    return df

def market_regime(last):
    score = 0
    checks = [np.isfinite(last.get('ema200', np.nan)) and last['Close'] > last['ema200'], last['ema20'] > last['ema50'], np.isfinite(last.get('ema200', np.nan)) and last['ema50'] > last['ema200'], last['macd'] > last['macd_signal'], last['rsi'] > 50, last['adx'] > 20]
    score = sum(checks)
    if score >= 6:
        return '🚀 قوي جداً'
    elif score >= 4:
        return '🟢 صعود'
    elif score >= 3:
        return '🟡 محايد'
    else:
        return '🔴 هبوط'

def timeframe_score(df):
    if df is None or df.empty:
        return 0
    last = df.iloc[-1]
    score = 0
    if np.isfinite(last.get('ema200', np.nan)) and last['Close'] > last['ema200']:
        score += 25
    if last['ema20'] > last['ema50']:
        score += 20
    if np.isfinite(last.get('ema200', np.nan)) and last['ema50'] > last['ema200']:
        score += 20
    if last['macd'] > last['macd_signal']:
        score += 15
    if last['rsi'] > 50:
        score += 10
    if last['ema20_slope'] > 0:
        score += 10
    if not bool(last.get('ema200_complete', False)):
        score = min(score, 55)
    return score

def trend_alignment_score(df_d, df_w, df_m):
    daily_score = timeframe_score(df_d)
    weekly_score = timeframe_score(df_w)
    monthly_score = timeframe_score(df_m)
    alignment = daily_score * 0.4 + weekly_score * 0.35 + monthly_score * 0.25
    return min(100, max(0, alignment))

def calculate_pullback_entry(df_d):
    last = df_d.iloc[-1]
    close = float(last['Close'])
    atr_val = float(last.get('atr', close * 0.03))
    if not np.isfinite(atr_val) or atr_val <= 0:
        atr_val = close * 0.03
    levels = []
    candidates = [('Confirmed Support', last.get('previous_support', np.nan)), ('Confirmed Swing Low', last.get('confirmed_swing_low', np.nan)), ('EMA20', last.get('ema20', np.nan)), ('EMA50', last.get('ema50', np.nan)), ('Fib 38.2%', last.get('fib_382', np.nan)), ('Fib 50%', last.get('fib_500', np.nan)), ('Fib 61.8%', last.get('fib_618', np.nan))]
    for name, level in candidates:
        try:
            level = float(level)
            if np.isfinite(level) and level > 0 and (level <= close):
                levels.append((name, level))
        except Exception:
            pass
    if not levels:
        return (close, 'لا توجد منطقة Pullback مؤكدة أسفل السعر')
    max_distance = max(atr_val * 1.5, close * 0.06)
    nearby = [x for x in levels if close - x[1] <= max_distance]
    if not nearby:
        return (close, 'لا يوجد Pullback قريب بما يكفي؛ انتظار تأكيد سعري')
    priority = {'Confirmed Support': 1, 'Confirmed Swing Low': 2, 'Fib 61.8%': 3, 'Fib 50%': 4, 'Fib 38.2%': 5, 'EMA50': 6, 'EMA20': 7}
    name, price = min(nearby, key=lambda x: (priority.get(x[0], 99), abs(close - x[1])))
    return (float(price), f'منطقة {name} مؤكدة + مسافة Pullback ضمن {max_distance / close * 100:.1f}%')

def determine_entry(df_d, alignment):
    last = df_d.iloc[-1]
    market_price = float(last['Close'])
    previous_resistance = float(last.get('previous_resistance', np.nan))
    ema20 = float(last['ema20'])
    ema50 = float(last['ema50'])
    breakout = bool(last.get('breakout', False))
    pullback = bool(last.get('pullback', False))
    volume_ratio = float(last['volume_ratio'])
    atr_pct = float(last['atr_pct'])
    body_pct = float(last.get('body_pct', 0))
    if breakout and np.isfinite(previous_resistance) and (market_price > previous_resistance) and (volume_ratio >= 1.5) and (0.015 <= atr_pct <= 0.12) and (body_pct >= 0.45) and (alignment >= 60):
        return {'type': 'دخول اختراق', 'price': market_price, 'reason': 'اختراق مقاومة سابقة + حجم قوي + شمعة اختراق جيدة + ATR مناسب + Trend Alignment قوي'}
    if pullback and ema20 > ema50 and (alignment >= 55):
        pullback_price, pullback_reason = calculate_pullback_entry(df_d)
        return {'type': 'دخول عند Pullback', 'price': pullback_price, 'reason': 'اتجاه صاعد + منطقة دعم/EMA/Fibonacci + انخفاض ضغط البيع + تأكيد سعري | ' + pullback_reason}
    if market_price > ema20 and market_price > ema50 and (last['rsi'] >= 50) and (last['macd'] > last['macd_signal']) and (market_price > last['vwap']) and (volume_ratio >= 1.0) and (alignment >= 50):
        return {'type': 'دخول فوري', 'price': market_price, 'reason': 'السعر فوق EMA20/50 وVWAP + RSI إيجابي + MACD إيجابي + حجم مقبول + Trend Alignment'}
    return {'type': 'انتظار تأكيد', 'price': market_price, 'reason': 'لا توجد حاليًا شروط كافية لدخول اختراق أو Pullback أو دخول فوري'}

def add_target_level(levels, price, reason, category):
    try:
        price = float(price)
        if np.isfinite(price) and price > 0:
            levels.append({'price': price, 'reason': reason, 'category': category})
    except Exception:
        pass

def deduplicate_levels(levels, tolerance):
    if not levels:
        return []
    levels = sorted(levels, key=lambda x: x['price'])
    result = []
    for level in levels:
        if not result:
            result.append(level)
        else:
            previous = result[-1]
            relative_gap = abs(level['price'] - previous['price']) / max(previous['price'], 1e-09)
            if relative_gap >= tolerance:
                result.append(level)
            else:
                priority = {'Resistance': 1, 'Swing High': 2, 'Weekly': 3, 'Monthly': 4, 'Fibonacci': 5, 'ATR': 6}
                old_priority = priority.get(previous['category'], 99)
                new_priority = priority.get(level['category'], 99)
                if new_priority < old_priority:
                    result[-1] = level
    return result

def calculate_risk_engine(df_d, entry, capital, risk_percent, df_w=None, df_m=None):
    last = df_d.iloc[-1]
    support = float(last.get('previous_support', np.nan))
    atr_val = float(last.get('atr', np.nan))
    if not np.isfinite(atr_val) or atr_val <= 0:
        atr_val = entry * 0.03
    bullish = bool(last.get('ema20', entry) > last.get('ema50', entry))
    stop_candidates = []
    for level in [support, last.get('confirmed_swing_low', np.nan)]:
        try:
            level = float(level)
            if np.isfinite(level) and 0 < level < entry:
                stop_candidates.append(level - atr_val * 0.2)
        except Exception:
            pass
    stop_candidates.append(entry - atr_val * (1.5 if bullish else 1.2))
    stop_candidates = [x for x in stop_candidates if np.isfinite(x) and 0 < x < entry]
    stop = max(stop_candidates) if stop_candidates else entry * 0.95
    risk_per_share = entry - stop
    if risk_per_share <= 0 or not np.isfinite(risk_per_share):
        risk_per_share = entry * 0.03
        stop = entry - risk_per_share
    risk_pct_actual = risk_per_share / entry
    allowed_loss = capital * risk_percent / 100.0
    position_size = allowed_loss / risk_per_share
    max_position_value = capital * (DEFAULT_MAX_POSITION_PCT / 100.0)
    position_size = min(position_size, max_position_value / entry)
    position_value = position_size * entry
    levels = []

    def add(price, reason, category):
        try:
            price = float(price)
            if np.isfinite(price) and price > entry:
                levels.append({'price': price, 'reason': reason, 'category': category})
        except Exception:
            pass
    add(last.get('previous_resistance', np.nan), 'المقاومة اليومية السابقة', 'Resistance')
    add(last.get('resistance', np.nan), 'المقاومة اليومية الحالية', 'Resistance')
    add(last.get('confirmed_swing_high', np.nan), 'آخر Swing High مؤكد', 'Swing High')
    for col, reason, cat in [('fib_ext_1272', 'Fibonacci Extension 127.2% مبني على Swing مؤكد', 'Fibonacci'), ('fib_ext_1618', 'Fibonacci Extension 161.8% مبني على Swing مؤكد', 'Fibonacci'), ('fib_ext_2000', 'Fibonacci Extension 200% مبني على Swing مؤكد', 'Fibonacci')]:
        add(last.get(col, np.nan), reason, cat)
    if df_w is not None and (not df_w.empty):
        try:
            w_high = df_w['High'].rolling(20, min_periods=10).max().shift(1).iloc[-1]
            add(w_high, 'مقاومة Weekly سابقة', 'Weekly')
        except Exception:
            pass
    if df_m is not None and (not df_m.empty):
        try:
            m_high = df_m['High'].rolling(12, min_periods=6).max().shift(1).iloc[-1]
            add(m_high, 'مقاومة Monthly سابقة', 'Monthly')
        except Exception:
            pass
    priority = {'Resistance': 1, 'Swing High': 2, 'Weekly': 3, 'Monthly': 4, 'Fibonacci': 5}
    levels.sort(key=lambda x: x['price'])
    dedup = []
    for x in levels:
        if not dedup or abs(x['price'] - dedup[-1]['price']) / max(dedup[-1]['price'], 1e-09) >= 0.008:
            dedup.append(x)
        elif priority.get(x['category'], 99) < priority.get(dedup[-1]['category'], 99):
            dedup[-1] = x
    min_gap = max(atr_val * 0.4, entry * 0.012)
    selected = []
    for x in dedup:
        if not selected or x['price'] >= selected[-1]['price'] + min_gap:
            selected.append(x)
        if len(selected) >= 4:
            break
    while len(selected) < 4:
        selected.append({'price': np.nan, 'reason': 'لا يوجد مستوى سعري هيكلي موثوق كافٍ', 'category': 'غير متاح'})
    prices = [x['price'] for x in selected]
    profits = [(p - entry) / entry * 100 if np.isfinite(p) else np.nan for p in prices]
    rr = [(p - entry) / risk_per_share if np.isfinite(p) else np.nan for p in prices]
    points = {'Resistance': 1.0, 'Swing High': 0.95, 'Weekly': 0.9, 'Monthly': 0.9, 'Fibonacci': 0.8, 'غير متاح': 0.0}
    target_quality = float(np.mean([points.get(x['category'], 0.0) for x in selected]) * 100)
    structural_count = sum(np.isfinite(prices))
    return {'entry': float(entry), 'stop': float(stop), 'tp1': float(prices[0]) if np.isfinite(prices[0]) else np.nan, 'tp2': float(prices[1]) if np.isfinite(prices[1]) else np.nan, 'tp3': float(prices[2]) if np.isfinite(prices[2]) else np.nan, 'tp4': float(prices[3]) if np.isfinite(prices[3]) else np.nan, 'tp1_profit_pct': float(profits[0]) if np.isfinite(profits[0]) else np.nan, 'tp2_profit_pct': float(profits[1]) if np.isfinite(profits[1]) else np.nan, 'tp3_profit_pct': float(profits[2]) if np.isfinite(profits[2]) else np.nan, 'tp4_profit_pct': float(profits[3]) if np.isfinite(profits[3]) else np.nan, 'tp1_reason': selected[0]['reason'], 'tp2_reason': selected[1]['reason'], 'tp3_reason': selected[2]['reason'], 'tp4_reason': selected[3]['reason'], 'tp1_category': selected[0]['category'], 'tp2_category': selected[1]['category'], 'tp3_category': selected[2]['category'], 'tp4_category': selected[3]['category'], 'rr1': float(rr[0]) if np.isfinite(rr[0]) else np.nan, 'rr2': float(rr[1]) if np.isfinite(rr[1]) else np.nan, 'rr3': float(rr[2]) if np.isfinite(rr[2]) else np.nan, 'rr4': float(rr[3]) if np.isfinite(rr[3]) else np.nan, 'target_quality': target_quality, 'risk_pct': float(risk_pct_actual * 100), 'position_size': float(position_size), 'position_value': float(position_value), 'structural_target_count': structural_count}

def ai_confidence(last_d, last_w, last_m, alignment, data_quality):
    score = 0
    total = 13
    if np.isfinite(last_d.get('ema200', np.nan)) and last_d['Close'] > last_d['ema200']:
        score += 1
    if np.isfinite(last_w.get('ema200', np.nan)) and last_w['Close'] > last_w['ema200']:
        score += 1
    if np.isfinite(last_m.get('ema200', np.nan)) and last_m['Close'] > last_m['ema200']:
        score += 1
    if last_d['macd'] > last_d['macd_signal']:
        score += 1
    if 45 < last_d['rsi'] < 70:
        score += 1
    if last_d['volume_ratio'] > 1:
        score += 1
    if last_d['adx'] > 20:
        score += 1
    if 40 < last_d['mfi'] < 80:
        score += 1
    if np.isfinite(last_d['obv']) and np.isfinite(last_d['obv_ma']) and (last_d['obv'] > last_d['obv_ma']):
        score += 1
    if np.isfinite(last_d['stoch_rsi_k']) and np.isfinite(last_d['stoch_rsi_d']) and (last_d['stoch_rsi_k'] > last_d['stoch_rsi_d']):
        score += 1
    if np.isfinite(last_d['vwap']) and last_d['Close'] > last_d['vwap']:
        score += 1
    if alignment >= 60:
        score += 1
    if data_quality >= 90:
        score += 1
    return score / total

def estimate_probabilities(base_conf, rr1, rr2, rr3, rr4, alignment, adx_val):
    trend_factor = alignment / 100
    momentum_factor = min(1.0, max(0.5, adx_val / 35))
    base = base_conf * 0.6 + trend_factor * 0.25 + momentum_factor * 0.15
    tp1 = base
    if rr1 >= 2:
        tp1 += 0.05
    elif rr1 < 1.2:
        tp1 -= 0.1
    tp1 = min(0.9, max(0.2, tp1))
    tp2 = tp1 * 0.82
    if rr2 >= 2:
        tp2 += 0.03
    elif rr2 < 1.5:
        tp2 -= 0.05
    tp2 = min(0.82, max(0.15, tp2))
    tp3 = tp2 * 0.78
    if rr3 >= 2.5:
        tp3 += 0.03
    elif rr3 < 2:
        tp3 -= 0.05
    tp3 = min(0.75, max(0.1, tp3))
    tp4 = tp3 * 0.72
    if rr4 >= 3:
        tp4 += 0.03
    elif rr4 < 2.5:
        tp4 -= 0.05
    tp4 = min(0.68, max(0.08, tp4))
    return (tp1, tp2, tp3, tp4)

def calculate_buy_percentage(last_d, last_w, last_m, alignment, relative_strength):
    """
    مؤشر عرضي من 0-100 لقياس ميل الإشارات الفنية ناحية الشراء.
    لا يغيّر أي منطق تداول قائم في V9.
    """
    buy = 0.0
    total = 0.0

    def add(condition, weight):
        nonlocal buy, total
        total += float(weight)
        if bool(condition):
            buy += float(weight)
    add(last_d['ema20'] > last_d['ema50'], 10)
    add(last_d['Close'] > last_d['ema50'], 5)
    add(last_w['ema20'] > last_w['ema50'], 5)
    add(last_m['ema20'] > last_m['ema50'], 5)
    rsi = float(last_d.get('rsi', np.nan))
    if np.isfinite(rsi):
        if 50 <= rsi <= 65:
            buy += 7
        elif 45 <= rsi < 50 or 65 < rsi <= 70:
            buy += 5
        elif rsi >= 70:
            buy += 3
        total += 7
    add(float(last_d.get('macd', np.nan)) > float(last_d.get('macd_signal', np.nan)), 8)
    add(float(last_d.get('stoch_rsi_k', np.nan)) > float(last_d.get('stoch_rsi_d', np.nan)), 5)
    add(float(last_d.get('volume_ratio', np.nan)) >= 1.0, 5)
    add(50 <= float(last_d.get('mfi', np.nan)) <= 75, 5)
    add(float(last_d.get('obv', np.nan)) > float(last_d.get('obv_ma', np.nan)), 5)
    add(float(last_d.get('Close', np.nan)) > float(last_d.get('vwap', np.nan)), 5)
    add(float(last_d.get('ema20_slope', np.nan)) > 0, 5)
    add(float(alignment) >= 60, 10)
    try:
        rs = float(relative_strength)
    except Exception:
        rs = 0.0
    add(rs >= 0, 10)
    if total <= 0:
        return 50.0
    return round(float(np.clip(buy / total * 100.0, 0.0, 100.0)), 1)

def style_buy_percentage(value):
    """تنسيق بصري للخلية فقط: أخضر/أصفر/أحمر."""
    try:
        x = float(value)
    except Exception:
        return ''
    if x >= 60:
        return 'background-color: rgba(0, 180, 0, 0.18); color: #0a7a0a; font-weight: 700;'
    if x < 40:
        return 'background-color: rgba(220, 0, 0, 0.15); color: #b00000; font-weight: 700;'
    return 'background-color: rgba(220, 170, 0, 0.16); color: #8a6a00; font-weight: 700;'

def display_with_buy_percentage(df):
    """عرض الجدول مع تلوين عمود نسبة الشراء فقط."""
    if 'نسبة الشراء %' not in df.columns:
        return df
    return df.style.map(style_buy_percentage, subset=['نسبة الشراء %'])

def analyze(df_d, df_w, df_m, capital, risk_percent):
    df_d = add_indicators(df_d)
    df_w = add_indicators(df_w)
    df_m = add_indicators(df_m)
    if len(df_d) < MIN_DAILY_ROWS:
        raise ValueError('بيانات يومية غير كافية')
    if len(df_w) < MIN_WEEKLY_ROWS:
        raise ValueError('بيانات أسبوعية غير كافية')
    if len(df_m) < MIN_MONTHLY_ROWS:
        raise ValueError('بيانات شهرية غير كافية')
    quality_d = calculate_data_quality(df_d)
    quality_w = calculate_data_quality(df_w)
    quality_m = calculate_data_quality(df_m)
    data_quality = quality_d['quality'] * 0.5 + quality_w['quality'] * 0.3 + quality_m['quality'] * 0.2
    required_daily = ['ema20', 'ema50', 'rsi', 'macd', 'macd_signal', 'macd_hist', 'vol_ma', 'volume_ratio', 'obv', 'obv_ma', 'obv_slope', 'mfi', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d', 'stoch_rsi_k_slope', 'vwap', 'support', 'resistance', 'previous_support', 'previous_resistance', 'atr', 'adx', 'ema20_slope', 'ema50_slope', 'body_pct']
    required_tf = ['ema20', 'ema50', 'macd', 'macd_signal', 'rsi', 'ema20_slope']
    df_d = df_d.dropna(subset=required_daily)
    df_w = df_w.dropna(subset=required_tf)
    df_m = df_m.dropna(subset=required_tf)
    if df_d.empty or df_w.empty or df_m.empty:
        raise ValueError('المؤشرات غير متاحة')
    last_d = df_d.iloc[-1]
    last_w = df_w.iloc[-1]
    last_m = df_m.iloc[-1]
    market_price = float(last_d['Close'])
    if market_price <= 0:
        raise ValueError('سعر غير صحيح')
    liquidity_ratio = float(last_d.get('liquidity_ratio', np.nan))
    if not np.isfinite(liquidity_ratio):
        liquidity_ratio = 0.0
    stock_return_20 = float(last_d.get('return_20d', np.nan))
    market_return_20 = float(last_d.get('market_return_20', np.nan))
    if not np.isfinite(stock_return_20):
        stock_return_20 = 0.0
    if not np.isfinite(market_return_20):
        market_return_20 = 0.0
    relative_strength = stock_return_20 - market_return_20
    liquidity_score = 5 if liquidity_ratio >= 2 else 4 if liquidity_ratio >= 1.5 else 3 if liquidity_ratio >= 1.0 else 1 if liquidity_ratio >= 0.7 else 0
    rs_score = 5 if relative_strength >= 0.1 else 4 if relative_strength >= 0.05 else 3 if relative_strength >= 0 else 1 if relative_strength >= -0.05 else 0
    daily_ema200_complete = len(df_d) >= EMA200_REQUIRED_ROWS
    weekly_ema200_complete = len(df_w) >= EMA200_REQUIRED_ROWS
    monthly_ema200_complete = len(df_m) >= EMA200_REQUIRED_ROWS
    ema200_status = '✅ مكتمل' if daily_ema200_complete and weekly_ema200_complete and monthly_ema200_complete else '⚠️ غير مكتمل'
    alignment = trend_alignment_score(df_d, df_w, df_m)
    buy_percentage = calculate_buy_percentage(last_d, last_w, last_m, alignment, relative_strength)
    regime = market_regime(last_d)
    entry_info = determine_entry(df_d, alignment)
    entry = float(entry_info['price'])
    entry_type = entry_info['type']
    entry_reason = entry_info['reason']
    risk = calculate_risk_engine(df_d, entry, capital, risk_percent, df_w, df_m)
    stop = risk['stop']
    tp1 = risk['tp1']
    tp2 = risk['tp2']
    tp3 = risk['tp3']
    tp4 = risk['tp4']
    score = 0.0
    trend_component = alignment * 0.25
    score += trend_component
    rsi = float(last_d['rsi'])
    momentum_score = 0
    if 50 <= rsi <= 65:
        momentum_score += 7
    elif 45 <= rsi < 50:
        momentum_score += 5
    elif 65 < rsi <= 70:
        momentum_score += 5
    elif 35 <= rsi < 45:
        momentum_score += 2
    if last_d['macd'] > last_d['macd_signal']:
        momentum_score += 5
    elif last_d['macd_hist'] > 0:
        momentum_score += 3
    stoch_k = float(last_d['stoch_rsi_k'])
    stoch_d = float(last_d['stoch_rsi_d'])
    if stoch_k > stoch_d:
        momentum_score += 3
    score += min(15, momentum_score)
    volume_ratio = float(last_d['volume_ratio'])
    money_score = 0
    if volume_ratio >= 2:
        money_score += 5
    elif volume_ratio >= 1.5:
        money_score += 4
    elif volume_ratio >= 1.1:
        money_score += 3
    elif volume_ratio >= 0.8:
        money_score += 1
    mfi = float(last_d['mfi'])
    if 50 <= mfi <= 75:
        money_score += 4
    elif 40 <= mfi < 50:
        money_score += 2
    elif 75 < mfi <= 85:
        money_score += 2
    obv = float(last_d['obv'])
    obv_ma = float(last_d['obv_ma'])
    obv_slope = float(last_d['obv_slope'])
    if obv > obv_ma and obv_slope > 0:
        money_score += 6
    elif obv > obv_ma or obv_slope > 0:
        money_score += 4
    elif obv_slope > 0:
        money_score += 2
    score += min(10, money_score)
    adx_val = float(last_d['adx'])
    strength_score = 0
    if adx_val >= 30:
        strength_score = 5
    elif adx_val >= 25:
        strength_score = 4
    elif adx_val >= 20:
        strength_score = 3
    elif adx_val >= 15:
        strength_score = 1.5
    score += min(5, strength_score)
    structure_score = 0
    if last_d['ema20_slope'] > 0 and last_d['ema50_slope'] > 0:
        structure_score += 4
    elif last_d['ema20_slope'] > 0:
        structure_score += 2
    if last_d['Close'] > last_d['vwap']:
        structure_score += 3
    if last_d['Close'] > last_d['ema50']:
        structure_score += 3
    score += min(10, structure_score)
    entry_score = 0
    if entry_type == 'دخول عند Pullback':
        entry_score = 10
    elif entry_type == 'دخول اختراق':
        entry_score = 9
    elif entry_type == 'دخول فوري':
        entry_score = 7
    else:
        entry_score = 2
    score += entry_score
    target_quality = float(risk['target_quality'])
    target_component = target_quality * 0.1
    score += target_component
    rr1 = float(risk['rr1'])
    risk_pct_actual = float(risk['risk_pct'])
    risk_score = 0
    if np.isfinite(rr1) and rr1 >= 2:
        risk_score += 3
    elif rr1 >= 1.5:
        risk_score += 2
    elif rr1 >= 1.2:
        risk_score += 1
    if risk_pct_actual <= 5:
        risk_score += 2
    elif risk_pct_actual <= 8:
        risk_score += 1
    score += min(5, risk_score)
    incomplete_count = sum([not daily_ema200_complete, not weekly_ema200_complete, not monthly_ema200_complete])
    if incomplete_count >= 2:
        score -= 4
    elif incomplete_count == 1:
        score -= 2
    if entry_type == 'انتظار تأكيد':
        score = min(score, 69)
    score = min(100, max(0, score))
    base_conf = ai_confidence(last_d, last_w, last_m, alignment, data_quality)
    tp1_prob, tp2_prob, tp3_prob, tp4_prob = estimate_probabilities(base_conf, 0 if not np.isfinite(risk['rr1']) else risk['rr1'], 0 if not np.isfinite(risk['rr2']) else risk['rr2'], 0 if not np.isfinite(risk['rr3']) else risk['rr3'], 0 if not np.isfinite(risk['rr4']) else risk['rr4'], alignment, adx_val)
    if score >= 85 and np.isfinite(rr1) and (rr1 >= 1.5) and (alignment >= 65) and (entry_type != 'انتظار تأكيد'):
        signal = '🔥 قوي جداً'
    elif score >= 70 and np.isfinite(rr1) and (rr1 >= 1.3) and (entry_type != 'انتظار تأكيد'):
        signal = '🟢 قوي'
    elif score >= 55:
        signal = '🟡 متوسط'
    else:
        signal = '⚠️ متابعة'
    volatility = float(last_d['atr']) / entry
    if volatility > 0.07:
        time_est = '1 - 3 أسابيع'
    elif volatility > 0.04:
        time_est = '3 - 8 أسابيع'
    elif volatility > 0.02:
        time_est = '1 - 3 شهور'
    else:
        time_est = '2 - 4 شهور'
    return {'التقييم': round(score, 2), 'نسبة الشراء %': buy_percentage, 'الإشارة': signal, 'الاتجاه': regime, 'نوع الدخول': entry_type, 'سبب الدخول': entry_reason, 'سعر الدخول': round(entry, 2), 'وقف الخسارة': round(stop, 2), 'الهدف الأول': round(tp1, 2), 'الهدف الثاني': round(tp2, 2), 'الهدف الثالث': round(tp3, 2), 'الهدف الرابع': round(tp4, 2), 'سبب الهدف الأول': risk['tp1_reason'], 'سبب الهدف الثاني': risk['tp2_reason'], 'سبب الهدف الثالث': risk['tp3_reason'], 'سبب الهدف الرابع': risk['tp4_reason'], 'نوع الهدف الأول': risk['tp1_category'], 'نوع الهدف الثاني': risk['tp2_category'], 'نوع الهدف الثالث': risk['tp3_category'], 'نوع الهدف الرابع': risk['tp4_category'], 'ربح الهدف الأول %': round(risk['tp1_profit_pct'], 2), 'ربح الهدف الثاني %': round(risk['tp2_profit_pct'], 2), 'ربح الهدف الثالث %': round(risk['tp3_profit_pct'], 2), 'ربح الهدف الرابع %': round(risk['tp4_profit_pct'], 2), 'R/R الهدف الأول': round(risk['rr1'], 2), 'R/R الهدف الثاني': round(risk['rr2'], 2), 'R/R الهدف الثالث': round(risk['rr3'], 2), 'R/R الهدف الرابع': round(risk['rr4'], 2), 'ثقة الهدف الأول %': round(tp1_prob * 100, 1), 'ثقة الهدف الثاني %': round(tp2_prob * 100, 1), 'ثقة الهدف الثالث %': round(tp3_prob * 100, 1), 'ثقة الهدف الرابع %': round(tp4_prob * 100, 1), 'جودة الأهداف': round(target_quality, 1), 'EMA200': ema200_status, 'التذبذب ATR %': round(volatility * 100, 2), 'قوة الاتجاه ADX': round(adx_val, 2), 'مؤشر RSI': round(rsi, 2), 'المدة المتوقعة': time_est, 'السيولة Ratio': round(liquidity_ratio, 2), 'قوة السيولة': round(liquidity_score + rs_score, 2), 'Relative Strength %': round(relative_strength * 100, 2), 'عدد الأهداف الهيكلية': int(risk.get('structural_target_count', 0)), '_entry_type': entry_type, '_trend_alignment': round(alignment, 2), '_data_quality': round(data_quality, 2), '_ema200_daily': 'مكتمل' if daily_ema200_complete else 'غير مكتمل', '_ema200_weekly': 'مكتمل' if weekly_ema200_complete else 'غير مكتمل', '_ema200_monthly': 'مكتمل' if monthly_ema200_complete else 'غير مكتمل', '_risk_pct': round(risk['risk_pct'], 2), '_rr1': round(risk['rr1'], 2), '_rr2': round(risk['rr2'], 2), '_rr3': round(risk['rr3'], 2), '_rr4': round(risk['rr4'], 2), '_target_quality': round(target_quality, 2), '_position_size': round(risk['position_size'], 2), '_position_value': round(risk['position_value'], 2), '_obv': round(obv, 2), '_obv_ma': round(obv_ma, 2), '_stoch_rsi_k': round(stoch_k, 4), '_stoch_rsi_d': round(stoch_d, 4), '_vwap': round(float(last_d['vwap']), 4), '_pullback_quality': round(float(last_d.get('pullback_quality_score', 0)), 2), '_volume_ratio': round(volume_ratio, 2), '_liquidity_ratio': round(liquidity_ratio, 2), '_relative_strength': round(relative_strength * 100, 2), '_structural_target_count': int(risk.get('structural_target_count', 0))}

def _clip_score(value, low, high):
    """تحويل قيمة رقمية إلى درجة 0-100 بشكل محافظ."""
    try:
        x = float(value)
    except Exception:
        return np.nan
    if not np.isfinite(x):
        return np.nan
    if high <= low:
        return 50.0
    return float(np.clip((x - low) / (high - low) * 100.0, 0.0, 100.0))

def _evidence_score(value, low, high):
    return _clip_score(value, low, high)

def build_market_return_proxy(data, symbols):
    returns = []
    for symbol in symbols:
        try:
            d = extract_symbol_data(data, symbol)
            if not d.empty and len(d) >= RS_LOOKBACK + 1:
                r = d['Close'].pct_change(RS_LOOKBACK).iloc[-1]
                if np.isfinite(r):
                    returns.append(float(r))
        except Exception:
            pass
    return float(np.median(returns)) if returns else 0.0


# ============================================================
# EGX INSTITUTIONAL FINANCIAL ENGINE V8 — FINANCIAL VALUATION ONLY
# V9 technical engine remains separate. Technical data NEVER enters fair value.
# ============================================================
import os, math, json, time, requests
from dataclasses import dataclass
from typing import Any, Dict, Optional

st.set_page_config(page_title="المحرك المالي المؤسسي EGX", page_icon="🏛️", layout="wide")

RAW = """COMI MFPC PHDC ORAS HDBK EFIH AMES INEG BTFH BIOC CLHO MBSC MTIE EGTS EGSA MHOT EGBE IFAP PRDC MIPH MPCI MOIN ISMQ AXPH PHTV CPCI NINH SPIN ENGC CNFN SVCE KABO OFH GSSC WCDF MFSC SAIB ACGC UEFM KZPC ADCI INFI ASCM VALU ZEOT SMFR ETRS CIRA QNBE EDFM MILS GBCO ACTF SCTS HRHO TMGH FWRY SWDY ETEL AMOC HELI EAST EFID JUFO ABUK ESRS EMFD CCAP ACAP CICH OCDI ORHD MASR AIHC ADIB SAUD CIEB FAIT AFDI CANA EXPA ARCC AJWA MICH SUGR POUL DOMT ISMA UEGC FERC UBEE FAITA MNHD SUCE SMPP ALEX CRST DCRC DIFC MAAL GGRN GGCC IEEC NDRL EFIC GPIM RTVC RUBX PRMH UNIP TWSA ICLE MEGM EASB APSW MOED KWIN KORA RMDA OIH NAPR BONY SPHT SDTI GTWL CFGH NAHO ACAMD NARE CEFM ASPI SCFM CERA DEIN MBEG SIPC NHPS ROTO TYCN RAKT EEII CCRS AREH EPCO FCMD GRCA GIHD ELWA MMAT NEDA EPPK GMCI CPME VLMR GPPL ADPC ADRI AIDC OBRI RREI RKAZ SEIG SNFC TANM UPMS UTOP VERT WKOL LUTS AIFI AMIA AMII ACRO DGTZ DTPP EALR EBSC EGREF EHDR ELNA EOSB FIRE FNAR FTNS GOUR ICID IDRE KASABF KRDI LCSW MOSC TAQA OLFI SKPC AMER TALM ALUM ORWE SPMD ZMID MENA DAPH RAYA EGAL ECAP MPRC AFMC NCCW SCEM ARAB GDWA ELEC IRON ATQA EGCH ALCN MPCO ELSH MEPA ODIN EGAS RACC PRCL BINV EDBM MCQE MOIL NIPH ISPH DSCW AALR UNIT PHAR TRTO CAED CSAG ICFC ELKA PHGC NCGC MCRO ATLC COSG AMPI COPR OCPH""".split()
STOCKS=list(dict.fromkeys(x+".CA" for x in RAW))

BANKS=set("COMI HDBK EGBE SAIB QNBE CICH SAUD CIEB ADIB".split())
RE=set("PHDC PRDC TMGH HELI EMFD CCAP OCDI ORHD MASR MNHD DCRC ARCC RMDA IDRE RREI EGREF EHDR MENA MPRC".split())
HEALTH=set("BIOC CLHO MIPH NIPH ISPH PHAR SPMD DAPH PHTV OCPH".split())
TECH=set("ETEL MTIE RAYA EFIH UBEE DGTZ GOUR".split())
ENERGY=set("AMOC SKPC EGAS TAQA MOIL GPIM EGAL ELSH MEPA".split())
CONSUMER=set("DOMT EAST JUFO SUGR POUL OLFI AJWA MICH UEGC ISMA FERC".split())
CONSTRUCTION=set("ORAS ENGC SVCE ARAB ELNA UPMS UNIT NCCW RACC PRCL AIDC".split())
FIN=set("EFIH BTFH VALU OFH CNFN MCQE ADCI ACAP FAIT AFDI UBEE FAITA AIFI AMIA AMII ATLC BINV DIFC".split())

SECTOR_RULES={
    'بنوك':['ROE','ROA','NIM','Cost/Income','NPL','NPL Coverage','CAR','Loan Growth','Deposit Growth','Net Income Growth','P/B','P/E','Dividend Yield'],
    'عقارات':['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROE','Debt/Equity','Net Debt/EBITDA','Operating Cash Flow','FCF Margin','P/B','P/E'],
    'رعاية صحية':['Revenue Growth','EPS Growth','Net Margin','EBITDA Margin','ROE','ROA','FCF Margin','Debt/Equity','Current Ratio','P/E','P/B'],
    'اتصالات وتكنولوجيا':['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROIC','FCF Margin','Net Debt/EBITDA','ROE','P/E','EV/EBITDA','Dividend Yield'],
    'طاقة وبتروكيماويات':['Revenue Growth','EPS Growth','EBITDA Margin','Net Margin','ROIC','FCF Margin','Debt/Equity','Net Debt/EBITDA','ROE','P/E','EV/EBITDA','Dividend Yield'],
    'استهلاكي':['Revenue Growth','EPS Growth','Gross Margin','EBITDA Margin','Net Margin','ROE','ROIC','FCF Margin','Debt/Equity','P/E','Dividend Yield'],
    'إنشاءات وهندسة':['Revenue Growth','EBITDA Margin','Net Margin','ROE','ROIC','Operating Cash Flow','FCF Margin','Debt/Equity','Net Debt/EBITDA','P/E','P/B'],
    'صناعة ومواد':['Revenue Growth','EPS Growth','Gross Margin','EBITDA Margin','Net Margin','ROE','ROIC','FCF Margin','Debt/Equity','Net Debt/EBITDA','P/E','P/B','Dividend Yield'],
    'خدمات مالية':['Revenue Growth','Net Income Growth','ROE','ROA','Net Margin','Debt/Equity','Current Ratio','P/E','P/B','Dividend Yield'],
    'عام':['Revenue Growth','EPS Growth','Net Margin','ROE','ROA','ROIC','FCF Margin','Debt/Equity','Current Ratio','P/E','P/B','Dividend Yield']
}

@dataclass
class SourceResult:
    source:str
    ok:bool
    data:Any=None
    error:str=''


def num(x):
    try:
        x=float(x)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan


def clean_series(s):
    if s is None: return pd.Series(dtype=float)
    try:
        return pd.to_numeric(s,errors='coerce').dropna()
    except Exception:
        return pd.Series(dtype=float)


def ordered_series(s):
    s=clean_series(s)
    if len(s)<=1:return s
    try:
        if isinstance(s.index,pd.DatetimeIndex): return s.sort_index(ascending=False)
    except Exception: pass
    return s


def last(s):
    s=ordered_series(s); return num(s.iloc[0]) if len(s) else np.nan


def prev(s):
    s=ordered_series(s); return num(s.iloc[1]) if len(s)>1 else np.nan


def growth_series(s):
    s=ordered_series(s)
    return (s.iloc[0]/s.iloc[1]-1)*100 if len(s)>=2 and s.iloc[1]!=0 else np.nan


def find(df,names):
    if df is None or getattr(df,'empty',True): return None
    for n in names:
        if n in df.index: return pd.to_numeric(df.loc[n],errors='coerce')
    # conservative matching: only normalized token matches, avoiding accidental substring hits
    norm={str(n).strip().lower().replace('_',' '):n for n in names}
    for idx in df.index:
        k=str(idx).strip().lower().replace('_',' ')
        if k in norm:return pd.to_numeric(df.loc[idx],errors='coerce')
    return None


def sector(sym,info):
    s=sym.replace('.CA','')
    for g,n in [(BANKS,'بنوك'),(RE,'عقارات'),(HEALTH,'رعاية صحية'),(TECH,'اتصالات وتكنولوجيا'),(ENERGY,'طاقة وبتروكيماويات'),(CONSUMER,'استهلاكي'),(CONSTRUCTION,'إنشاءات وهندسة'),(FIN,'خدمات مالية')]:
        if s in g:return n
    txt=(str(info.get('sector',''))+' '+str(info.get('industry',''))).lower()
    if 'bank' in txt:return 'بنوك'
    if 'real estate' in txt:return 'عقارات'
    if any(x in txt for x in ['health','medical','pharma']):return 'رعاية صحية'
    if any(x in txt for x in ['telecom','software','technology','internet']):return 'اتصالات وتكنولوجيا'
    if any(x in txt for x in ['oil','gas','energy','petro']):return 'طاقة وبتروكيماويات'
    if any(x in txt for x in ['consumer','food','beverage','retail']):return 'استهلاكي'
    if any(x in txt for x in ['construction','engineering']):return 'إنشاءات وهندسة'
    if any(x in txt for x in ['financial','insurance','investment']):return 'خدمات مالية'
    return 'صناعة ومواد'


@st.cache_data(ttl=21600, show_spinner=False)
def safe_yahoo_bundle(ticker):
    out={'info':{},'financials':pd.DataFrame(),'balance':pd.DataFrame(),'cashflow':pd.DataFrame(),'quarterly_income':pd.DataFrame(),'quarterly_balance':pd.DataFrame(),'quarterly_cashflow':pd.DataFrame(),'dividends':pd.Series(dtype=float),'errors':[]}
    try:
        t=yf.Ticker(ticker)
    except Exception as e:
        out['errors'].append(f'إنشاء Ticker: {e}'); return out
    # history is intentionally separate and should work even when Yahoo info returns 401.
    for key,attr in [('financials','financials'),('balance','balance_sheet'),('cashflow','cashflow'),('quarterly_income','quarterly_financials'),('quarterly_balance','quarterly_balance_sheet'),('quarterly_cashflow','quarterly_cashflow')]:
        try:
            out[key]=getattr(t,attr)
        except Exception as e:
            out['errors'].append(f'{key}: {str(e)[:140]}')
    try: out['dividends']=t.dividends
    except Exception as e: out['errors'].append(f'dividends: {str(e)[:140]}')
    try: out['info']=t.info or {}
    except Exception as e: out['errors'].append(f'info: {str(e)[:140]}')
    return out


@st.cache_data(ttl=1800, show_spinner=False)
def latest_price(ticker):
    for period,auto in [('10d',False),('10d',True)]:
        try:
            h=yf.Ticker(ticker).history(period=period,interval='1d',auto_adjust=auto,actions=False)
            if h is not None and not h.empty and 'Close' in h:
                h=h.dropna(subset=['Close'])
                if not h.empty:
                    return num(h['Close'].iloc[-1]),pd.Timestamp(h.index[-1]).strftime('%Y-%m-%d'),'Yahoo - آخر إغلاق'
        except Exception:
            pass
    # Stooq fallback for price only; failure never crashes the app.
    try:
        s=ticker.replace('.CA','').lower()+'.eg'
        u=f'https://stooq.com/q/d/l/?s={s}&i=d'
        r=requests.get(u,timeout=8,headers={'User-Agent':'Mozilla/5.0'})
        if r.ok and len(r.text)>30:
            d=pd.read_csv(pd.io.common.StringIO(r.text)); d['Date']=pd.to_datetime(d['Date'],errors='coerce'); d=d.dropna(subset=['Date','Close'])
            if not d.empty:return num(d['Close'].iloc[-1]),d['Date'].iloc[-1].strftime('%Y-%m-%d'),'Stooq - احتياطي'
    except Exception: pass
    return np.nan,'—','غير متاح'


def _ttm_or_annual(q,a,names):
    qv=find(q,names); av=find(a,names)
    qv=ordered_series(qv); av=ordered_series(av)
    if len(qv)>=4:return float(qv.iloc[:4].sum())
    return last(av)


def normalize_financials(raw,price):
    info=raw.get('info') or {}; inc=raw.get('financials'); bal=raw.get('balance'); cf=raw.get('cashflow'); qi=raw.get('quarterly_income'); qb=raw.get('quarterly_balance'); qc=raw.get('quarterly_cashflow')
    rev=find(inc,['Total Revenue','Operating Revenue','Revenue']); ni=find(inc,['Net Income','Net Income Common Stockholders']); eq=find(bal,['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity']); assets=find(bal,['Total Assets']); debt=find(bal,['Total Debt','Long Term Debt','Current Debt']); cash=find(bal,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']); ocf=find(cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex=find(cf,['Capital Expenditure','Capital Expenditures']); ebit=find(inc,['EBIT','Operating Income']); ebitda=find(inc,['EBITDA','Normalized EBITDA']); gross=find(inc,['Gross Profit']); eps=find(inc,['Diluted EPS','Basic EPS']); dep=find(cf,['Depreciation And Amortization','Depreciation']); ca=find(bal,['Current Assets','Current Assets Total']); cl=find(bal,['Current Liabilities','Current Liabilities Total']); retained=find(bal,['Retained Earnings']); shares_s=find(inc,['Diluted Average Shares','Basic Average Shares']); shares_b=find(bal,['Ordinary Shares Number','Share Issued'])
    rev_ttm=_ttm_or_annual(qi,inc,['Total Revenue','Operating Revenue','Revenue']); ni_ttm=_ttm_or_annual(qi,inc,['Net Income','Net Income Common Stockholders']); eps_ttm=_ttm_or_annual(qi,inc,['Diluted EPS','Basic EPS']); ocf_ttm=_ttm_or_annual(qc,cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex_ttm=_ttm_or_annual(qc,cf,['Capital Expenditure','Capital Expenditures'])
    if pd.notna(rev_ttm): rev=pd.Series([rev_ttm])
    if pd.notna(ni_ttm): ni=pd.Series([ni_ttm])
    if pd.notna(eps_ttm): eps=pd.Series([eps_ttm])
    if pd.notna(ocf_ttm): ocf=pd.Series([ocf_ttm])
    if pd.notna(capex_ttm): capex=pd.Series([capex_ttm])
    mcap=num(info.get('marketCap')); shares=num(info.get('sharesOutstanding')); shares=shares if pd.notna(shares) else last(shares_s if shares_s is not None else shares_b)
    if pd.isna(shares) and pd.notna(mcap) and pd.notna(price) and price>0: shares=mcap/price
    R,NI,EQ,AS,D,C,OCF,EBIT,EBITDA,GROSS,EPS,DEP,CA,CL,RETAIN=[last(x) for x in [rev,ni,eq,assets,debt,cash,ocf,ebit,ebitda,gross,eps,dep,ca,cl,retained]]
    FCF=(OCF+capex) if pd.notna(OCF) and pd.notna(capex) and capex<0 else (OCF-capex if pd.notna(OCF) and pd.notna(capex) else np.nan)
    prev_rev=prev(rev); prev_ni=prev(ni); prev_eps=prev(eps); prev_eq=prev(eq)
    tax=find(inc,['Tax Provision','Tax Expense']); pretax=find(inc,['Pretax Income','Pretax Income Common Stockholders']); taxrate=(last(tax)/last(pretax)) if tax is not None and pd.notna(last(pretax)) and last(pretax)!=0 else num(info.get('effectiveTaxRate'))
    if pd.notna(taxrate) and 0<=taxrate<=1: taxrate*=100
    if pd.isna(taxrate): taxrate=22.5
    taxrate=float(np.clip(taxrate,0,45))
    bvps=EQ/shares if pd.notna(EQ) and pd.notna(shares) and shares>0 else np.nan
    market_cap=(shares*price if pd.notna(shares) and pd.notna(price) else mcap)
    enterprise=(market_cap+D-C) if pd.notna(market_cap) else np.nan
    m={'Price':price,'Shares':shares,'Market Cap':market_cap,'Revenue':R,'Previous Revenue':prev_rev,'Net Income':NI,'Previous Net Income':prev_ni,'EPS':EPS,'Previous EPS':prev_eps,'Equity':EQ,'Previous Equity':prev_eq,'Assets':AS,'Debt':D,'Cash':C,'Operating Cash Flow':OCF,'CAPEX':capex_ttm if pd.notna(capex_ttm) else last(capex),'FCF':FCF,'EBIT':EBIT,'EBITDA':EBITDA,'Gross Profit':GROSS,'D&A':DEP,'Current Assets':CA,'Current Liabilities':CL,'Retained Earnings':RETAIN,'Tax Rate %':taxrate,'Enterprise Value':enterprise,'BVPS':bvps}
    m['Revenue Growth']=((R/prev_rev)-1)*100 if pd.notna(R) and pd.notna(prev_rev) and prev_rev!=0 else np.nan
    m['Net Income Growth']=((NI/prev_ni)-1)*100 if pd.notna(NI) and pd.notna(prev_ni) and prev_ni!=0 else np.nan
    m['EPS Growth']=((EPS/prev_eps)-1)*100 if pd.notna(EPS) and pd.notna(prev_eps) and prev_eps!=0 else np.nan
    m['Gross Margin']=GROSS/R*100 if pd.notna(GROSS) and pd.notna(R) and R!=0 else np.nan
    m['EBITDA Margin']=EBITDA/R*100 if pd.notna(EBITDA) and pd.notna(R) and R!=0 else np.nan
    m['Net Margin']=NI/R*100 if pd.notna(NI) and pd.notna(R) and R!=0 else np.nan
    m['ROE']=NI/((EQ+prev_eq)/2)*100 if pd.notna(NI) and pd.notna(EQ) and pd.notna(prev_eq) and (EQ+prev_eq)!=0 else (NI/EQ*100 if pd.notna(NI) and pd.notna(EQ) and EQ!=0 else np.nan)
    m['ROA']=NI/AS*100 if pd.notna(NI) and pd.notna(AS) and AS!=0 else np.nan
    invested=(EQ+D-C) if pd.notna(EQ) and pd.notna(D) and pd.notna(C) else np.nan
    m['ROIC']=EBIT*(1-taxrate/100)/invested*100 if pd.notna(EBIT) and pd.notna(invested) and invested>0 else np.nan
    m['FCF Margin']=FCF/R*100 if pd.notna(FCF) and pd.notna(R) and R!=0 else np.nan
    m['Debt/Equity']=D/EQ if pd.notna(D) and pd.notna(EQ) and EQ!=0 else np.nan
    m['Net Debt/EBITDA']=(D-C)/EBITDA if pd.notna(D) and pd.notna(C) and pd.notna(EBITDA) and EBITDA>0 else np.nan
    m['Current Ratio']=CA/CL if pd.notna(CA) and pd.notna(CL) and CL!=0 else np.nan
    m['P/E']=price/EPS if pd.notna(price) and pd.notna(EPS) and EPS>0 else np.nan
    m['P/B']=price/bvps if pd.notna(price) and pd.notna(bvps) and bvps>0 else np.nan
    m['EV/EBITDA']=enterprise/EBITDA if pd.notna(enterprise) and pd.notna(EBITDA) and EBITDA>0 else np.nan
    m['_annual_revenue_series']=ordered_series(find(inc,['Total Revenue','Operating Revenue','Revenue']))
    m['_annual_ni_series']=ordered_series(find(inc,['Net Income','Net Income Common Stockholders']))
    m['_annual_eps_series']=ordered_series(find(inc,['Diluted EPS','Basic EPS']))
    m['_annual_assets_series']=ordered_series(find(bal,['Total Assets']))
    m['_annual_equity_series']=ordered_series(find(bal,['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity']))
    m['_annual_ocf_series']=ordered_series(find(cf,['Operating Cash Flow','Total Cash From Operating Activities']))
    return m


def model_applicable(sec,model):
    if sec in ['بنوك','خدمات مالية'] and model=='DCF/FCFF': return False
    if sec=='عقارات' and model=='EV/EBITDA': return False
    return True


def sector_multiples(sec):
    return {'بنوك':(8.5,0.95,0.0),'خدمات مالية':(10.0,1.05,0.0),'عقارات':(10.0,0.85,10.0),'رعاية صحية':(15.0,1.8,9.0),'اتصالات وتكنولوجيا':(16.0,2.0,8.0),'طاقة وبتروكيماويات':(9.0,1.5,6.0),'استهلاكي':(14.0,1.8,8.0),'إنشاءات وهندسة':(11.0,1.5,7.0),'صناعة ومواد':(11.0,1.5,7.0)}.get(sec,(12.0,1.5,7.0))


def peer_multiples(target,peers,sec):
    vals={}
    for key in ['P/E','P/B','EV/EBITDA']:
        a=[]
        for x in peers:
            v=num(x.get(key))
            if pd.notna(v) and v>0 and v<80:a.append(v)
        vals[key]=float(np.median(a)) if a else np.nan
    return vals


def relative_value(m,sec,peers):
    pm=peer_multiples(m,peers,sec); ref_pe,ref_pb,ref_ev=sector_multiples(sec)
    pe_mult=pm['P/E'] if pd.notna(pm['P/E']) else ref_pe; pb_mult=pm['P/B'] if pd.notna(pm['P/B']) else ref_pb; ev_mult=pm['EV/EBITDA'] if pd.notna(pm['EV/EBITDA']) else ref_ev
    values={}
    if pd.notna(m.get('EPS')) and m['EPS']>0 and pd.notna(pe_mult):values['P/E']=m['EPS']*pe_mult
    if pd.notna(m.get('BVPS')) and m['BVPS']>0 and pd.notna(pb_mult):values['P/B']=m['BVPS']*pb_mult
    if sec not in ['بنوك','خدمات مالية'] and pd.notna(m.get('EBITDA')) and m['EBITDA']>0 and pd.notna(m.get('Shares')) and m['Shares']>0 and pd.notna(ev_mult):
        ev=m['EBITDA']*ev_mult; eq=ev-(m['Debt'] if pd.notna(m['Debt']) else 0)+(m['Cash'] if pd.notna(m['Cash']) else 0); values['EV/EBITDA']=eq/m['Shares']
    return {'value':float(np.median(list(values.values()))) if values else np.nan,'methods':len(values),'values':values,'peer_P/E':pm['P/E'],'peer_P/B':pm['P/B'],'peer_EV/EBITDA':pm['EV/EBITDA'],'reference_P/E':ref_pe,'reference_P/B':ref_pb,'reference_EV/EBITDA':ref_ev}


def dcf_fcff(m,scenario,rf=0.16,mrp=0.08):
    if not all(pd.notna(m.get(k)) for k in ['EBIT','FCF','Shares']) or m['Shares']<=0:return {'value':np.nan,'status':'غير متاح — بيانات FCFF غير كافية'}
    base=max(m['FCF'],0)
    if base<=0:return {'value':np.nan,'status':'غير متاح — FCFF الحالي غير موجب'}
    hist=max(-10,min(25,num(m.get('Revenue Growth')) if pd.notna(m.get('Revenue Growth')) else 8))
    if scenario=='محافظ': g0=float(np.clip(hist*0.45,2,10)); wacc=rf+mrp+0.025; tg=0.025; margin_factor=0.92
    elif scenario=='متفائل': g0=float(np.clip(hist*0.85,6,22)); wacc=rf+mrp-0.005; tg=0.04; margin_factor=1.06
    else: g0=float(np.clip(hist*0.65,4,16)); wacc=rf+mrp+0.01; tg=0.0325; margin_factor=1.0
    if wacc<=tg+0.01:wacc=tg+0.03
    pv=0; fcff=base*margin_factor
    for y in range(1,6):
        g=g0+(tg-g0)*(y-1)/4
        fcff*=1+g/100
        pv+=fcff/(1+wacc)**y
    tv=fcff*(1+tg)/(wacc-tg); ev=pv+tv/(1+wacc)**5
    debt=m['Debt'] if pd.notna(m.get('Debt')) else 0; cash=m['Cash'] if pd.notna(m.get('Cash')) else 0
    eqv=ev-debt+cash
    return {'value':eqv/m['Shares'],'status':'متاح','wacc':wacc,'terminal_growth':tg,'first_growth':g0,'base_fcff':base}


def bank_value(m,scenario):
    if pd.isna(m.get('BVPS')) or m['BVPS']<=0:return {'value':np.nan,'status':'غير متاح — BVPS غير متاح'}
    roe=m.get('ROE'); eps=m.get('EPS'); pe=m.get('P/E');
    # Cost of equity / sustainable ROE framework; never uses technical inputs.
    if scenario=='محافظ': target_pb=0.75; pe_mult=7.0
    elif scenario=='متفائل': target_pb=1.35; pe_mult=10.5
    else: target_pb=1.05; pe_mult=8.5
    if pd.notna(roe):
        target_pb=float(np.clip(target_pb*(1+np.clip((roe-12)/40,-0.25,0.25)),0.55,1.70))
    vals=[]
    if pd.notna(m['BVPS']):vals.append(m['BVPS']*target_pb)
    if pd.notna(eps) and eps>0:vals.append(eps*pe_mult)
    return {'value':float(np.median(vals)) if vals else np.nan,'status':'متاح','target_pb':target_pb,'target_pe':pe_mult}


def nav_value(m,scenario):
    if pd.isna(m.get('BVPS')) or m['BVPS']<=0:return {'value':np.nan,'status':'غير متاح — صافي الأصول/الأسهم غير متاح'}
    mult={'محافظ':0.80,'أساسي':1.05,'متفائل':1.30}[scenario]
    # This is accounting NAV, not invented property revaluation.
    return {'value':m['BVPS']*mult,'status':'متاح — NAV محاسبي/صافي أصول','nav_per_share':m['BVPS'],'asset_multiple':mult}


def valuation_engine(m,sec,peers,rf,mrp):
    scenarios=['محافظ','أساسي','متفائل']; out={}
    for sc in scenarios:
        vals=[]; models={}
        if sec in ['بنوك','خدمات مالية']:
            b=bank_value(m,sc); models['نموذج البنوك']=b
            if pd.notna(b['value']):vals.append(b['value'])
        elif sec=='عقارات':
            n=nav_value(m,sc); models['NAV']=n
            if pd.notna(n['value']):vals.append(n['value'])
            d=dcf_fcff(m,sc,rf,mrp); models['DCF/FCFF']=d
            # DCF is secondary for real estate, never forced.
            if pd.notna(d['value']):vals.append(d['value'])
        else:
            d=dcf_fcff(m,sc,rf,mrp); models['DCF/FCFF']=d
            if pd.notna(d['value']):vals.append(d['value'])
        rv=relative_value(m,sec,peers); models['التقييم النسبي']=rv
        if pd.notna(rv['value']):vals.append(rv['value'])
        out[sc]={'value':float(np.median(vals)) if vals else np.nan,'models':models,'model_count':len(vals)}
    low=out['محافظ']['value']; base=out['أساسي']['value']; high=out['متفائل']['value']
    # Never fabricate a range. If scenarios collapse, the UI explicitly reports it.
    fair=base
    buy20=fair*.80 if pd.notna(fair) else np.nan; buy30=fair*.70 if pd.notna(fair) else np.nan
    return {'conservative':low,'base':base,'optimistic':high,'fair':fair,'safe_buy_20':buy20,'safe_buy_30':buy30,'scenarios':out}


def targets_3y(m,sec,valuation):
    eps=num(m.get('EPS')); bvps=num(m.get('BVPS')); revg=num(m.get('Revenue Growth')); price=num(m.get('Price'))
    if sec in ['بنوك','خدمات مالية']:
        g=np.clip(revg if pd.notna(revg) else 8,-5,18); base_pe=8.5; cons_pe=7; opt_pe=10.5
        vals=[]
        for sc,pe in [('محافظ',cons_pe),('أساسي',base_pe),('متفائل',opt_pe)]:
            if pd.notna(eps) and eps>0:
                gr={'محافظ':max(2,g*.45),'أساسي':max(4,g*.7),'متفائل':max(6,g*.9)}[sc]/100
                eps3=eps*((1+gr)**3); vals.append((sc,eps3*pe))
        return target_path(vals,price)
    if pd.notna(eps) and eps>0:
        g=np.clip(revg if pd.notna(revg) else 8,-5,22); result={}
        for sc,mult in [('محافظ',0.55),('أساسي',0.75),('متفائل',1.0)]:
            gr=max(-0.03,min(0.20,g*mult/100)); pe={'محافظ':8,'أساسي':11,'متفائل':15}[sc]
            result[sc]=[eps*(1+gr)**y*pe for y in [1,2,3]]
        return result
    if pd.notna(bvps) and bvps>0:
        return {sc:[v*{'محافظ':.8,'أساسي':1.05,'متفائل':1.3}[sc] for v in [bvps,bvps,bvps]] for sc in ['محافظ','أساسي','متفائل']}
    return {sc:[np.nan,np.nan,np.nan] for sc in ['محافظ','أساسي','متفائل']}


def target_path(vals,price):
    d={sc:[np.nan,np.nan,np.nan] for sc in ['محافظ','أساسي','متفائل']}
    for sc,v in vals:
        if pd.notna(v):d[sc]=[v/((1.0+0.03)**2),v/((1.0+0.03)),v]
    return d


def dividend_engine(divs,price,m):
    out={'yield':np.nan,'last':np.nan,'payout':np.nan,'fcf_payout':np.nan,'continuity_years':0,'sustainability':np.nan,'status':'غير متاح'}
    try:
        s=pd.to_numeric(divs,errors='coerce').dropna(); s=s[s>0]
        if s.empty:return out
        idx=pd.to_datetime(s.index)
        s.index=idx
        now=pd.Timestamp.now(tz=idx.tz) if getattr(idx,'tz',None) else pd.Timestamp.now()
        ttm=float(s[idx>=now-pd.Timedelta(days=365)].sum())
        out['yield']=ttm/price*100 if pd.notna(price) and price>0 else np.nan; out['last']=float(s.iloc[-1])
        annual=[float(s[(idx>=now-pd.Timedelta(days=365*(y+1)))&(idx<now-pd.Timedelta(days=365*y))].sum()) for y in range(3)]
        if pd.notna(m.get('EPS')) and m['EPS']>0:out['payout']=annual[0]/m['EPS']*100
        if pd.notna(m.get('FCF')) and m['FCF']>0 and pd.notna(m.get('Shares')) and m['Shares']>0:out['fcf_payout']=annual[0]/(m['FCF']/m['Shares'])*100
        years=set(idx.year.tolist()); out['continuity_years']=sum(1 for y in range(now.year-1,now.year-4,-1) if y in years)
        parts=[]
        if pd.notna(out['payout']):parts.append(float(np.clip(100-abs(out['payout']-55)*1.2,0,100)))
        if pd.notna(out['fcf_payout']):parts.append(float(np.clip(100-abs(out['fcf_payout']-55)*1.0,0,100)))
        parts.append(min(100,out['continuity_years']/3*100))
        out['sustainability']=float(np.mean(parts)); out['status']='متاح'
    except Exception as e:out['status']=f'غير متاح: {str(e)[:100]}'
    return out


def piotroski_score(m):
    # A conservative 9-point implementation using available annual data.
    a=m.get('_annual_assets_series',pd.Series(dtype=float)); e=m.get('_annual_equity_series',pd.Series(dtype=float)); r=m.get('_annual_revenue_series',pd.Series(dtype=float)); n=m.get('_annual_ni_series',pd.Series(dtype=float)); eps=m.get('_annual_eps_series',pd.Series(dtype=float)); ocf=m.get('_annual_ocf_series',pd.Series(dtype=float))
    if min(len(a),len(e),len(r),len(n),len(ocf))<2:return {'score':np.nan,'coverage':0,'status':'غير متاح — بيانات سنوية غير كافية'}
    checks=[]
    roa0=n.iloc[0]/a.iloc[0] if a.iloc[0]!=0 else np.nan; roa1=n.iloc[1]/a.iloc[1] if a.iloc[1]!=0 else np.nan
    checks += [n.iloc[0]>0, ocf.iloc[0]>0, roa0>0, ocf.iloc[0]>n.iloc[0], roa0>roa1]
    if len(e)>=2: checks.append((e.iloc[0]/a.iloc[0]) <= (e.iloc[1]/a.iloc[1]) if a.iloc[0]!=0 and a.iloc[1]!=0 else np.nan)
    checks.append(r.iloc[0]>r.iloc[1])
    checks.append(n.iloc[0]>n.iloc[1])
    checks.append(eps.iloc[0]>eps.iloc[1] if len(eps)>=2 else np.nan)
    valid=[x for x in checks if isinstance(x,(bool,np.bool_))]
    return {'score':int(sum(valid)) if valid else np.nan,'coverage':len(valid)/9*100,'status':'متاح — نسخة محافظة 9 نقاط'}


def beneish_screen(m):
    flags=[]
    if pd.notna(m.get('Revenue Growth')) and m['Revenue Growth']>80:flags.append('نمو إيرادات غير اعتيادي')
    if pd.notna(m.get('Net Margin')) and m['Net Margin']<0:flags.append('هامش صافي سلبي')
    if pd.notna(m.get('Debt/Equity')) and m['Debt/Equity']>2:flags.append('مديونية مرتفعة')
    if pd.notna(m.get('FCF Margin')) and m['FCF Margin']<0:flags.append('تدفق حر سلبي')
    return {'flags':len(flags),'status':'فحص تحذيري — ليس Beneish M-Score كاملًا','details':flags}


def altman_z(m,sec):
    if sec in ['بنوك','خدمات مالية']:return {'score':np.nan,'status':'غير مناسب للبنوك/الخدمات المالية'}
    if not all(pd.notna(m.get(k)) for k in ['Market Cap','Debt','Assets','Revenue']):return {'score':np.nan,'status':'غير متاح — بيانات غير كافية'}
    wc=(m.get('Current Assets')-m.get('Current Liabilities')) if pd.notna(m.get('Current Assets')) and pd.notna(m.get('Current Liabilities')) else np.nan
    if pd.isna(wc) or m['Assets']==0:return {'score':np.nan,'status':'غير متاح'}
    x1=wc/m['Assets']; x2=(m.get('Retained Earnings')/m['Assets']) if pd.notna(m.get('Retained Earnings')) else np.nan; x3=(m.get('EBIT')/m['Assets']) if pd.notna(m.get('EBIT')) else np.nan; x4=m['Market Cap']/m['Debt'] if m['Debt']>0 else np.nan; x5=m['Revenue']/m['Assets']
    vals=[x1,x2,x3,x4,x5]
    if any(pd.isna(vals)):return {'score':np.nan,'status':'غير متاح — مدخلات Altman ناقصة'}
    z=1.2*x1+1.4*x2+3.3*x3+0.6*x4+1.0*x5
    return {'score':float(z),'status':'متاح — مؤشر إنذار ائتماني'}


def earnings_quality(m):
    parts=[]
    if pd.notna(m.get('Net Income')) and m['Net Income']!=0 and pd.notna(m.get('Operating Cash Flow')):
        parts.append(np.clip(50+(m['Operating Cash Flow']/abs(m['Net Income'])-1)*50,0,100))
    if pd.notna(m.get('FCF')) and pd.notna(m.get('Net Income')) and m['Net Income']>0:
        parts.append(100 if m['FCF']>=m['Net Income'] else np.clip(m['FCF']/m['Net Income']*100,0,100))
    if pd.notna(m.get('ROE')):parts.append(np.clip(50+m['ROE']*2,0,100))
    return {'score':float(np.mean(parts)) if parts else np.nan,'status':'متاح' if parts else 'غير متاح'}


def financial_score(m,sec):
    rules=SECTOR_RULES.get(sec,SECTOR_RULES['صناعة ومواد']); vals=[]
    for k in rules:
        x=num(m.get(k))
        if pd.isna(x):continue
        if k in ['Revenue Growth','Net Income Growth','EPS Growth']:z=np.clip(50+x*1.5,0,100)
        elif k in ['ROE','ROIC']:z=np.clip(x*3,0,100)
        elif k=='ROA':z=np.clip(x*15,0,100)
        elif k in ['Gross Margin','EBITDA Margin','Net Margin','FCF Margin']:z=np.clip(x*2,0,100)
        elif k=='Debt/Equity':z=np.clip(100-max(x,0)*40,0,100)
        elif k=='Net Debt/EBITDA':z=np.clip(100-max(x,0)*18,0,100)
        elif k=='Current Ratio':z=np.clip(x*50,0,100)
        elif k=='Dividend Yield':z=np.clip(x*12,0,100)
        elif k=='P/E':z=np.clip(100-abs(x-12)*4,0,100) if x>0 else np.nan
        elif k=='P/B':z=np.clip(100-abs(x-1.4)*35,0,100) if x>0 else np.nan
        elif k=='NPL':z=np.clip(100-x*15,0,100)
        elif k=='NPL Coverage':z=np.clip(x,0,100)
        elif k=='Cost/Income':z=np.clip(100-x,0,100)
        else:z=50
        if np.isfinite(z):vals.append(z)
    return float(np.mean(vals)) if vals else np.nan


def data_quality(m,raw,price_date):
    critical=['Price','Revenue','Net Income','EPS','Equity','Assets','Debt','Cash','Operating Cash Flow','FCF','ROE','P/E','P/B']
    weights={'Price':2,'Revenue':2,'Net Income':2,'EPS':2,'Equity':2,'Assets':1,'Debt':1,'Cash':1,'Operating Cash Flow':2,'FCF':2,'ROE':2,'P/E':1,'P/B':1}
    got=sum(weights[k] for k in critical if pd.notna(m.get(k))); total=sum(weights.values()); base=got/total*100
    if not price_date or price_date=='—':base-=15
    errors=len(raw.get('errors',[])); base-=min(20,errors*2)
    return float(np.clip(base,0,100))


def risk_flags(m,valuation,sec):
    flags=[]
    if pd.notna(m.get('Debt/Equity')) and m['Debt/Equity']>2:flags.append('مديونية مرتفعة')
    if pd.notna(m.get('Net Debt/EBITDA')) and m['Net Debt/EBITDA']>4:flags.append('Net Debt/EBITDA مرتفع')
    if pd.notna(m.get('FCF')) and m['FCF']<0:flags.append('تدفق نقدي حر سلبي')
    if pd.notna(m.get('P/E')) and m['P/E']>25:flags.append('مضاعف أرباح مرتفع')
    if pd.notna(m.get('P/B')) and m['P/B']>3 and sec not in ['بنوك','خدمات مالية']:flags.append('مضاعف قيمة دفترية مرتفع')
    if pd.notna(valuation.get('fair')) and pd.notna(m.get('Price')) and m['Price']>valuation['fair']:flags.append('السعر أعلى من القيمة الأساسية')
    return flags


def analyze_one(sym,rf,mrp):
    raw=safe_yahoo_bundle(sym); price,pdate,psource=latest_price(sym); info=raw.get('info') or {}
    if pd.isna(price):price=num(info.get('currentPrice'))
    m=normalize_financials(raw,price); sec=sector(sym,info); m['_sector']=sec
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'metrics':m,'raw':raw,'price_date':pdate,'price_source':psource}


def scan_universe(symbols,rf,mrp,workers):
    out=[]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs={ex.submit(analyze_one,s,rf,mrp):s for s in symbols}
        for f in as_completed(fs):
            sym=fs[f]
            try:out.append(f.result())
            except Exception as e:out.append({'symbol':sym,'error':str(e)[:180]})
    good=[x for x in out if not x.get('error')]
    for r in good:
        peers=[x['metrics'] for x in good if x.get('sector')==r.get('sector') and x.get('symbol')!=r.get('symbol')]
        m=r['metrics']; val=valuation_engine(m,r['sector'],peers,rf,mrp); div=dividend_engine(r['raw'].get('dividends'),m.get('Price'),m); pi=piotroski_score(m); be=beneish_screen(m); al=altman_z(m,r['sector']); eq=earnings_quality(m); fin=financial_score(m,r['sector']); dq=data_quality(m,r['raw'],r['price_date'])
        val['targets']=targets_3y(m,r['sector'],val); val['risks']=risk_flags(m,val,r['sector'])
        r.update({'valuation':val,'dividend':div,'piotroski':pi,'beneish':be,'altman':al,'earnings_quality':eq,'financial_score':fin,'data_quality':dq})
        # Technical engine can be displayed separately later; never referenced here.
    return out


st.title('🏛️ المحرك المالي المؤسسي EGX')
st.caption('محرك مالي أساسي 100% — القيمة العادلة لا تستخدم أي تحليل فني. التحليل الفني، إن أضيف لاحقًا، يبقى منفصلًا تمامًا.')
with st.sidebar:
    st.header('⚙️ الإعدادات')
    workers=st.slider('عدد العمليات المتوازية',2,16,8)
    top_n=st.slider('أفضل عدد من الأسهم',5,100,20,5)
    rf=st.slider('معدل خالي من المخاطر %',5.0,30.0,16.0,0.5)/100
    mrp=st.slider('علاوة مخاطر السوق %',3.0,15.0,8.0,0.5)/100
    min_cov=st.slider('الحد الأدنى لجودة البيانات %',0,100,60,5)
    if st.button('🔄 مسح الكاش',use_container_width=True):
        st.cache_data.clear(); st.rerun()

if 'financial_results' not in st.session_state:st.session_state.financial_results=None
if st.button('🚀 تشغيل المحرك المالي',type='primary',use_container_width=True) or st.session_state.financial_results is None:
    with st.spinner(f'جاري تحليل {len(STOCKS)} سهم ماليًا…'):
        st.session_state.financial_results=scan_universe(STOCKS,rf,mrp,workers)
results=st.session_state.financial_results or []
valid=[r for r in results if not r.get('error') and r.get('data_quality',0)>=min_cov]

rows=[]
for r in valid:
    m=r['metrics']; v=r['valuation']; p=m.get('Price'); fair=v.get('fair'); upside=(fair/p-1)*100 if pd.notna(fair) and pd.notna(p) and p>0 else np.nan
    quality=np.nanmean([r['earnings_quality'].get('score'),r['piotroski'].get('score')/9*100 if pd.notna(r['piotroski'].get('score')) else np.nan])
    valuation_score=np.clip(50+(upside if pd.notna(upside) else 0)*.5,0,100) if pd.notna(upside) else np.nan
    final=np.nanmean([r['financial_score'],quality,valuation_score,r['data_quality']])
    rows.append({'الترتيب':0,'السهم':r['symbol'].replace('.CA',''),'القطاع':r['sector'],'الدرجة المالية /100':r['financial_score'],'الدرجة النهائية /100':final,'جودة البيانات /100':r['data_quality'],'السعر':p,'القيمة العادلة':fair,'محافظ':v.get('conservative'),'أساسي':v.get('base'),'متفائل':v.get('optimistic'),'شراء آمن -20%':v.get('safe_buy_20'),'شراء آمن -30%':v.get('safe_buy_30'),'الصعود %':upside,'هدف 3 سنوات أساسي':v.get('targets',{}).get('أساسي',[np.nan]*3)[2],'عائد التوزيعات %':r['dividend'].get('yield'),'استدامة التوزيعات /100':r['dividend'].get('sustainability'),'Piotroski':r['piotroski'].get('score'),'Beneish Screening':r['beneish'].get('flags'),'Altman Z':r['altman'].get('score'),'المخاطر': '؛ '.join(v.get('risks',[])) or 'لا توجد إشارة رئيسية'} )
df=pd.DataFrame(rows)
if not df.empty:
    df=df.sort_values('الدرجة النهائية /100',ascending=False,na_position='last').reset_index(drop=True); df['الترتيب']=np.arange(1,len(df)+1)

st.subheader('🏆 ترتيب الأسهم ماليًا')
if df.empty:st.warning('لا توجد نتائج بجودة البيانات المطلوبة.')
else:
    st.dataframe(df.head(top_n),use_container_width=True,hide_index=True)
    st.download_button('⬇️ تحميل CSV',df.to_csv(index=False,encoding='utf-8-sig').encode('utf-8-sig'),'EGX_Financial_Engine.csv','text/csv')

if valid:
    names=sorted([r['symbol'] for r in valid])
    sel=st.selectbox('🔎 اختر سهم للتقرير المالي الكامل',names)
    r=next(x for x in valid if x['symbol']==sel); m=r['metrics']; v=r['valuation']
    st.markdown(f'## {sel.replace(".CA","")} — {r["name"]}')
    c=st.columns(6)
    cards=[('السعر الحالي',m.get('Price')),('القيمة العادلة',v.get('fair')),('شراء آمن -20%',v.get('safe_buy_20')),('درجة مالية',r['financial_score']),('جودة البيانات',r['data_quality']),('هدف 3 سنوات',v.get('targets',{}).get('أساسي',[np.nan]*3)[2])]
    for col,(lab,x) in zip(c,cards):col.metric(lab,'—' if pd.isna(x) else f'{x:.2f}')
    st.info(f'القطاع: {r["sector"]} | آخر سعر: {r["price_source"]} | تاريخ السعر: {r["price_date"]}')
    tabs=st.tabs(['💰 القيمة العادلة','🎯 أهداف 3 سنوات','📊 المؤشرات المالية','🧪 جودة الأرباح والفحوصات','💵 التوزيعات','⚠️ المخاطر','🛡️ جودة البيانات'])
    with tabs[0]:
        sc=[]
        for name,key in [('🔴 محافظ','محافظ'),('🟢 أساسي','أساسي'),('🚀 متفائل','متفائل')]:
            z=v['scenarios'][key]; sc.append({'السيناريو':name,'القيمة':z.get('value'),'عدد النماذج المستخدمة':z.get('model_count')})
        st.dataframe(pd.DataFrame(sc),use_container_width=True,hide_index=True)
        st.dataframe(pd.DataFrame([{'النموذج':k,'القيمة':vv} for k,vv in v['scenarios']['أساسي']['models'].items()]),use_container_width=True,hide_index=True)
        st.caption('مهم: القيمة العادلة لا تستخدم RSI أو EMA أو MACD أو دعم/مقاومة أو أي إشارة فنية.')
        if v.get('fair') and m.get('Price') and m['Price']>v['fair']:st.warning('السعر الحالي أعلى من القيمة الأساسية المحسوبة.')
        elif pd.notna(v.get('fair')):st.success('السعر الحالي تحت القيمة الأساسية المحسوبة.')
    with tabs[1]:
        t=[]
        for sc in ['محافظ','أساسي','متفائل']:
            vals=v['targets'].get(sc,[np.nan]*3)
            t.append({'السيناريو':sc,'هدف سنة':vals[0],'هدف سنتين':vals[1],'هدف 3 سنوات':vals[2]})
        st.dataframe(pd.DataFrame(t),use_container_width=True,hide_index=True)
        st.caption('الأهداف مبنية على نمو مالي ومضاعفات تقييم، وليست أهدافًا فنية.')
    with tabs[2]:
        show={k:vx for k,vx in m.items() if not str(k).startswith('_')}
        st.dataframe(pd.DataFrame([{'المؤشر':k,'القيمة':vx} for k,vx in show.items()]),use_container_width=True,hide_index=True)
    with tabs[3]:
        st.dataframe(pd.DataFrame([{'الفحص':'Piotroski','النتيجة':r['piotroski'].get('score'),'التغطية':r['piotroski'].get('coverage'),'الحالة':r['piotroski'].get('status')},{'الفحص':'Beneish Screening','التحذيرات':r['beneish'].get('flags'),'الحالة':r['beneish'].get('status'),'التفاصيل':'؛ '.join(r['beneish'].get('details',[]))},{'الفحص':'Altman Z','النتيجة':r['altman'].get('score'),'الحالة':r['altman'].get('status')},{'الفحص':'جودة الأرباح','النتيجة':r['earnings_quality'].get('score'),'الحالة':r['earnings_quality'].get('status')}]),use_container_width=True,hide_index=True)
    with tabs[4]:
        st.dataframe(pd.DataFrame([r['dividend']]),use_container_width=True,hide_index=True)
    with tabs[5]:
        if v.get('risks'): 
            for x in v['risks']:st.warning('⚠️ '+x)
        else:st.success('لا توجد إشارة مخاطر رئيسية من البيانات المتاحة.')
    with tabs[6]:
        st.metric('جودة البيانات /100',f'{r["data_quality"]:.1f}')
        errs=r['raw'].get('errors',[])
        if errs:st.warning('بعض مصادر Yahoo لم تُرجع بيانات، وتم الاستمرار بدون إسقاط السهم.'); st.write(errs)
        else:st.success('لم تُسجل أخطاء مصادر رئيسية.')
        st.write({'تاريخ السعر':r['price_date'],'مصدر السعر':r['price_source']})

st.divider()
st.caption('⚠️ هذا محرك تحليل مالي مساعد وليس توصية استثمارية. لا يتم اختراع أرقام عند نقص البيانات، والنماذج غير المناسبة لنوع الشركة لا تدخل القيمة العادلة.')
