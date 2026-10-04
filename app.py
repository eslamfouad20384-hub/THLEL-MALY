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
BACKTEST_WARMUP = 220
PIVOT_RADIUS = 3
LIQUIDITY_LOOKBACK = 20
RS_LOOKBACK = 20
DEFAULT_COMMISSION_PCT = 0.15
DEFAULT_SLIPPAGE_PCT = 0.1
DEFAULT_MAX_POSITION_PCT = 20.0

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(symbols, period, interval):
    if not symbols:
        return pd.DataFrame()
    symbols = tuple(symbols)
    last_error = None
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            data = yf.download(tickers=list(symbols), period=period, interval=interval, group_by='ticker', threads=True, auto_adjust=True, progress=False, timeout=30)
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

def _bt_signal(row, volume_threshold=1.0, rsi_threshold=50.0):
    """Backtest signal using signal-bar information only. Parameters are WFO-tunable."""
    try:
        close = float(row['Close'])
        ema20 = float(row['ema20'])
        ema50 = float(row['ema50'])
        rsi = float(row['rsi'])
        macd = float(row['macd'])
        macd_signal = float(row['macd_signal'])
        vol_ratio = float(row['volume_ratio'])
        body_pct = float(row['body_pct'])
        atr_pct = float(row['atr_pct'])
    except Exception:
        return False
    vals = [close, ema20, ema50, rsi, macd, macd_signal, vol_ratio, body_pct, atr_pct]
    if not all((np.isfinite(x) for x in vals)):
        return False
    breakout = bool(row.get('breakout', False))
    pullback = bool(row.get('pullback', False))
    immediate = close > ema20 > ema50 and rsi >= rsi_threshold and (macd > macd_signal) and (vol_ratio >= volume_threshold) and (0.015 <= atr_pct <= 0.12)
    try:
        prev_res = float(row.get('previous_resistance', np.nan))
    except Exception:
        prev_res = np.nan
    breakout_fallback = np.isfinite(prev_res) and close > prev_res and (vol_ratio >= max(1.3, volume_threshold)) and (body_pct >= 0.35) and (close > ema20 > ema50) and (0.015 <= atr_pct <= 0.12)
    pullback_fallback = close > ema20 > ema50 and (abs(close - ema20) / close <= 0.03 or abs(close - ema50) / close <= 0.05) and (rsi >= max(45, rsi_threshold - 5)) and (macd >= macd_signal)
    return bool(breakout or pullback or immediate or breakout_fallback or pullback_fallback)

def _bt_structural_targets(row, entry):
    vals = []
    for col, name in [('previous_resistance', 'مقاومة يومية سابقة'), ('resistance', 'مقاومة يومية'), ('confirmed_swing_high', 'آخر Swing High مؤكد'), ('fib_ext_1272', 'Fib 127.2%'), ('fib_ext_1618', 'Fib 161.8%'), ('fib_ext_2000', 'Fib 200%')]:
        try:
            x = float(row.get(col, np.nan))
            if np.isfinite(x) and x > entry * 1.001:
                vals.append((x, name))
        except Exception:
            pass
    vals = sorted(vals, key=lambda z: z[0])
    out = []
    for x, name in vals:
        if not out or abs(x - out[-1][0]) / max(out[-1][0], 1e-09) >= 0.008:
            out.append((x, name))
        if len(out) >= 4:
            break
    return out

