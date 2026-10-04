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
    """تحميل جماعي واحد لكل timeframe مع Cache. منطق التحليل لا يتغير."""
    if not symbols:
        return pd.DataFrame()
    symbols = tuple(dict.fromkeys(symbols))
    last_error = None
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            data = yf.download(
                tickers=list(symbols),
                period=period,
                interval=interval,
                group_by='ticker',
                threads=False,
                auto_adjust=True,
                progress=False,
                timeout=30
            )
            if data is not None and not data.empty:
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
# EGX INSTITUTIONAL QUANT V7 — SINGLE FILE / NO BACKTEST
# Original V9.5 technical engine retained; Backtest/WFO/OOS/Monte Carlo removed.
# ============================================================
import os, math, json
from dataclasses import dataclass
from typing import Any, Dict
import requests

st.set_page_config(page_title="EGX Institutional Quant — V9 Technical + Fundamental", page_icon="🏛️", layout="wide")

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

def num(x):
    try:
        x=float(x); return x if np.isfinite(x) else np.nan
    except Exception: return np.nan

def clean_series(s):
    if s is None: return pd.Series(dtype=float)
    return pd.to_numeric(s,errors='coerce').dropna()

def last(s):
    s=clean_series(s); return num(s.iloc[0]) if len(s) else np.nan

def prev(s):
    s=clean_series(s); return num(s.iloc[1]) if len(s)>1 else np.nan

def growth_series(s):
    s=clean_series(s)
    return (s.iloc[0]/s.iloc[1]-1)*100 if len(s)>=2 and s.iloc[1]!=0 else np.nan

def find(df,names):
    if df is None or df.empty: return None
    for n in names:
        if n in df.index: return pd.to_numeric(df.loc[n],errors='coerce')
    for idx in df.index:
        low=str(idx).lower()
        for n in names:
            if n.lower() in low or low in n.lower(): return pd.to_numeric(df.loc[idx],errors='coerce')
    return None

def val_at(s,i):
    s=clean_series(s); return num(s.iloc[i]) if len(s)>i else np.nan

def sector(sym,info):
    s=sym.replace('.CA','')
    for g,n in [(BANKS,'Banks'),(RE,'Real Estate'),(HEALTH,'Healthcare'),(TECH,'Telecom & Technology'),(ENERGY,'Energy & Petrochemicals'),(CONSUMER,'Consumer'),(CONSTRUCTION,'Construction & Engineering'),(FIN,'Financial Services')]:
        if s in g:return n
    txt=(str(info.get('sector',''))+' '+str(info.get('industry',''))).lower()
    if 'bank' in txt:return 'Banks'
    if 'real estate' in txt:return 'Real Estate'
    if any(x in txt for x in ['health','medical','pharma']):return 'Healthcare'
    if any(x in txt for x in ['telecom','software','technology','internet']):return 'Telecom & Technology'
    if any(x in txt for x in ['oil','gas','energy','petro']):return 'Energy & Petrochemicals'
    if any(x in txt for x in ['consumer','food','beverage','retail']):return 'Consumer'
    if any(x in txt for x in ['construction','engineering']):return 'Construction & Engineering'
    if any(x in txt for x in ['financial','insurance','investment']):return 'Financial Services'
    return 'Industrial & Materials'

@dataclass
class SourceResult:
    source:str; ok:bool; data:Any=None; error:str=''; timestamp:str=''

@st.cache_data(ttl=21600, show_spinner=False)
def load_yahoo_fundamentals(ticker):
    """Financial data لكل سهم مرة واحدة ثم Cache."""
    try:
        t = yf.Ticker(ticker)
        return {
            'info': t.info or {},
            'financials': t.financials,
            'balance': t.balance_sheet,
            'cashflow': t.cashflow,
            'dividends': t.dividends,
        }
    except Exception as e:
        return {
            'info': {},
            'financials': pd.DataFrame(),
            'balance': pd.DataFrame(),
            'cashflow': pd.DataFrame(),
            'dividends': pd.Series(dtype=float),
            '_error': str(e)[:180],
        }

@st.cache_data(ttl=21600, show_spinner=False)
def load_stooq_latest(ticker):
    try:
        sym=ticker.replace('.CA','').lower()+'.eg'
        u=f'https://stooq.com/q/d/l/?s={sym}&d1=20000101&i=d'
        r=requests.get(u,timeout=8,headers={'User-Agent':'Mozilla/5.0'})
        if r.ok and len(r.text)>30 and 'No data' not in r.text:
            d=pd.read_csv(pd.io.common.StringIO(r.text))
            d['Date']=pd.to_datetime(d['Date'],errors='coerce')
            d=d.dropna(subset=['Date','Close'])
            if not d.empty:
                row=d.iloc[-1]
                return (num(row['Close']),pd.Timestamp(row['Date']).strftime('%Y-%m-%d'))
    except Exception:
        pass
    return (np.nan,'—')

