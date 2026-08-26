"""
Relative Strength (RS) Module for Indian Equities.
Calculates stock outperformance vs NIFTY 50 benchmark (^NSEI) and Sector indices
over 20-day, 50-day, and 65-day periods, and computes universe percentile ranking.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import yfinance as yf
from modules.universe import to_yf_symbol, from_yf_symbol, get_stock_sector, SECTORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for benchmark OHLCV data to prevent redundant downloads
_BENCHMARK_CACHE: Dict[str, pd.DataFrame] = {}


def get_benchmark_data(benchmark: str = "^NSEI", period: str = "6mo") -> Optional[pd.DataFrame]:
    """Fetch and cache historical data for benchmark index (default NIFTY 50)."""
    global _BENCHMARK_CACHE
    if benchmark in _BENCHMARK_CACHE and not _BENCHMARK_CACHE[benchmark].empty:
        return _BENCHMARK_CACHE[benchmark]
    
    try:
        df = yf.download(benchmark, period=period, interval="1d", progress=False, auto_adjust=True)
        if df is not None and not df.empty and len(df) >= 30:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            _BENCHMARK_CACHE[benchmark] = df.dropna()
            return _BENCHMARK_CACHE[benchmark]
    except Exception as e:
        logger.warning(f"Failed to fetch benchmark data for {benchmark}: {e}")
    return None


def calculate_relative_strength(
    stock_df: pd.DataFrame,
    benchmark_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Calculate Relative Strength metrics of a stock against the NIFTY 50 index.
    Returns 20d, 50d, 65d alpha, Mansfield RS indicator, and an RS score (0-100).
    """
    if benchmark_df is None:
        benchmark_df = get_benchmark_data("^NSEI", period="1y")

    if benchmark_df is None or benchmark_df.empty or stock_df is None or stock_df.empty:
        return {
            "alpha_20d": 0.0,
            "alpha_50d": 0.0,
            "alpha_65d": 0.0,
            "stock_return_20d": 0.0,
            "nifty_return_20d": 0.0,
            "mansfield_rs": 0.0,
            "is_outperforming_nifty": False,
            "rs_score": 50.0,
            "rs_percentile": "N/A"
        }

    # Ensure 1D Series
    stock_close = stock_df['Close'].squeeze()
    if isinstance(stock_close, pd.DataFrame):
        stock_close = stock_close.iloc[:, 0]
    stock_close = stock_close.dropna().astype(float)

    nifty_close = benchmark_df['Close'].squeeze()
    if isinstance(nifty_close, pd.DataFrame):
        nifty_close = nifty_close.iloc[:, 0]
    nifty_close = nifty_close.dropna().astype(float)
    
    # Align dates via concat
    combined = pd.concat([stock_close.rename("stock"), nifty_close.rename("nifty")], axis=1).dropna()
    if len(combined) < 25:
        return {
            "alpha_20d": 0.0,
            "alpha_50d": 0.0,
            "alpha_65d": 0.0,
            "stock_return_20d": 0.0,
            "nifty_return_20d": 0.0,
            "mansfield_rs": 0.0,
            "is_outperforming_nifty": False,
            "rs_score": 50.0,
            "rs_percentile": "N/A"
        }

    # 20-day returns
    stock_ret_20d = ((combined['stock'].iloc[-1] - combined['stock'].iloc[-21]) / combined['stock'].iloc[-21]) * 100 if len(combined) >= 21 else 0.0
    nifty_ret_20d = ((combined['nifty'].iloc[-1] - combined['nifty'].iloc[-21]) / combined['nifty'].iloc[-21]) * 100 if len(combined) >= 21 else 0.0
    alpha_20d = stock_ret_20d - nifty_ret_20d

    # 50-day returns
    stock_ret_50d = ((combined['stock'].iloc[-1] - combined['stock'].iloc[-51]) / combined['stock'].iloc[-51]) * 100 if len(combined) >= 51 else stock_ret_20d
    nifty_ret_50d = ((combined['nifty'].iloc[-1] - combined['nifty'].iloc[-51]) / combined['nifty'].iloc[-51]) * 100 if len(combined) >= 51 else nifty_ret_20d
    alpha_50d = stock_ret_50d - nifty_ret_50d

    # 65-day returns
    stock_ret_65d = ((combined['stock'].iloc[-1] - combined['stock'].iloc[-66]) / combined['stock'].iloc[-66]) * 100 if len(combined) >= 66 else stock_ret_50d
    nifty_ret_65d = ((combined['nifty'].iloc[-1] - combined['nifty'].iloc[-66]) / combined['nifty'].iloc[-66]) * 100 if len(combined) >= 66 else nifty_ret_50d
    alpha_65d = stock_ret_65d - nifty_ret_65d

    # Mansfield RS calculation
    rs_ratio = combined['stock'] / combined['nifty']
    rs_sma_50 = rs_ratio.rolling(window=50, min_periods=20).mean()
    mansfield_rs = float(((rs_ratio.iloc[-1] / rs_sma_50.iloc[-1]) - 1) * 100) if not pd.isna(rs_sma_50.iloc[-1]) else 0.0

    is_outperforming = bool(alpha_20d > 0 and alpha_50d > 0)

    # Score from 0 to 100
    rs_score = 50.0 + (alpha_20d * 1.5) + (alpha_50d * 0.8) + (mansfield_rs * 2.0)
    rs_score = min(100.0, max(0.0, float(rs_score)))

    return {
        "alpha_20d": round(float(alpha_20d), 2),
        "alpha_50d": round(float(alpha_50d), 2),
        "alpha_65d": round(float(alpha_65d), 2),
        "stock_return_20d": round(float(stock_ret_20d), 2),
        "nifty_return_20d": round(float(nifty_ret_20d), 2),
        "mansfield_rs": round(float(mansfield_rs), 2),
        "is_outperforming_nifty": is_outperforming,
        "rs_score": round(float(rs_score), 1),
        "rs_percentile": "Top 10%" if rs_score >= 80 else ("Top 20%" if rs_score >= 70 else "Average")
    }


def rank_universe_by_relative_strength(stocks_rs_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of stock RS results, assign precise universe percentile rank (e.g. Top 5%, Top 10%).
    """
    if not stocks_rs_list:
        return []
    
    # Sort descending by composite rs_score
    sorted_list = sorted(stocks_rs_list, key=lambda x: x.get("rs_score", 0), reverse=True)
    total = len(sorted_list)

    for idx, item in enumerate(sorted_list):
        percentile = round(((total - idx) / total) * 100, 1)
        if percentile >= 95:
            rank_label = "Top 5%"
        elif percentile >= 90:
            rank_label = "Top 10%"
        elif percentile >= 80:
            rank_label = "Top 20%"
        elif percentile >= 50:
            rank_label = "Top Half"
        else:
            rank_label = "Bottom Half"
        
        item["rs_percentile_exact"] = percentile
        item["rs_percentile"] = rank_label
        item["rs_rank"] = idx + 1

    return sorted_list