def _simulate_bt_window(df, start_idx, end_idx, commission_pct=0.15, slippage_pct=0.1, volume_threshold=1.0, rsi_threshold=50.0):
    trades = []
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    next_allowed = start_idx
    signals = entries = skipped_no_target = skipped_bad_stop = 0
    warmup = max(BACKTEST_WARMUP, 220)
    for i in range(max(start_idx, warmup), min(end_idx, len(df) - 2)):
        if i < next_allowed:
            continue
        row = df.iloc[i]
        signals += 1
        try:
            needed = ['Open', 'High', 'Low', 'Close', 'ema20', 'ema50', 'rsi', 'macd', 'macd_signal', 'atr', 'volume_ratio', 'body_pct', 'atr_pct']
            if not all((np.isfinite(float(row.get(c, np.nan))) for c in needed)):
                continue
            atr_val = float(row['atr'])
            close = float(row['Close'])
            if atr_val <= 0 or close <= 0 or (not _bt_signal(row, volume_threshold, rsi_threshold)):
                continue
            raw_entry = float(df.iloc[i + 1]['Open'])
            if not np.isfinite(raw_entry) or raw_entry <= 0:
                continue
            entry = raw_entry * (1 + slippage_pct / 100.0 + commission_pct / 100.0)
            entries += 1
            try:
                swing = float(row.get('confirmed_swing_low', np.nan))
            except Exception:
                swing = np.nan
            stop = max(swing - atr_val * 0.2, entry - atr_val * 1.5) if np.isfinite(swing) and 0 < swing < entry else entry - atr_val * 1.5
            if not np.isfinite(stop) or stop <= 0 or stop >= entry:
                skipped_bad_stop += 1
                continue
            targets = _bt_structural_targets(row, entry)
            if not targets:
                skipped_no_target += 1
                continue
            tprices = [x[0] for x in targets]
            remaining = 1.0
            realized = 0.0
            tp_hits = 0
            exit_i = None
            trail = stop
            for j in range(i + 1, min(end_idx, len(df))):
                bar = df.iloc[j]
                try:
                    low = float(bar['Low'])
                    high = float(bar['High'])
                    close_j = float(bar['Close'])
                except Exception:
                    continue
                if low <= trail:
                    exit_raw = trail * (1 - slippage_pct / 100.0 - commission_pct / 100.0)
                    realized += remaining * ((exit_raw - entry) / entry)
                    remaining = 0
                    exit_i = j
                    break
                while tp_hits < len(tprices) and high >= tprices[tp_hits]:
                    qty = min(0.25, remaining)
                    exit_raw = tprices[tp_hits] * (1 - slippage_pct / 100.0 - commission_pct / 100.0)
                    realized += qty * ((exit_raw - entry) / entry)
                    remaining -= qty
                    tp_hits += 1
                    if tp_hits == 1:
                        trail = max(trail, entry)
                    else:
                        trail = max(trail, float(bar['Low']), close_j - atr_val * 1.5)
                if remaining <= 1e-09:
                    exit_i = j
                    break
                if tp_hits > 0:
                    trail = max(trail, close_j - atr_val * 1.5)
            if remaining > 1e-09:
                j = min(end_idx - 1, len(df) - 1)
                exit_raw = float(df.iloc[j]['Close']) * (1 - slippage_pct / 100.0 - commission_pct / 100.0)
                realized += remaining * ((exit_raw - entry) / entry)
                exit_i = j
            ret = float(realized)
            equity *= max(0.0001, 1 + ret)
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak)
            trades.append({'return': ret, 'tp_hits': tp_hits, 'bars': int(exit_i - i), 'entry': entry, 'entry_i': i + 1, 'exit_i': int(exit_i)})
            next_allowed = max(next_allowed, int(exit_i) + 1)
        except Exception:
            continue
    return (trades, equity, max_dd, signals, entries, skipped_no_target, skipped_bad_stop)

def _daily_returns_from_trades(trades, start_idx, end_idx):
    n = max(0, int(end_idx - start_idx))
    arr = np.zeros(n, dtype=float)
    for t in trades:
        try:
            idx = int(t['exit_i']) - int(start_idx)
            if 0 <= idx < n:
                arr[idx] = max(-0.9999, float(t['return']))
        except Exception:
            pass
    return arr

