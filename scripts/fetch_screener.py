#!/usr/bin/env python3
"""
CLI Script: Fetch fundamental analysis and ratios from Screener.in for an Indian stock.
Usage: python3 scripts/fetch_screener.py <SYMBOL>
Example: python3 scripts/fetch_screener.py TRENT
"""

import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.fundamentals import analyze_fundamentals


def main():
    if len(sys.argv) < 2:
        symbol = "TRENT"
        print(f"No symbol provided. Defaulting to {symbol}")
    else:
        symbol = sys.argv[1].upper()

    print(f"==================================================")
    print(f"      SCREENER.IN FUNDAMENTALS: {symbol}          ")
    print(f"==================================================")
    
    data = analyze_fundamentals(symbol)
    
    print(f"Company: {data.get('company_name')}")
    print(f"Fundamental Quality Score: {data.get('fundamental_score')}/100\n")
    
    print("--- KEY RATIOS ---")
    for k, v in data.get("ratios", {}).items():
        print(f"  {k:<20}: {v}")

    growth = data.get("growth_metrics", {})
    if growth:
        print("\n--- GROWTH METRICS ---")
        print(f"  Sales YoY Growth:  {growth.get('sales_yoy_growth_pct', 'N/A')}%")
        print(f"  Sales QoQ Growth:  {growth.get('sales_qoq_growth_pct', 'N/A')}%")
        print(f"  PAT YoY Growth:    {growth.get('pat_yoy_growth_pct', 'N/A')}%")
        print(f"  PAT QoQ Growth:    {growth.get('pat_qoq_growth_pct', 'N/A')}%")

    pros = data.get("pros", [])
    if pros:
        print("\n--- PROS ---")
        for p in pros:
            print(f"  ✓ {p}")

    cons = data.get("cons", [])
    if cons:
        print("\n--- CONS ---")
        for c in cons:
            print(f"  ⚠ {c}")

    qr = data.get("quarterly_results", {})
    quarters = qr.get("quarters", [])
    if quarters:
        print("\n--- RECENT QUARTERS (Sales & Profit) ---")
        print(f"  Quarters: {', '.join(quarters[-4:])}")
        sales = qr.get("sales", [])
        if sales:
            print(f"  Sales (₹ Cr): {', '.join(sales[-4:])}")
        net_p = qr.get("net_profit", [])
        if net_p:
            print(f"  Net Profit (₹ Cr): {', '.join(net_p[-4:])}")

    print("==================================================")


if __name__ == "__main__":
    main()
