#!/usr/bin/env python3
"""
CLI Script: Fetch and analyze current Indian Market Regime.
Usage: python3 scripts/fetch_market_regime.py
"""

import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.market_regime import analyze_market_regime


def main():
    print("==================================================")
    print("      INDIAN MARKET REGIME SCANNER               ")
    print("==================================================")
    print("Fetching NIFTY 50, NIFTY BANK, INDIA VIX & Sectors...")
    
    data = analyze_market_regime()
    
    print(f"\nMarket Status: {data.get('regime_badge')}")
    print(f"Strategy Guidance: {data.get('guidance')}\n")
    
    nifty = data.get("nifty_50", {})
    bank = data.get("bank_nifty", {})
    vix = data.get("india_vix", {})
    breadth = data.get("sector_breadth", {})

    print(f"📊 NIFTY 50:    ₹{nifty.get('price'):,.2f} ({nifty.get('change_1d'):+.2f}%) | 20 EMA: ₹{nifty.get('ema_20'):,.2f} | {nifty.get('trend')}")
    print(f"🏦 NIFTY BANK:  ₹{bank.get('price'):,.2f} ({bank.get('change_1d'):+.2f}%) | 20 EMA: ₹{bank.get('ema_20'):,.2f} | {bank.get('trend')}")
    print(f"⚡ INDIA VIX:   {vix.get('value')} ({vix.get('change_pct'):+.2f}%) | Volatility: {vix.get('status')}")
    print(f"📈 Sector Breadth: {breadth.get('breadth_pct')}% ({breadth.get('bullish_sectors_count')}/{breadth.get('total_sectors')} sectors above 20 EMA)")

    print("\n--- SECTOR PERFORMANCE MATRIX ---")
    print(f"{'Sector':<20} {'1D %':<10} {'5D %':<10} {'20D %':<10} {'Trend'}")
    print("-" * 65)
    for sec in data.get("sectors", []):
        print(f"{sec.get('name'):<20} {sec.get('change_1d', 0):>+6.2f}%   {sec.get('change_5d', 0):>+6.2f}%   {sec.get('change_20d', 0):>+6.2f}%   {sec.get('trend')}")
    print("==================================================")


if __name__ == "__main__":
    main()