def _summarize_bt(trades, equity, max_dd, signals, entries, skipped_no_target, skipped_bad_stop, start_idx=0, end_idx=0):
    rets = np.array([t['return'] for t in trades], dtype=float) if trades else np.array([], dtype=float)
    wins = rets[rets > 0]
    losses = rets[rets < 0]
    gross_win = float(wins.sum()) if len(wins) else 0.0
    gross_loss = float(abs(losses.sum())) if len(losses) else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else 999.0 if gross_win > 0 else 0.0
    expectancy = float(rets.mean()) if len(rets) else 0.0
    daily = _daily_returns_from_trades(trades, start_idx, end_idx)
    dstd = float(daily.std(ddof=1)) if len(daily) > 1 else 0.0
    downside = daily[daily < 0]
    downstd = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0
    sharpe = daily.mean() / dstd * np.sqrt(252) if dstd > 0 else 0.0
    sortino = daily.mean() / downstd * np.sqrt(252) if downstd > 0 else 0.0
    bars = max(1, int(end_idx - start_idx))
    cagr = equity ** (252 / bars) - 1 if equity > 0 and bars > 0 else 0.0
    calmar = cagr / max_dd if max_dd > 0 else 0.0
    return {'trades': len(trades), 'closed_trades': len(trades), 'open_trades': 0, 'win_rate': len(wins) / len(rets) * 100 if len(rets) else 0.0, 'profit_pct': (equity - 1) * 100, 'max_drawdown_pct': max_dd * 100, 'profit_factor': pf, 'avg_trade_pct': expectancy * 100, 'expectancy_pct': expectancy * 100, 'avg_win_pct': wins.mean() * 100 if len(wins) else 0, 'avg_loss_pct': losses.mean() * 100 if len(losses) else 0, 'sharpe': sharpe, 'sortino': sortino, 'calmar': calmar, 'signals': signals, 'entries': entries, 'skipped_no_target': skipped_no_target, 'skipped_bad_stop': skipped_bad_stop, 'tp1_hit_rate': sum((t['tp_hits'] >= 1 for t in trades)) / len(trades) * 100 if trades else 0, 'tp2_hit_rate': sum((t['tp_hits'] >= 2 for t in trades)) / len(trades) * 100 if trades else 0, 'tp3_hit_rate': sum((t['tp_hits'] >= 3 for t in trades)) / len(trades) * 100 if trades else 0, 'tp4_hit_rate': sum((t['tp_hits'] >= 4 for t in trades)) / len(trades) * 100 if trades else 0, 'bars_used': bars}

def _beta_binomial_ci(successes, n, z=1.96):
    if n <= 0:
        return (np.nan, np.nan)
    p = successes / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (float(max(0, center - half) * 100), float(min(1, center + half) * 100))

def _score_backtest_evidence(bt):
    n = int(bt.get('trades', 0))
    pf = float(bt.get('profit_factor', 0))
    exp = float(bt.get('expectancy_pct', 0))
    dd = float(bt.get('max_drawdown_pct', 0))
    oos = float(bt.get('oos_return_pct', 0))
    wfo = float(bt.get('walk_forward_score', 0))
    ci_width = float(bt.get('tp1_ci_width', 100))
    sample = min(100, n / 50 * 100)
    pf_s = np.clip((pf - 0.8) / 2.2 * 100, 0, 100)
    exp_s = np.clip((exp + 1) / 5 * 100, 0, 100)
    dd_s = 100 - np.clip(dd / 30 * 100, 0, 100)
    oos_s = np.clip((oos + 20) / 60 * 100, 0, 100)
    ci_s = 100 - np.clip(ci_width / 60 * 100, 0, 100)
    return float(np.clip(0.2 * sample + 0.2 * pf_s + 0.15 * exp_s + 0.15 * dd_s + 0.15 * oos_s + 0.1 * wfo + 0.05 * ci_s, 0, 100))

def _optimize_wfo_params(bt, train_start, train_end, comm, slip):
    candidates = [(1.0, 50.0), (1.15, 50.0), (1.3, 50.0), (1.15, 55.0), (1.3, 55.0)]
    best = (1.0, 50.0)
    best_score = -1000000000.0
    for vol_thr, rsi_thr in candidates:
        tr, eq, dd, sg, en, sn, sb = _simulate_bt_window(bt, train_start, train_end, comm, slip, vol_thr, rsi_thr)
        if len(tr) < 5:
            continue
        x = _summarize_bt(tr, eq, dd, sg, en, sn, sb, train_start, train_end)
        score = x['profit_pct'] * 0.45 + x['expectancy_pct'] * 10 * 0.2 + min(x['profit_factor'], 5) * 10 * 0.2 - x['max_drawdown_pct'] * 0.15
        if score > best_score:
            best_score = score
            best = (vol_thr, rsi_thr)
    return best

