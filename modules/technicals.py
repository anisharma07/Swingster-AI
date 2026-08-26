"""
Technical Analysis and Indicator calculation module for Indian Equities.
Computes EMAs (20, 50, 200), RSI, MACD, Volume Multiplier, ATR, Breakout setups,
and calculates suggested Swing Trade structures (Entry, Stop Loss, Target 1, Target 2, R:R).
"""

import logging
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import yfinance as yf
from modules.universe import to_yf_symbol, from_yf_symbol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    series = series.astype(float)
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD Line, Signal Line, and Histogram."""
    series = series.astype(float)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr


def fetch_historical_ohlcv(symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """Fetch daily historical OHLCV data for an Indian stock ticker via Yahoo Finance."""
    yf_sym = to_yf_symbol(symbol)
    try:
        df = yf.download(yf_sym, period=period, interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 30:
            return None
        
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        df = df.dropna()
        return df
    except Exception as e:
        logger.warning(f"Error fetching OHLCV for {symbol}: {e}")
        return None


def analyze_technicals(symbol: str, df: Optional[pd.DataFrame] = None) -> Optional[Dict[str, Any]]:
    """
    Run comprehensive technical analysis on an Indian equity ticker.
    Calculates EMAs, RSI, MACD, Volume Multiplier, ATR, Setups, and Swing Trade Structure.
    """
    if df is None:
        df = fetch_historical_ohlcv(symbol, period="1y")
    
    if df is None or len(df) < 30:
        return None

    # Ensure 1D Series
    close = df['Close'].squeeze()
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    
    volume = df['Volume'].squeeze()
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    high = df['High'].squeeze()
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]

    low = df['Low'].squeeze()
    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]

    close = close.astype(float)
    high = high.astype(float)
    low = low.astype(float)
    volume = volume.astype(float)

    # 1. Moving Averages
    ema_20 = close.ewm(span=20, adjust=False).mean()
    ema_50 = close.ewm(span=50, adjust=False).mean()
    ema_200 = close.ewm(span=200, adjust=False).mean() if len(df) >= 200 else close.ewm(span=len(df), adjust=False).mean()
    
    # 2. Momentum & Oscillators
    rsi = compute_rsi(close, 14)
    macd_line, macd_signal, macd_hist = compute_macd(close, 12, 26, 9)
    roc_20 = ((close - close.shift(20)) / close.shift(20)) * 100

    # 3. Volume Indicators
    vol_sma_20 = volume.rolling(window=20).mean()
    cur_vol = float(volume.iloc[-1])
    avg_vol_20 = float(vol_sma_20.iloc[-1]) if not pd.isna(vol_sma_20.iloc[-1]) else cur_vol
    vol_multiplier = round(float(cur_vol / avg_vol_20), 2) if avg_vol_20 > 0 else 1.0

    # 4. Volatility & Ranges
    atr = compute_atr(high, low, close, 14)
    cur_close = float(close.iloc[-1])
    cur_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else (cur_close * 0.02)
    atr_pct = round((cur_atr / cur_close) * 100, 2)

    # 52-week High / Low
    high_52w = float(high.tail(252).max()) if len(df) >= 252 else float(high.max())
    low_52w = float(low.tail(252).min()) if len(df) >= 252 else float(low.min())
    pct_from_52w_high = round(((cur_close - high_52w) / high_52w) * 100, 2)

    # 20-day High / Low
    high_20d = float(high.iloc[-21:-1].max()) if len(df) > 20 else cur_close
    is_20d_high_breakout = cur_close >= high_20d

    # Current Indicator Values
    cur_ema_20 = float(ema_20.iloc[-1])
    cur_ema_50 = float(ema_50.iloc[-1])
    cur_ema_200 = float(ema_200.iloc[-1])
    cur_rsi = round(float(rsi.iloc[-1]), 2)
    cur_macd = round(float(macd_line.iloc[-1]), 2)
    cur_macd_signal = round(float(macd_signal.iloc[-1]), 2)
    cur_macd_hist = round(float(macd_hist.iloc[-1]), 2)
    cur_roc_20 = round(float(roc_20.iloc[-1]), 2) if not pd.isna(roc_20.iloc[-1]) else 0.0

    # Trend & Setup Diagnoses
    is_ema_bullish_stack = bool(cur_close > cur_ema_20 > cur_ema_50 > cur_ema_200)
    is_price_above_20ema = bool(cur_close > cur_ema_20)
    is_price_above_50ema = bool(cur_close > cur_ema_50)
    is_price_above_200ema = bool(cur_close > cur_ema_200)
    is_52w_high_breakout = bool(pct_from_52w_high >= -2.0)
    
    # 20 EMA Pullback Setup (in strong uptrend, price within 1.8% of 20 EMA)
    is_pullback_20ema = bool((cur_ema_20 > cur_ema_50) and (abs(cur_close - cur_ema_20) / cur_ema_20 <= 0.018) and (cur_close >= cur_ema_50))
    
    # Higher Highs / Higher Lows structure (last 10 days vs previous 15 days)
    recent_high = float(high.iloc[-10:].max())
    prev_high = float(high.iloc[-25:-10].max()) if len(df) >= 25 else recent_high
    recent_low = float(low.iloc[-10:].min())
    prev_low = float(low.iloc[-25:-10].min()) if len(df) >= 25 else recent_low
    is_higher_high_structure = bool((recent_high >= prev_high) and (recent_low >= prev_low))

    # Setup Identification Tag
    identified_setups = []
    if is_52w_high_breakout:
        identified_setups.append("52-Week High Breakout")
    if is_20d_high_breakout and not is_52w_high_breakout:
        identified_setups.append("20-Day Consolidation Breakout")
    if is_pullback_20ema:
        identified_setups.append("Pullback to 20 EMA")
    if vol_multiplier >= 2.0:
        identified_setups.append("High Volume Surge (>2x)")
    elif vol_multiplier >= 1.5:
        identified_setups.append("Volume Expansion (>1.5x)")
    if is_ema_bullish_stack and not identified_setups:
        identified_setups.append("Strong EMA Trend (Bullish Stack)")
    if not identified_setups:
        identified_setups.append("Rangebound / Developing")

    primary_setup = identified_setups[0]

    # Calculate Technical Score (0 to 100)
    tech_score = 0.0
    # 1. Trend Alignment (max 35)
    if is_ema_bullish_stack:
        tech_score += 35
    elif is_price_above_20ema and is_price_above_50ema:
        tech_score += 25
    elif is_price_above_20ema:
        tech_score += 15
    
    # 2. Momentum & RSI (max 25)
    if 55 <= cur_rsi <= 72:
        tech_score += 15
    elif 50 <= cur_rsi < 55 or 72 < cur_rsi <= 80:
        tech_score += 10
    elif cur_rsi < 40:
        tech_score -= 5

    if cur_macd_hist > 0 and cur_macd > cur_macd_signal:
        tech_score += 10
    
    # 3. Volume & Breakout (max 25)
    if vol_multiplier >= 2.0:
        tech_score += 15
    elif vol_multiplier >= 1.3:
        tech_score += 10
    
    if is_52w_high_breakout or is_20d_high_breakout:
        tech_score += 10
    elif is_pullback_20ema:
        tech_score += 8

    # 4. Structure (max 15)
    if is_higher_high_structure:
        tech_score += 15
    
    tech_score = min(100.0, max(0.0, tech_score))

    # Suggested Swing Trade Structure Levels
    risk_distance = max(cur_atr * 1.3, cur_close * 0.025)
    suggested_stop = round(cur_close - risk_distance, 2)
    risk_amount = cur_close - suggested_stop
    suggested_target_1 = round(cur_close + (risk_amount * 2.0), 2)  # 2R
    suggested_target_2 = round(cur_close + (risk_amount * 3.0), 2)  # 3R
    rr_ratio = "1 : 2.5"

    return {
        "symbol": from_yf_symbol(symbol),
        "close": round(cur_close, 2),
        "change_pct_1d": round(float(((cur_close - close.iloc[-2]) / close.iloc[-2]) * 100), 2) if len(close) > 1 else 0.0,
        "ema_20": round(cur_ema_20, 2),
        "ema_50": round(cur_ema_50, 2),
        "ema_200": round(cur_ema_200, 2),
        "rsi": cur_rsi,
        "macd": cur_macd,
        "macd_signal": cur_macd_signal,
        "macd_hist": cur_macd_hist,
        "roc_20": cur_roc_20,
        "volume": int(cur_vol),
        "avg_volume_20": int(avg_vol_20),
        "volume_multiplier": vol_multiplier,
        "atr": round(cur_atr, 2),
        "atr_pct": atr_pct,
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_from_52w_high": pct_from_52w_high,
        "is_ema_bullish_stack": is_ema_bullish_stack,
        "is_52w_high_breakout": is_52w_high_breakout,
        "is_20d_high_breakout": is_20d_high_breakout,
        "is_pullback_20ema": is_pullback_20ema,
        "is_higher_high_structure": is_higher_high_structure,
        "primary_setup": primary_setup,
        "all_setups": identified_setups,
        "technical_score": round(tech_score, 1),
        "trade_structure": {
            "entry": round(cur_close, 2),
            "stop_loss": suggested_stop,
            "stop_loss_pct": round(((suggested_stop - cur_close) / cur_close) * 100, 2),
            "target_1": suggested_target_1,
            "target_1_pct": round(((suggested_target_1 - cur_close) / cur_close) * 100, 2),
            "target_2": suggested_target_2,
            "target_2_pct": round(((suggested_target_2 - cur_close) / cur_close) * 100, 2),
            "risk_reward": rr_ratio,
        }
    }