class DataSourceManager:
    def __init__(self,ticker): self.ticker=ticker
    def yahoo(self):
        raw=load_yahoo_fundamentals(self.ticker)
        return SourceResult('Yahoo Finance',True,raw,error=raw.get('_error',''))
    def stooq_price(self):
        price,date=load_stooq_latest(self.ticker)
        if pd.notna(price):
            d=pd.DataFrame([{'Date':pd.Timestamp(date),'Close':price}])
            return SourceResult('Stooq',True,d)
        return SourceResult('Stooq',False,error='No compatible series')

def normalize_financials(raw,price):
    info=raw['info']; inc=raw['financials']; bal=raw['balance']; cf=raw['cashflow']
    rev=find(inc,['Total Revenue','Operating Revenue','Revenue']); ni=find(inc,['Net Income','Net Income Common Stockholders']); eq=find(bal,['Stockholders Equity','Total Equity Gross Minority Interest','Common Stock Equity']); assets=find(bal,['Total Assets']); debt=find(bal,['Total Debt','Long Term Debt','Current Debt']); cash=find(bal,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']); ocf=find(cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex=find(cf,['Capital Expenditure','Capital Expenditures']); ebit=find(inc,['EBIT','Operating Income']); ebitda=find(inc,['EBITDA','Normalized EBITDA']); gross=find(inc,['Gross Profit']); eps=find(inc,['Diluted EPS','Basic EPS']); ar=find(bal,['Receivables','Accounts Receivable']); ppe=find(bal,['Net PPE','Property Plant Equipment','Net Property Plant Equipment']); dep=find(cf,['Depreciation And Amortization','Depreciation']); ca=find(bal,['Current Assets','Current Assets Total']); cl=find(bal,['Current Liabilities','Current Liabilities Total']); retained=find(bal,['Retained Earnings']); shares_s=find(inc,['Diluted Average Shares','Basic Average Shares']); shares_b=find(bal,['Ordinary Shares Number','Share Issued'])
    fcf=(pd.to_numeric(ocf,errors='coerce')-pd.to_numeric(capex,errors='coerce')) if ocf is not None and capex is not None else (pd.to_numeric(ocf,errors='coerce') if ocf is not None else pd.Series(dtype=float))
    mcap=num(info.get('marketCap')); shares=num(info.get('sharesOutstanding')); shares=shares if pd.notna(shares) else last(shares_s if shares_s is not None else shares_b)
    if pd.isna(shares) and pd.notna(mcap) and pd.notna(price) and price>0: shares=mcap/price
    R,NI,EQ,AS,D,C,OCF,FCF,EBIT,EBITDA,GP=[last(x) for x in [rev,ni,eq,assets,debt,cash,ocf,fcf,ebit,ebitda,gross]]
    invested=EQ+D-C if all(pd.notna(x) for x in [EQ,D,C]) else np.nan
    tax=num(info.get('effectiveTaxRate')); tax=tax if pd.notna(tax) and 0<=tax<=.6 else .22
    m={'Revenue':R,'Revenue Prior':prev(rev),'Net Income':NI,'Net Income Prior':prev(ni),'Equity':EQ,'Equity Prior':prev(eq),'Assets':AS,'Assets Prior':prev(assets),'Debt':D,'Debt Prior':prev(debt),'Cash':C,'Cash Prior':prev(cash),'Operating Cash Flow':OCF,'Operating Cash Flow Prior':prev(ocf),'Capex':last(capex),'FCF':FCF,'FCF Prior':prev(fcf),'EBIT':EBIT,'EBITDA':EBITDA,'Gross Profit':GP,'EPS':last(eps),'EPS Prior':prev(eps),'Receivables':last(ar),'Receivables Prior':prev(ar),'Current Assets':last(ca),'Current Assets Prior':prev(ca),'Current Liabilities':last(cl),'Current Liabilities Prior':prev(cl),'Retained Earnings':last(retained),'Market Cap':mcap,'Price':price,'Shares':shares,'Revenue Growth':growth_series(rev),'Net Income Growth':growth_series(ni),'EPS Growth':growth_series(eps),'Gross Margin':GP/R*100 if pd.notna(GP) and pd.notna(R) and R else np.nan,'EBITDA Margin':EBITDA/R*100 if pd.notna(EBITDA) and pd.notna(R) and R else np.nan,'Net Margin':NI/R*100 if pd.notna(NI) and pd.notna(R) and R else np.nan,'ROE':NI/EQ*100 if pd.notna(NI) and pd.notna(EQ) and EQ else num(info.get('returnOnEquity'))*100 if pd.notna(num(info.get('returnOnEquity'))) else np.nan,'ROA':NI/AS*100 if pd.notna(NI) and pd.notna(AS) and AS else num(info.get('returnOnAssets'))*100 if pd.notna(num(info.get('returnOnAssets'))) else np.nan,'ROIC':EBIT*(1-tax)/invested*100 if pd.notna(EBIT) and pd.notna(invested) and invested else np.nan,'FCF Margin':FCF/R*100 if pd.notna(FCF) and pd.notna(R) and R else np.nan,'Debt/Equity':D/EQ if pd.notna(D) and pd.notna(EQ) and EQ else np.nan,'Net Debt/EBITDA':(D-C)/EBITDA if all(pd.notna(x) for x in [D,C,EBITDA]) and EBITDA else np.nan,'Current Ratio':CA/CL if (CA:=last(ca)) and pd.notna(CA) and pd.notna(CL:=last(cl)) and CL else num(info.get('currentRatio')),'P/E':num(info.get('trailingPE')),'P/B':num(info.get('priceToBook')),'EV/EBITDA':num(info.get('enterpriseToEbitda'))}
    m['_series']={'revenue':rev,'ni':ni,'eps':eps,'assets':assets,'equity':eq,'debt':debt,'cash':cash,'ocf':ocf,'fcf':fcf,'gross':gross,'receivables':ar,'ppe':ppe,'dep':dep,'current_assets':ca,'current_liabilities':cl}
    return m

def piotroski_full(m):
    s=m['_series']; vals=[]
    ni0,ni1=val_at(s['ni'],0),val_at(s['ni'],1); cfo0,cfo1=val_at(s['ocf'],0),val_at(s['ocf'],1); a0,a1=val_at(s['assets'],0),val_at(s['assets'],1); d0,d1=val_at(s['debt'],0),val_at(s['debt'],1); ca0,ca1=val_at(s['current_assets'],0),val_at(s['current_assets'],1); cl0,cl1=val_at(s['current_liabilities'],0),val_at(s['current_liabilities'],1); gp0,gp1=val_at(s['gross'],0),val_at(s['gross'],1); r0,r1=val_at(s['revenue'],0),val_at(s['revenue'],1)
    roa0=ni0/a0 if pd.notna(ni0) and pd.notna(a0) and a0 else np.nan; roa1=ni1/a1 if pd.notna(ni1) and pd.notna(a1) and a1 else np.nan; cr0=ca0/cl0 if pd.notna(ca0) and pd.notna(cl0) and cl0 else np.nan; cr1=ca1/cl1 if pd.notna(ca1) and pd.notna(cl1) and cl1 else np.nan; gm0=gp0/r0 if pd.notna(gp0) and pd.notna(r0) and r0 else np.nan; gm1=gp1/r1 if pd.notna(gp1) and pd.notna(r1) and r1 else np.nan; at0=r0/a0 if pd.notna(r0) and pd.notna(a0) and a0 else np.nan; at1=r1/a1 if pd.notna(r1) and pd.notna(a1) and a1 else np.nan
    tests=[ni0>0,cfo0>0,roa0>roa1,cfo0>ni0,d0/a0<d1/a1 if all(pd.notna(x) for x in [d0,a0,d1,a1]) and a0 and a1 else False,cr0>cr1,gm0>gm1,at0>at1, m.get('Shares',np.nan)<=m.get('Shares',np.nan)]
    available=sum(pd.notna(x) for x in [ni0,cfo0,roa0, cfo0, d0,a0,d1,a1,cr0,cr1,gm0,gm1,at0,at1])
    score=sum(bool(x) for x in tests if x is not None); return {'score':score,'coverage':min(100,available/14*100),'checks':tests}

def beneish_full(m):
    s=m['_series']; ar0,ar1=val_at(s['receivables'],0),val_at(s['receivables'],1); rev0,rev1=val_at(s['revenue'],0),val_at(s['revenue'],1); gp0,gp1=val_at(s['gross'],0),val_at(s['gross'],1); a0,a1=val_at(s['assets'],0),val_at(s['assets'],1); ca0,ca1=val_at(s['current_assets'],0),val_at(s['current_assets'],1); ppe0,ppe1=val_at(s['ppe'],0),val_at(s['ppe'],1); dep0,dep1=abs(val_at(s['dep'],0)),abs(val_at(s['dep'],1)); d0,d1=val_at(s['debt'],0),val_at(s['debt'],1); ni,ocf=val_at(s['ni'],0),val_at(s['ocf'],0)
    def rr(a,b): return a/b if pd.notna(a) and pd.notna(b) and b else np.nan
    dsri=rr(ar0/rev0,ar1/rev1) if all(pd.notna(x) for x in [ar0,rev0,ar1,rev1]) and rev0 and rev1 else np.nan; gmi=rr(gp1/rev1,gp0/rev0) if all(pd.notna(x) for x in [gp0,rev0,gp1,rev1]) and rev0 and rev1 and gp0 else np.nan; aqi=rr(1-ca0/a0,1-ca1/a1) if all(pd.notna(x) for x in [ca0,a0,ca1,a1]) and a0 and a1 else np.nan; sgi=rr(rev0,rev1); depi=rr(dep1/(dep1+ppe1),dep0/(dep0+ppe0)) if all(pd.notna(x) for x in [dep0,ppe0,dep1,ppe1]) and dep0+ppe0 and dep1+ppe1 else np.nan; lvgi=rr(d0/a0,d1/a1) if all(pd.notna(x) for x in [d0,a0,d1,a1]) and a0 and a1 else np.nan; tata=rr(ni-ocf,a0) if pd.notna(ni) and pd.notna(ocf) and pd.notna(a0) and a0 else np.nan
    vals=[dsri,gmi,aqi,sgi,depi,lvgi,tata]; cov=sum(pd.notna(x) for x in vals)
    if cov<7:return {'score':np.nan,'status':'بيانات غير كافية','coverage':cov/7*100}
    score=-4.84+.92*dsri+.528*gmi+.404*aqi+.892*sgi+.115*depi-.327*lvgi+4.679*tata
    return {'score':score,'status':'إشارة تحتاج مراجعة' if score>-1.78 else 'لا توجد إشارة حسب الحد التقليدي','coverage':100.0}

def altman_z(m,sec):
    if sec=='Banks':return {'score':np.nan,'status':'غير مناسب للبنوك','coverage':0}
    A=(m.get('Current Assets',np.nan)-m.get('Current Liabilities',np.nan))/m.get('Assets',np.nan) if pd.notna(m.get('Assets')) and m.get('Assets') else np.nan; B=m.get('Retained Earnings',np.nan)/m.get('Assets',np.nan) if pd.notna(m.get('Retained Earnings')) and m.get('Assets') else np.nan; C=m.get('EBIT',np.nan)/m.get('Assets',np.nan) if pd.notna(m.get('EBIT')) and m.get('Assets') else np.nan; D=m.get('Market Cap',np.nan)/m.get('Debt',np.nan) if pd.notna(m.get('Market Cap')) and pd.notna(m.get('Debt')) and m.get('Debt') else np.nan; E=m.get('Revenue',np.nan)/m.get('Assets',np.nan) if pd.notna(m.get('Revenue')) and m.get('Assets') else np.nan
    xs=[A,B,C,D,E]; cov=sum(pd.notna(x) for x in xs)/5*100
    if cov<100:return {'score':np.nan,'status':'بيانات غير كافية','coverage':cov}
    z=1.2*A+1.4*B+3.3*C+.6*D+E; return {'score':z,'status':'مرتفع المخاطر' if z<1.8 else 'منطقة مراقبة' if z<3 else 'منطقة سليمة','coverage':100}

def earnings_quality(m):
    ni,ocf,fcf=m.get('Net Income'),m.get('Operating Cash Flow'),m.get('FCF'); vals=[]
    if pd.notna(ni) and ni!=0 and pd.notna(ocf):vals.append(np.clip(50+50*ocf/abs(ni),0,100))
    if pd.notna(ni) and ni!=0 and pd.notna(fcf):vals.append(np.clip(50+50*fcf/abs(ni),0,100))
    if pd.notna(ocf) and pd.notna(ni):vals.append(100 if ocf>=ni else 30)
    return {'score':float(np.mean(vals)) if vals else np.nan,'coverage':len(vals)/3*100,'accrual_ratio':(ocf-ni)/abs(ni) if pd.notna(ni) and ni and pd.notna(ocf) else np.nan}

def roic_quality(m):
    parts=[]
    if pd.notna(m.get('ROIC')):parts.append(np.clip(m['ROIC']*3,0,100))
    if pd.notna(m.get('FCF Margin')):parts.append(np.clip(50+m['FCF Margin']*2,0,100))
    if pd.notna(m.get('Revenue Growth')):parts.append(np.clip(50+m['Revenue Growth'],0,100))
    if pd.notna(m.get('Net Debt/EBITDA')):parts.append(np.clip(100-max(m['Net Debt/EBITDA'],0)*20,0,100))
    return float(np.mean(parts)) if parts else np.nan

def dcf_fcff(m,rf=0.16,mrp=0.08,tg=0.04,years=5):
    if m.get('_sector')=='Banks':return {'value':np.nan,'status':'DCF/FCFF غير مناسب للبنوك'}
    ebit,da,capex=m.get('EBIT'),abs(m.get('Capex',np.nan)),m.get('Capex',np.nan); debt,cash,shares=m.get('Debt'),m.get('Cash'),m.get('Shares'); mcap=m.get('Market Cap')
    tax=.22; beta=1.0
    base=m.get('FCF')
    if pd.notna(ebit) and pd.notna(da) and pd.notna(capex):base=ebit*(1-tax)+da-capex
    if pd.isna(base) or base<=0 or pd.isna(shares) or shares<=0:return {'value':np.nan,'status':'FCFF غير متاح/غير موجب'}
    ke=rf+beta*mrp; d=max(debt,0) if pd.notna(debt) else 0; wacc=ke if not pd.notna(mcap) or mcap<=0 else ke*mcap/(mcap+d)+.12*(1-tax)*d/(mcap+d); wacc=max(wacc,tg+.02)
    g0=np.clip((m.get('Revenue Growth') or 6)/100,-.05,.20); pv=0; cur=base
    for i in range(1,years+1):
        g=g0+(tg-g0)*(i-1)/(years-1); cur*=1+g; pv+=cur/(1+wacc)**i
    tv=cur*(1+tg)/(wacc-tg); ev=pv+tv/(1+wacc)**years; eqv=ev-(debt if pd.notna(debt) else 0)+(cash if pd.notna(cash) else 0); return {'value':eqv/shares,'status':'OK','wacc':wacc,'base_fcff':base,'terminal_growth':tg}

def dividend_engine(dividends,price,m):
    try:
        s=pd.to_numeric(dividends,errors='coerce').dropna(); s=s[s>0]
        if s.empty:return {'yield':np.nan,'sustainability':np.nan,'last':np.nan,'payout':np.nan}
        now=pd.Timestamp.now(tz=s.index.tz) if getattr(s.index,'tz',None) else pd.Timestamp.now(); ttm=s[s.index>=now-pd.Timedelta(days=365)].sum(); annual=[]
        for y in range(3):annual.append(float(s[(s.index>=now-pd.Timedelta(days=365*(y+1)))&(s.index<now-pd.Timedelta(days=365*y))].sum()))
        payout=annual[0]/m['Net Income']*100 if annual[0]>0 and pd.notna(m.get('Net Income')) and m['Net Income']>0 else np.nan; fcfp=annual[0]/m['FCF']*100 if annual[0]>0 and pd.notna(m.get('FCF')) and m['FCF']>0 else np.nan
        sus=np.nanmean([np.clip(100-abs((payout if pd.notna(payout) else 50)-50),0,100),np.clip(100-abs((fcfp if pd.notna(fcfp) else 50)-50),0,100),80 if len(s)>2 else 40])
        return {'yield':float(ttm/price*100) if pd.notna(price) and price else np.nan,'sustainability':float(sus),'last':float(s.iloc[-1]),'payout':payout,'fcf_payout':fcfp}
    except Exception:return {'yield':np.nan,'sustainability':np.nan,'last':np.nan,'payout':np.nan}

def financial_score(m,sec):
    rules=SECTOR_RULES.get(sec,SECTOR_RULES['Industrial & Materials']); vals=[]
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



def relative_valuation(target, peers, sec):
    valid=[x for x in peers if x.get('symbol')!=target.get('symbol')]
    def med(key):
        vals=[num(x.get(key)) for x in valid]; vals=[x for x in vals if pd.notna(x) and x>0 and x<100]
        return float(np.median(vals)) if vals else np.nan
    pe,pb,ev=med('P/E'),med('P/B'),med('EV/EBITDA')
    eps,bv,shares,ebitda,debt,cash=target.get('EPS'),target.get('Equity'),target.get('Shares'),target.get('EBITDA'),target.get('Debt'),target.get('Cash')
    vals=[]
    if sec=='Banks':
        if pd.notna(pe) and pd.notna(eps) and eps>0: vals.append(eps*pe)
        if pd.notna(pb) and pd.notna(bv) and pd.notna(shares) and shares>0: vals.append((bv/shares)*pb)
    else:
        if pd.notna(pe) and pd.notna(eps) and eps>0: vals.append(eps*pe)
        if pd.notna(pb) and pd.notna(bv) and pd.notna(shares) and shares>0: vals.append((bv/shares)*pb)
        if pd.notna(ev) and pd.notna(ebitda) and pd.notna(shares) and shares>0: vals.append((ebitda*ev-(debt if pd.notna(debt) else 0)+(cash if pd.notna(cash) else 0))/shares)
    return {'value':float(np.median(vals)) if vals else np.nan,'P/E Median':pe,'P/B Median':pb,'EV/EBITDA Median':ev,'methods':len(vals)}

def latest_price_from_daily(data,symbol):
    """السعر وآخر شمعة من الـDaily Batch نفسه، بدون request إضافي."""
    try:
        d=extract_symbol_data(data,symbol)
        if d.empty:
            return np.nan,'—'
        row=d.iloc[-1]
        return num(row['Close']),pd.Timestamp(d.index[-1]).strftime('%Y-%m-%d')
    except Exception:
        return np.nan,'—'

def source_price(ticker):
    """Fallback فقط عند فشل الـDaily Batch."""
    return np.nan,'—',[]

def analyze_one(sym,daily,weekly,monthly,capital,risk_percent,rf,mrp,tg):
    ds=DataSourceManager(sym).yahoo()
    info=ds.data.get('info',{})
    price,pdate=latest_price_from_daily(daily,sym)
    backups=[]
    if pd.isna(price):
        price=num(info.get('currentPrice'))
        if pd.notna(price):
            pdate='Yahoo info'
    if pd.isna(price):
        sp,sd=load_stooq_latest(sym)
        if pd.notna(sp):
            price,pdate=sp,sd
            backups=[('Stooq',sp,sd)]
    m=normalize_financials(ds.data,price)
    sec=sector(sym,info)
    m['_sector']=sec
    # نحافظ على نفس منطق النسخة الأصلية: Market Proxy لكل سهم، لكن بدون تحميل بيانات جديدة.
    market=build_market_return_proxy(daily,[sym])
    v9=process(sym,daily,weekly,monthly,capital,risk_percent,market)
    pi=piotroski_full(m); be=beneish_full(m); al=altman_z(m,sec); eq=earnings_quality(m); rq=roic_quality(m)
    div=dividend_engine(ds.data.get('dividends',pd.Series(dtype=float)),price,m)
    m['Dividend Yield']=div.get('yield')
    dcf=dcf_fcff(m,rf,mrp,tg)
    technical=num(v9.get('التقييم',v9.get('Technical Score',v9.get('score',np.nan))))
    dq=np.mean([pd.notna(m.get(k)) for k in ['Price','Revenue','Net Income','Equity','Assets','Debt','Cash','Operating Cash Flow','FCF','EBIT','EPS','P/E','P/B','ROE','ROIC']])*100
    quality=np.nanmean([pi['score']/9*100 if pi['coverage']>=55 else np.nan,100 if be.get('score',0)<=-1.78 else 50, al['score']*25 if pd.notna(al.get('score')) else np.nan,eq['score'],rq])
    return {'symbol':sym,'name':info.get('longName',sym),'sector':sec,'metrics':m,'v9':v9,'piotroski':pi,'beneish':be,'altman':al,'earnings_quality':eq,'roic_quality':rq,'dividend':div,'dcf':dcf,'relative':{'value':np.nan},'technical':technical,'data_quality':dq,'price_date':pdate,'price_source':'Yahoo batch daily' if pd.notna(price) and pdate not in ('Yahoo info','—') and not backups else ('Yahoo info' if pdate=='Yahoo info' else 'Stooq'),'backup_prices':backups}

def scan_universe(symbols,period_d,period_w,period_m,capital,risk,rf,mrp,tg,workers):
    symbols=tuple(dict.fromkeys(symbols))

    # ========================================================
    # PRICE DATA: 3 requests فقط لكل الـUniverse
    # ========================================================
    daily=load_data(symbols,period_d,'1d')
    weekly=load_data(symbols,period_w,'1wk')
    monthly=load_data(symbols,period_m,'1mo')

    out=[]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs={ex.submit(analyze_one,s,daily,weekly,monthly,capital,risk,rf,mrp,tg):s for s in symbols}
        for f in as_completed(fs):
            try: out.append(f.result())
            except Exception as e: out.append({'symbol':fs[f],'error':str(e)[:180]})

    good=[r for r in out if not r.get('error')]
    for r in good:
        peers=[x['metrics'] for x in good if x.get('sector')==r.get('sector') and x.get('symbol')!=r.get('symbol')]
        rv=relative_valuation(r['metrics'],peers,r['sector'])
        r['relative']=rv
        candidates=[x for x in [r['dcf'].get('value'),rv.get('value')] if pd.notna(x) and x>0]
        r['fair_value']=float(np.median(candidates)) if candidates else np.nan
        p=r['metrics'].get('Price')
        r['upside']=(r['fair_value']/p-1)*100 if candidates and pd.notna(p) and p else np.nan
    return out

# Backtest/WFO/OOS/Monte Carlo are intentionally absent.


def process(symbol,daily,weekly,monthly,capital,risk_percent,market_return_20=0.0):
    clean_symbol=symbol.replace('.CA','')
    try:
        df_d=extract_symbol_data(daily,symbol); df_w=extract_symbol_data(weekly,symbol); df_m=extract_symbol_data(monthly,symbol)
        if df_d.empty:return {'السهم':clean_symbol,'الحالة':'❌ لا توجد بيانات يومية'}
        if len(df_d)<MIN_DAILY_ROWS:return {'السهم':clean_symbol,'الحالة':'❌ بيانات يومية غير كافية'}
        if df_w.empty or len(df_w)<MIN_WEEKLY_ROWS:return {'السهم':clean_symbol,'الحالة':'❌ بيانات أسبوعية غير كافية'}
        if df_m.empty or len(df_m)<MIN_MONTHLY_ROWS:return {'السهم':clean_symbol,'الحالة':'❌ بيانات شهرية غير كافية'}
        last_candle_date=pd.Timestamp(df_d.index[-1]).strftime('%Y-%m-%d')
        df_d['market_return_20']=market_return_20
        result=analyze(df_d,df_w,df_m,capital,risk_percent)
        result['تاريخ آخر شمعة Close']=last_candle_date; result['السهم']=clean_symbol; result['الحالة']='✅ تم التحليل'
        return result
    except Exception as e:return {'السهم':clean_symbol,'الحالة':f'❌ {str(e)[:160]}'}


st.title("🏛️ EGX Institutional Quant — V9 Technical + Fundamental")
st.caption("V9.5 Technical Engine + DCF/FCFF + Relative/Forensic Quality — بدون Backtest/WFO/OOS/Monte Carlo")
with st.sidebar:
    st.header("⚙️ الإعدادات")
    period_d=st.selectbox("Daily",["1y","2y","3y","5y","max"],index=2)
    period_w=st.selectbox("Weekly",["3y","5y","10y","max"],index=2)
    period_m=st.selectbox("Monthly",["10y","15y","20y","max"],index=1)
    workers=st.slider("Workers",2,16,8)
    top_n=st.slider("أفضل N",5,100,20,5)
    capital=st.number_input("رأس المال",1000.0,100000000.0,100000.0,5000.0)
    risk=st.slider("المخاطرة %",0.5,10.0,2.0,0.5)
    rf=st.slider("Risk-free %",5.0,30.0,16.0,0.5)/100
    mrp=st.slider("MRP %",3.0,15.0,8.0,0.5)/100
    tg=st.slider("Terminal Growth %",1.0,6.0,4.0,0.25)/100
    min_cov=st.slider("حد جودة البيانات %",0,100,60,5)
    if st.button("🔄 مسح الكاش"):
        st.cache_data.clear(); st.rerun()
if 'results' not in st.session_state: st.session_state.results=None
if st.button("🚀 تشغيل التحليل",type="primary",use_container_width=True) or st.session_state.results is None:
    with st.spinner(f"جاري تحليل {len(STOCKS)} سهم…"):
        st.session_state.results=scan_universe(STOCKS,period_d,period_w,period_m,capital,risk,rf,mrp,tg,workers)
results=st.session_state.results or []
valid=[r for r in results if not r.get('error') and r.get('data_quality',0)>=min_cov]
rows=[]
for r in valid:
    m=r['metrics']; fv=r.get('fair_value',r['dcf'].get('value')); p=m.get('Price'); upside=(fv/p-1)*100 if pd.notna(fv) and pd.notna(p) and p else np.nan
    fin=financial_score(m,r['sector']); tech=r['technical'] if pd.notna(r['technical']) else 50; qual=np.nanmean([r['earnings_quality'].get('score'),r['roic_quality'],r['piotroski']['score']/9*100]); val=np.clip(50+(upside if pd.notna(upside) else 0)*.5,0,100); final=np.nanmean([fin,qual,val,tech,r['data_quality']])
    rows.append({'السهم':r['symbol'].replace('.CA',''),'القطاع':r['sector'],'Final Score':final,'Financial':fin,'Quality':qual,'Valuation':val,'Technical V9':tech,'Data Quality':r['data_quality'],'السعر':p,'القيمة العادلة DCF':fv,'الصعود %':upside,'Piotroski':r['piotroski']['score'],'Beneish M':r['beneish'].get('score'),'Altman Z':r['altman'].get('score'),'Dividend Yield %':r['dividend'].get('yield'),'آخر شمعة V9':r['v9'].get('تاريخ آخر شمعة Close','—'),'مصدر السعر':r['price_source']})
df=pd.DataFrame(rows)
if not df.empty:
    df=df.sort_values('Final Score',ascending=False,na_position='last').reset_index(drop=True); df.insert(0,'الترتيب',np.arange(1,len(df)+1))
st.subheader('🏆 Ranking')
if df.empty: st.warning('لا توجد نتائج ضمن حد جودة البيانات.')
else:
    st.dataframe(df.head(top_n),use_container_width=True,hide_index=True)
    st.download_button('⬇️ CSV',df.to_csv(index=False,encoding='utf-8-sig').encode('utf-8-sig'),'EGX_Institutional_No_Backtest.csv','text/csv')

if valid:
    sel=st.selectbox('اختر سهم للتقرير العميق',sorted([r['symbol'] for r in valid]))
    r=next(x for x in valid if x['symbol']==sel); m=r['metrics']
    st.subheader(f"🔎 {sel.replace('.CA','')} — {r['name']}")
    c=st.columns(6)
    for col,label,val in zip(c,['Technical V9','Data Quality','DCF Fair Value','Price','Piotroski','Earnings Quality'],[r['technical'],r['data_quality'],r['dcf'].get('value'),m.get('Price'),r['piotroski']['score'],r['earnings_quality'].get('score')]): col.metric(label,'—' if pd.isna(val) else f'{val:.2f}')
    tabs=st.tabs(['💰 Valuation','🧪 Forensic','📊 Financial','📈 V9 Technical','💵 Dividend','🛡️ Data'])
    with tabs[0]: st.dataframe(pd.DataFrame([{'Model':'DCF/FCFF','Value':r['dcf'].get('value'),'WACC':r['dcf'].get('wacc'),'Status':r['dcf'].get('status')},{'Model':'Sector Relative','Value':r['relative'].get('value'),'P/E Median':r['relative'].get('P/E Median'),'P/B Median':r['relative'].get('P/B Median'),'EV/EBITDA Median':r['relative'].get('EV/EBITDA Median')},{'Model':'Blended Fair Value','Value':r.get('fair_value')},{'Model':'Buy 20% MOS','Value':r['dcf'].get('value')*.8 if pd.notna(r['dcf'].get('value')) else np.nan},{'Model':'Buy 30% MOS','Value':r['dcf'].get('value')*.7 if pd.notna(r['dcf'].get('value')) else np.nan}]),use_container_width=True,hide_index=True)
    with tabs[1]: st.dataframe(pd.DataFrame([{'Model':'Piotroski','Value':r['piotroski']['score'],'Coverage %':r['piotroski']['coverage']},{'Model':'Beneish','Value':r['beneish'].get('score'),'Coverage %':r['beneish'].get('coverage'),'Status':r['beneish'].get('status')},{'Model':'Altman Z','Value':r['altman'].get('score'),'Coverage %':r['altman'].get('coverage'),'Status':r['altman'].get('status')}]),use_container_width=True,hide_index=True)
    with tabs[2]: st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in m.items() if not k.startswith('_')]),use_container_width=True,hide_index=True)
    with tabs[3]: st.dataframe(pd.DataFrame([{'Metric':k,'Value':v} for k,v in r['v9'].items()]),use_container_width=True,hide_index=True)
    with tabs[4]: st.dataframe(pd.DataFrame([r['dividend']]),use_container_width=True,hide_index=True)
    with tabs[5]: st.write({'Data Quality %':r['data_quality'],'Price Date':r['price_date'],'Price Source':r['price_source'],'Backup Prices':r['backup_prices'],'V9 Last Candle':r['v9'].get('تاريخ آخر شمعة Close','—')})
st.divider(); st.caption('تحليل كمي مساعد لاتخاذ القرار وليس ضمانًا للنتائج. لا يحتوي هذا الإصدار على Backtest أو WFO/OOS أو Monte Carlo.')