def _true_walk_forward(bt, test_bars, comm, slip):
    n = len(bt)
    warm = max(BACKTEST_WARMUP, 220)
    available = max(0, n - warm)
    test = max(40, min(int(test_bars / 8), max(40, available // 4)))
    train = max(80, min(int(available * 0.35), 180))
    folds = []
    end_train = warm + train
    while end_train + test <= n and len(folds) < 4:
        params = _optimize_wfo_params(bt, warm, end_train, comm, slip)
        tr, eq, dd, sg, en, sn, sb = _simulate_bt_window(bt, end_train, end_train + test, comm, slip, *params)
        if tr:
            sm = _summarize_bt(tr, eq, dd, sg, en, sn, sb, end_train, end_train + test)
            folds.append({'oos_return': sm['profit_pct'], 'oos_pf': sm['profit_factor'], 'oos_dd': sm['max_drawdown_pct'], 'trades': sm['trades'], 'params': params})
        end_train += test
    if not folds:
        return {'score': 0.0, 'return': 0.0, 'trades': 0, 'pf': 0.0, 'dd': 0.0, 'folds': 0, 'positive_folds': 0, 'stability': 0.0}
    returns = np.array([f['oos_return'] for f in folds], float)
    pfs = np.array([f['oos_pf'] for f in folds], float)
    positive = int(np.sum(returns > 0))
    consistency = positive / len(folds) * 100
    mean_ret = float(returns.mean())
    median_ret = float(np.median(returns))
    dispersion = float(returns.std(ddof=1)) if len(returns) > 1 else 0
    stability = float(np.clip(100 - dispersion / (abs(mean_ret) + 10) * 100, 0, 100))
    score = float(np.clip(0.45 * consistency + 0.3 * np.clip((mean_ret + 20) / 60 * 100, 0, 100) + 0.15 * stability + 0.1 * np.clip((pfs.mean() - 0.8) / 2.2 * 100, 0, 100), 0, 100))
    return {'score': score, 'return': mean_ret, 'median_return': median_ret, 'trades': int(sum((f['trades'] for f in folds))), 'pf': float(np.mean(pfs)), 'dd': float(np.mean([f['oos_dd'] for f in folds])), 'folds': len(folds), 'positive_folds': positive, 'stability': stability}

def run_real_backtest(df, max_bars=600, commission_pct=None, slippage_pct=None, monte_carlo_runs=1000):
    empty = {'trades': 0, 'closed_trades': 0, 'open_trades': 0, 'win_rate': 0.0, 'profit_pct': 0.0, 'max_drawdown_pct': 0.0, 'profit_factor': 0.0, 'avg_trade_pct': 0.0, 'expectancy_pct': 0.0, 'avg_win_pct': 0.0, 'avg_loss_pct': 0.0, 'sharpe': 0.0, 'sortino': 0.0, 'calmar': 0.0, 'signals': 0, 'entries': 0, 'skipped_no_target': 0, 'skipped_bad_stop': 0, 'bars_used': 0, 'tp1_hit_rate': 0.0, 'tp2_hit_rate': 0.0, 'tp3_hit_rate': 0.0, 'tp4_hit_rate': 0.0, 'monte_carlo_5pct': 0.0, 'monte_carlo_median': 0.0, 'monte_carlo_95pct': 0.0, 'monte_carlo_profit_probability': 0.0, 'monte_carlo_max_dd_95pct': 0.0, 'walk_forward_score': 0.0, 'oos_return_pct': 0.0, 'wfo_stability': 0.0, 'wfo_folds': 0, 'oos_trades': 0, 'oos_profit_factor': 0.0, 'tp1_ci_low': np.nan, 'tp1_ci_high': np.nan, 'tp1_ci_width': np.nan, 'validation_score': 0.0}
    if df is None or df.empty:
        return empty
    try:
        bt = add_indicators(df.copy())
    except Exception:
        return empty
    if bt.empty:
        return empty
    comm = DEFAULT_COMMISSION_PCT if commission_pct is None else float(commission_pct)
    slip = DEFAULT_SLIPPAGE_PCT if slippage_pct is None else float(slippage_pct)
    warmup = max(BACKTEST_WARMUP, 220)
    test_bars = max(50, int(max_bars))
    start = max(warmup, len(bt) - test_bars - 1)
    end = len(bt) - 1
    trades, equity, dd, signals, entries, snt, sbs = _simulate_bt_window(bt, start, end, comm, slip)
    out = _summarize_bt(trades, equity, dd, signals, entries, snt, sbs, start, end)
    out['bars_used'] = max(0, end - start)
    n = len(trades)
    tp1_hits = sum((t['tp_hits'] >= 1 for t in trades))
    lo, hi = _beta_binomial_ci(tp1_hits, n)
    out['tp1_ci_low'] = lo
    out['tp1_ci_high'] = hi
    out['tp1_ci_width'] = hi - lo if np.isfinite(lo) else np.nan
    if trades and monte_carlo_runs:
        rng = np.random.default_rng(42)
        r = np.array([t['return'] for t in trades], float)
        terminal = []
        dds = []
        profitable = 0
        for _ in range(int(monte_carlo_runs)):
            sample = rng.choice(r, size=len(r), replace=True)
            curve = np.cumprod(np.maximum(0.0001, 1 + sample))
            term = float(curve[-1] - 1) * 100
            running = np.maximum.accumulate(curve)
            dd_sim = float(np.max((running - curve) / running) * 100) if len(curve) else 0
            terminal.append(term)
            dds.append(dd_sim)
            profitable += int(term > 0)
        out['monte_carlo_5pct'] = float(np.percentile(terminal, 5))
        out['monte_carlo_median'] = float(np.percentile(terminal, 50))
        out['monte_carlo_95pct'] = float(np.percentile(terminal, 95))
        out['monte_carlo_profit_probability'] = profitable / len(terminal) * 100
        out['monte_carlo_max_dd_95pct'] = float(np.percentile(dds, 95))
    wfo = _true_walk_forward(bt, test_bars, comm, slip)
    out['walk_forward_score'] = wfo['score']
    out['oos_return_pct'] = wfo['return']
    out['wfo_stability'] = wfo['stability']
    out['wfo_folds'] = wfo['folds']
    out['oos_trades'] = wfo['trades']
    out['oos_profit_factor'] = wfo['pf']
    out['oos_max_dd_pct'] = wfo['dd']
    out['validation_score'] = _score_backtest_evidence(out)
    return out

def estimate_historical_probabilities(bt):
    return tuple((bt.get(k, 0.0) / 100.0 for k in ['tp1_hit_rate', 'tp2_hit_rate', 'tp3_hit_rate', 'tp4_hit_rate']))

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

def calculate_trading_rank(row, backtest_enabled=True):
    """V9.5 ranking: separates current technical setup from historical statistical evidence."""
    tech = _clip_score(row.get('التقييم', np.nan), 0, 100)
    target = float(row.get('جودة الأهداف', 50)) if np.isfinite(float(row.get('جودة الأهداف', 50))) else 50
    rr = _clip_score(row.get('R/R الهدف الأول', np.nan), 0.8, 4.0)
    liq = _clip_score(row.get('السيولة Ratio', np.nan), 0.5, 2.0)
    if not backtest_enabled:
        vals = [(tech, 45), (target, 25), (rr, 15), (liq, 15)]
        return round(sum((v * w for v, w in vals if np.isfinite(v))) / sum((w for v, w in vals if np.isfinite(v))), 2)
    val = float(row.get('Validation Score', np.nan))
    wfo = float(row.get('Walk Forward Score %', np.nan))
    oos = _evidence_score(row.get('OOS Return %', np.nan), -20, 40)
    exp = _evidence_score(row.get('قيمة متوقعة %', np.nan), -2, 5)
    pf = _evidence_score(row.get('Backtest Profit Factor', np.nan), 0.8, 3.0)
    dd = 100 - _evidence_score(row.get('Backtest Max DD %', np.nan), 0, 30)
    stability = float(row.get('WFO Stability %', np.nan))
    sample = min(100, float(row.get('Backtest Trades', 0)) / 50 * 100)
    components = [(tech, 25), (val, 15), (wfo, 15), (oos, 15), (exp, 10), (pf, 7.5), (dd, 5), (stability, 5), (liq, 2.5)]
    valid = [(v, w) for v, w in components if np.isfinite(v)]
    base = sum((v * w for v, w in valid)) / sum((w for _, w in valid)) if valid else 0
    shrink = min(1.0, max(0.25, sample / 100))
    final = tech * (1 - shrink * 0.45) + base * (shrink * 0.45)
    return round(float(np.clip(final, 0, 100)), 2)

def apply_trading_ranking(df, backtest_enabled=True):
    out = df.copy()
    if out.empty:
        return out
    out['الترتيب التداولي'] = out.apply(lambda r: calculate_trading_rank(r, backtest_enabled), axis=1)
    out = out.sort_values(['الترتيب التداولي', 'التقييم'], ascending=[False, False]).reset_index(drop=True)
    out['الترتيب'] = np.arange(1, len(out) + 1)
    return out

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

def process(symbol, daily, weekly, monthly, capital, risk_percent, market_return_20=0.0, run_backtest=False, backtest_bars=300):
    clean_symbol = symbol.replace('.CA', '')
    try:
        df_d = extract_symbol_data(daily, symbol)
        df_w = extract_symbol_data(weekly, symbol)
        df_m = extract_symbol_data(monthly, symbol)
        if df_d.empty:
            return {'السهم': clean_symbol, 'الحالة': '❌ لا توجد بيانات يومية'}
        if len(df_d) < MIN_DAILY_ROWS:
            return {'السهم': clean_symbol, 'الحالة': '❌ بيانات يومية غير كافية'}
        if df_w.empty:
            return {'السهم': clean_symbol, 'الحالة': '❌ لا توجد بيانات أسبوعية'}
        if len(df_w) < MIN_WEEKLY_ROWS:
            return {'السهم': clean_symbol, 'الحالة': '❌ بيانات أسبوعية غير كافية'}
        if df_m.empty:
            return {'السهم': clean_symbol, 'الحالة': '❌ لا توجد بيانات شهرية'}
        if len(df_m) < MIN_MONTHLY_ROWS:
            return {'السهم': clean_symbol, 'الحالة': '❌ بيانات شهرية غير كافية'}
        last_candle_date = pd.Timestamp(df_d.index[-1]).strftime('%Y-%m-%d')
        df_d['market_return_20'] = market_return_20
        result = analyze(df_d, df_w, df_m, capital, risk_percent)
        result['تاريخ آخر شمعة Close'] = last_candle_date
        if run_backtest:
            bt = run_real_backtest(df_d, backtest_bars, commission_pct, slippage_pct, monte_carlo_runs)
            result['Backtest Trades'] = bt['trades']
            result['Backtest Win Rate %'] = round(bt['win_rate'], 1)
            result['Backtest Return %'] = round(bt['profit_pct'], 2)
            result['Validation Score'] = round(bt.get('validation_score', 0.0), 1)
            result['WFO Stability %'] = round(bt.get('wfo_stability', 0.0), 1)
            result['WFO Folds'] = int(bt.get('wfo_folds', 0))
            result['OOS Trades'] = int(bt.get('oos_trades', 0))
            result['OOS Profit Factor'] = round(bt.get('oos_profit_factor', 0.0), 2)
            result['OOS Max DD %'] = round(bt.get('oos_max_dd_pct', 0.0), 2)
            result['TP1 CI Low %'] = round(bt.get('tp1_ci_low', np.nan), 1) if np.isfinite(bt.get('tp1_ci_low', np.nan)) else np.nan
            result['TP1 CI High %'] = round(bt.get('tp1_ci_high', np.nan), 1) if np.isfinite(bt.get('tp1_ci_high', np.nan)) else np.nan
            result['Monte Carlo Profit Probability %'] = round(bt.get('monte_carlo_profit_probability', 0.0), 1)
            result['Monte Carlo 95% Max DD %'] = round(bt.get('monte_carlo_max_dd_95pct', 0.0), 2)
            result['Backtest Max DD %'] = round(bt['max_drawdown_pct'], 2)
            result['Backtest Profit Factor'] = round(bt['profit_factor'], 2)
            result['Backtest Signals'] = int(bt.get('signals', 0))
            result['Backtest Valid Entries'] = int(bt.get('entries', 0))
            result['Backtest No Target'] = int(bt.get('skipped_no_target', 0))
            result['Backtest Bad Stop'] = int(bt.get('skipped_bad_stop', 0))
            result['Backtest Invalid Indicators'] = 0
            result['Backtest Expectancy %'] = round(bt.get('expectancy_pct', 0.0), 3)
            result['Backtest Avg Win %'] = round(bt.get('avg_win_pct', 0.0), 2)
            result['Backtest Avg Loss %'] = round(bt.get('avg_loss_pct', 0.0), 2)
            result['Backtest Sharpe'] = round(bt.get('sharpe', 0.0), 2)
            result['Backtest Sortino'] = round(bt.get('sortino', 0.0), 2)
            result['Backtest Calmar'] = round(bt.get('calmar', 0.0), 2)
            result['Backtest TP1 Probability %'] = round(bt.get('tp1_hit_rate', 0.0), 1)
            result['Backtest TP2 Probability %'] = round(bt.get('tp2_hit_rate', 0.0), 1)
            result['Backtest TP3 Probability %'] = round(bt.get('tp3_hit_rate', 0.0), 1)
            result['Backtest TP4 Probability %'] = round(bt.get('tp4_hit_rate', 0.0), 1)
            result['Monte Carlo 5% Return %'] = round(bt.get('monte_carlo_5pct', 0.0), 2)
            result['Monte Carlo Median Return %'] = round(bt.get('monte_carlo_median', 0.0), 2)
            result['Monte Carlo 95% Return %'] = round(bt.get('monte_carlo_95pct', 0.0), 2)
            result['Walk Forward Score %'] = round(bt.get('walk_forward_score', 0.0), 1)
            result['OOS Return %'] = round(bt.get('oos_return_pct', 0.0), 2)
            result['احتمال TP1 التاريخي %'] = round(bt.get('tp1_hit_rate', 0.0), 1)
            result['احتمال TP2 التاريخي %'] = round(bt.get('tp2_hit_rate', 0.0), 1)
            result['احتمال TP3 التاريخي %'] = round(bt.get('tp3_hit_rate', 0.0), 1)
            result['احتمال TP4 التاريخي %'] = round(bt.get('tp4_hit_rate', 0.0), 1)
            result['قيمة متوقعة %'] = round(bt.get('expectancy_pct', 0.0), 3)
            result['حالة التحقق'] = '🟢 قوي' if bt.get('walk_forward_score', 0) >= 66 and bt.get('expectancy_pct', 0) > 0 and (bt.get('profit_factor', 0) > 1.1) else '🟡 محايد' if bt.get('trades', 0) >= 10 else '⚪ بيانات غير كافية'
        else:
            result['Backtest Trades'] = 0
            result['Backtest Win Rate %'] = np.nan
            result['Backtest Return %'] = np.nan
            result['Backtest Max DD %'] = np.nan
            result['Backtest Profit Factor'] = np.nan
            result['Backtest Signals'] = np.nan
            result['Backtest Valid Entries'] = np.nan
            result['Backtest No Target'] = np.nan
            result['Backtest Bad Stop'] = np.nan
            result['Backtest Invalid Indicators'] = np.nan
            for _k in ['Backtest Expectancy %', 'Backtest Avg Win %', 'Backtest Avg Loss %', 'Backtest Sharpe', 'Backtest Sortino', 'Backtest Calmar', 'Backtest TP1 Probability %', 'Backtest TP2 Probability %', 'Backtest TP3 Probability %', 'Backtest TP4 Probability %', 'Monte Carlo 5% Return %', 'Monte Carlo Median Return %', 'Monte Carlo 95% Return %', 'Monte Carlo Profit Probability %', 'Monte Carlo 95% Max DD %', 'Walk Forward Score %', 'WFO Stability %', 'WFO Folds', 'OOS Return %', 'OOS Trades', 'OOS Profit Factor', 'OOS Max DD %', 'Validation Score', 'TP1 CI Low %', 'TP1 CI High %', 'احتمال TP1 التاريخي %', 'احتمال TP2 التاريخي %', 'احتمال TP3 التاريخي %', 'احتمال TP4 التاريخي %', 'قيمة متوقعة %']:
                result[_k] = np.nan
            result['حالة التحقق'] = '⚪ Backtest غير مفعل'
        result['السهم'] = clean_symbol
        result['الحالة'] = '✅ تم التحليل'
        return result
    except Exception as e:
        return {'السهم': clean_symbol, 'الحالة': f'❌ {str(e)[:120]}'}
