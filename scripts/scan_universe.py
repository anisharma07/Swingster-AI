#!/usr/bin/env python3
"""
CLI Script: High-Performance Batch Universe Scanner for Indian Equities Swing Setups.
Scans liquid universe (NIFTY 50, NIFTY 100, Swing Top 30), computes technical setups,
relative strength vs NIFTY, event risk, and outputs ranked candidates.
"""

import sys
import os
import argparse
import logging
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.universe import get_universe, get_stock_sector, from_yf_symbol, to_yf_symbol
from modules.technicals import analyze_technicals
from modules.relative_strength import calculate_relative_strength, get_benchmark_data, rank_universe_by_relative_strength
from modules.corporate_events import fetch_corporate_events_and_risk
from modules.scoring import calculate_composite_score

logging.basicConfig(level=logging.WARNING)


def run_scanner(universe_name: str = "swing_top30", setup_filter: str = "all", min_score: float = 0.0, max_workers: int = 10):
    symbols = get_universe(universe_name)
    yf_symbols = [to_yf_symbol(s) for s in symbols]
    
    # 1. Fetch benchmark NIFTY 50
    benchmark_df = get_benchmark_data("^NSEI", period="1y")

    # 2. Parallel Fast Fetch OHLCV for universe
    def fetch_stock_data(sym):
        try:
            yf_sym = to_yf_symbol(sym)
            df = yf.download(yf_sym, period="1y", interval="1d", progress=False, auto_adjust=True)
            if df is None or df.empty or len(df) < 30:
                return None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df = df.dropna()
            
            clean_sym = from_yf_symbol(sym)
            tech = analyze_technicals(clean_sym, df)
            if not tech:
                return None
            
            rs = calculate_relative_strength(df, benchmark_df)
            sector = get_stock_sector(clean_sym)
            
            # Quick Composite Score for Scanner Table
            tech_score = tech.get("technical_score", 50.0)
            rs_score = rs.get("rs_score", 50.0)
            vol_mult = tech.get("volume_multiplier", 1.0)
            
            liq_score = 90.0 if vol_mult >= 1.8 else (80.0 if vol_mult >= 1.3 else 60.0)
            comp_score = round((tech_score * 0.50) + (rs_score * 0.40) + (liq_score * 0.10), 1)

            return {
                "symbol": clean_sym,
                "company_name": clean_sym,
                "sector": sector,
                "composite_score": comp_score,
                "close": tech.get("close"),
                "change_1d": tech.get("change_pct_1d"),
                "primary_setup": tech.get("primary_setup"),
                "all_setups": tech.get("all_setups", []),
                "volume_multiplier": tech.get("volume_multiplier"),
                "rsi": tech.get("rsi"),
                "ema_stack_bullish": tech.get("is_ema_bullish_stack"),
                "pct_from_52w_high": tech.get("pct_from_52w_high"),
                "alpha_20d": rs.get("alpha_20d"),
                "rs_score": rs.get("rs_score"),
                "days_to_results_display": "On Demand",
                "event_risk_badge": "🟢 Normal Risk",
                "event_risk_level": "LOW",
                "trade_structure": tech.get("trade_structure"),
                "technicals": tech,
                "relative_strength": rs
            }
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_stock_data, sym) for sym in symbols]
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
    
    # 3. Percentile Rank across this cohort
    results = rank_universe_by_relative_strength(results)
    
    # 4. Sort by Composite Score descending
    results.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)

    # 5. Smart Setup Filtering
    filtered = []
    for r in results:
        if r.get("composite_score", 0) < min_score:
            continue
        
        setups_str = " ".join(r.get("all_setups", [])) + f" {r.get('primary_setup', '')}"
        pct_52w = r.get("pct_from_52w_high", -99)
        vol_m = r.get("volume_multiplier", 1.0)
        
        if setup_filter == "breakout":
            # Matches any breakout setup or stock within 3.5% of 52W / 20D high or bullish EMA trend
            is_match = ("Breakout" in setups_str) or (pct_52w >= -3.5) or ("Bullish Stack" in setups_str and pct_52w >= -8.0)
            if not is_match:
                continue
        elif setup_filter == "pullback":
            # Matches pullback or support near 20/50 EMA
            is_match = ("Pullback" in setups_str) or ("Developing" in setups_str) or (r.get("technicals", {}).get("is_pullback_20ema", False))
            if not is_match:
                continue
        elif setup_filter == "volume":
            if vol_m < 1.3:
                continue

        filtered.append(r)

    return filtered


def main():
    parser = argparse.ArgumentParser(description="Scan Indian stock universe for swing trading setups.")
    parser.add_argument("--universe", type=str, default="swing_top30", help="Universe name: swing_top30, nifty50, nifty100")
    parser.add_argument("--setup", type=str, default="all", help="Setup filter: all, breakout, pullback, volume")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum composite score threshold (0-100)")
    parser.add_argument("--top", type=int, default=15, help="Number of top candidates to display")
    args = parser.parse_args()

    print("==========================================================================================================")
    print(f"         INDIAN EQUITIES SWING SCANNER — UNIVERSE: {args.universe.upper()}                               ")
    print("==========================================================================================================")

    candidates = run_scanner(universe_name=args.universe, setup_filter=args.setup, min_score=args.min_score)

    print(f"\nFound {len(candidates)} candidates matching criteria. Showing Top {min(args.top, len(candidates))}:\n")
    print(f"{'#':<3} {'Symbol':<12} {'Score':<8} {'Price':<10} {'1D %':<8} {'Setup':<26} {'Vol Mult':<10} {'RS Rank':<10}")
    print("-" * 96)

    for idx, c in enumerate(candidates[:args.top], 1):
        score_str = f"{c.get('composite_score')}/100"
        price_str = f"₹{c.get('close'):,.2f}"
        chg_str = f"{c.get('change_1d'):+.2f}%"
        setup_str = c.get('primary_setup')[:24]
        vol_str = f"{c.get('volume_multiplier')}x"
        rs_str = c.get('rs_percentile', 'N/A')

        print(f"{idx:<3} {c.get('symbol'):<12} {score_str:<8} {price_str:<10} {chg_str:<8} {setup_str:<26} {vol_str:<10} {rs_str:<10}")

    print("==========================================================================================================")


if __name__ == "__main__":
    main()
