"""
Market Regime and Breadth Engine for Indian Markets.
Analyzes NIFTY 50, NIFTY BANK, India VIX, and major Sector indices
to classify the current market environment into Bullish, Neutral, or Risk-Off.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
from modules.universe import SECTORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_index_summary(ticker: str, name: str) -> Dict[str, Any]:
    """Fetch recent price and moving average metrics for an index."""
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 20:
            return {"name": name, "ticker": ticker, "price": 0.0, "change_1d": 0.0, "trend": "Unknown"}
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        df = df.dropna()

        close = df['Close'].squeeze()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna().astype(float)

        cur_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2]) if len(close) > 1 else cur_price
        change_1d = round(((cur_price - prev_price) / prev_price) * 100, 2)
        
        # EMAs
        ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema_50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
        
        # 5-day and 20-day returns
        ret_5d = round(float(((cur_price - close.iloc[-6]) / close.iloc[-6]) * 100), 2) if len(close) >= 6 else change_1d
        ret_20d = round(float(((cur_price - close.iloc[-21]) / close.iloc[-21]) * 100), 2) if len(close) >= 21 else ret_5d

        above_20 = bool(cur_price > ema_20)
        above_50 = bool(cur_price > ema_50)
        
        if above_20 and above_50:
            trend_label = "Strong Uptrend (Above 20 & 50 EMA)"
        elif above_20:
            trend_label = "Mild Uptrend (Above 20 EMA)"
        elif above_50:
            trend_label = "Pullback / Support at 50 EMA"
        else:
            trend_label = "Downtrend (Below 20 & 50 EMA)"

        return {
            "name": name,
            "ticker": ticker,
            "price": round(cur_price, 2),
            "change_1d": change_1d,
            "change_5d": ret_5d,
            "change_20d": ret_20d,
            "ema_20": round(ema_20, 2),
            "ema_50": round(ema_50, 2),
            "trend": trend_label,
            "above_20_ema": above_20,
            "above_50_ema": above_50,
        }
    except Exception as e:
        logger.warning(f"Error fetching index {name}: {e}")
        return {"name": name, "ticker": ticker, "price": 0.0, "change_1d": 0.0, "trend": "Error"}


def analyze_market_regime() -> Dict[str, Any]:
    """
    Diagnose the overarching Indian Market Regime based on NIFTY 50, India VIX,
    and Sector Breadth.
    """
    nifty_info = fetch_index_summary("^NSEI", "NIFTY 50")
    bank_nifty_info = fetch_index_summary("^NSEBANK", "NIFTY BANK")
    
    # India VIX
    vix_val = 14.5
    vix_change = 0.0
    try:
        vix_df = yf.download("^INDIAVIX", period="1mo", interval="1d", progress=False, auto_adjust=True)
        if vix_df is not None and not vix_df.empty:
            if isinstance(vix_df.columns, pd.MultiIndex):
                vix_df.columns = [col[0] if isinstance(col, tuple) else col for col in vix_df.columns]
            vix_close = vix_df['Close'].squeeze()
            if isinstance(vix_close, pd.DataFrame):
                vix_close = vix_close.iloc[:, 0]
            vix_close = vix_close.dropna().astype(float)
            vix_val = round(float(vix_close.iloc[-1]), 2)
            if len(vix_close) > 1:
                vix_prev = float(vix_close.iloc[-2])
                vix_change = round(((vix_val - vix_prev) / vix_prev) * 100, 2)
    except Exception as e:
        logger.warning(f"Error fetching VIX: {e}")

    # Fetch Sector Heatmap
    sectors_data: List[Dict[str, Any]] = []
    bullish_sectors_count = 0
    
    for sec_name, sec_ticker in SECTORS.items():
        if sec_name in ("NIFTY 50", "NIFTY BANK", "INDIA VIX"):
            continue
        sec_info = fetch_index_summary(sec_ticker, sec_name)
        sectors_data.append(sec_info)
        if sec_info.get("above_20_ema", False):
            bullish_sectors_count += 1

    total_sectors = len(sectors_data) if sectors_data else 1
    sector_breadth_pct = round((bullish_sectors_count / total_sectors) * 100, 1)

    # Determine Regime Status
    nifty_above_20 = nifty_info.get("above_20_ema", False)
    nifty_above_50 = nifty_info.get("above_50_ema", False)
    
    if nifty_above_20 and nifty_above_50 and vix_val < 18:
        regime_status = "BULLISH"
        regime_badge = "🟢 Bullish Regime"
        guidance = "Market structure is supportive. Favor breakout setups, aggressive relative strength leaders, and full position sizing."
    elif (nifty_above_20 or nifty_above_50) and vix_val <= 22:
        regime_status = "NEUTRAL"
        regime_badge = "🟡 Neutral / Rangebound"
        guidance = "Market is choppy or consolidating. Be selective with breakout trades. Favor 20 EMA pullbacks and keep tighter risk management."
    else:
        regime_status = "BEARISH"
        regime_badge = "🔴 Risk-Off / Defensive"
        guidance = "Market is under pressure. High risk of false breakouts. Reduce exposure, maintain higher cash levels, and protect capital."

    return {
        "regime_status": regime_status,
        "regime_badge": regime_badge,
        "guidance": guidance,
        "nifty_50": nifty_info,
        "bank_nifty": bank_nifty_info,
        "india_vix": {
            "value": vix_val,
            "change_pct": vix_change,
            "status": "Low / Calm" if vix_val < 15 else ("Normal" if vix_val <= 20 else "Elevated / Volatile")
        },
        "sector_breadth": {
            "bullish_sectors_count": bullish_sectors_count,
            "total_sectors": total_sectors,
            "breadth_pct": sector_breadth_pct,
        },
        "sectors": sectors_data
    }
