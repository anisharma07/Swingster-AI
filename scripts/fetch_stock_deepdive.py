#!/usr/bin/env python3
"""
CLI Script: 360-degree Deep Dive Research & Thesis Card for an Indian Stock.
Combines Price Technicals, Relative Strength, Screener Fundamentals, NSE Filings,
Event Risk, and Trade Structure.
Usage: python3 scripts/fetch_stock_deepdive.py <SYMBOL>
Example: python3 scripts/fetch_stock_deepdive.py TRENT
"""

import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.technicals import analyze_technicals, fetch_historical_ohlcv
from modules.relative_strength import calculate_relative_strength, get_benchmark_data
from modules.fundamentals import analyze_fundamentals
from modules.corporate_events import fetch_corporate_events_and_risk
from modules.news_feed import fetch_stock_news
from modules.scoring import calculate_composite_score
from modules.universe import get_stock_sector


def get_complete_stock_profile(symbol: str) -> dict:
    """Aggregate complete 360-degree data for a single Indian stock."""
    clean_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
    sector = get_stock_sector(clean_symbol)
    
    # 1. Fetch OHLCV & Technicals
    stock_df = fetch_historical_ohlcv(clean_symbol, period="1y")
    tech_data = analyze_technicals(clean_symbol, stock_df)
    
    # 2. Relative Strength vs NIFTY 50
    nifty_df = get_benchmark_data("^NSEI", period="1y")
    rs_data = calculate_relative_strength(stock_df, nifty_df) if stock_df is not None else {}
    
    # 3. Screener Fundamentals
    fund_data = analyze_fundamentals(clean_symbol)
    
    # 4. Corporate Events & Results Risk
    events_data = fetch_corporate_events_and_risk(clean_symbol)
    
    # 5. News Feed
    news_items = fetch_stock_news(clean_symbol, company_name=fund_data.get("company_name", clean_symbol), limit=5)
    
    # 6. Composite Score
    tech_score = tech_data.get("technical_score", 50.0) if tech_data else 50.0
    rs_score = rs_data.get("rs_score", 50.0)
    fund_score = fund_data.get("fundamental_score", 50.0)
    vol_mult = tech_data.get("volume_multiplier", 1.0) if tech_data else 1.0
    event_risk_score = events_data.get("event_risk_score", 2.0)
    days_results = events_data.get("days_to_results", -1)

    scoring = calculate_composite_score(
        tech_score=tech_score,
        rs_score=rs_score,
        fundamental_score=fund_score,
        volume_multiplier=vol_mult,
        event_risk_score=event_risk_score,
        days_to_results=days_results
    )

    # 7. Bear Case / Invalidation Conditions
    invalidation_level = tech_data.get("trade_structure", {}).get("stop_loss", "Below 20 EMA") if tech_data else "Below 20 EMA"
    bear_case_points = []
    if days_results != -1 and days_results <= 7:
        bear_case_points.append(f"Upcoming quarterly earnings in {days_results} days creates high binary gap risk.")
    if tech_data and tech_data.get("rsi", 50) > 75:
        bear_case_points.append("RSI is overbought (>75), potential for mean reversion pullback.")
    if fund_data and fund_data.get("cons"):
        bear_case_points.append(f"Fundamental headwinds: {fund_data['cons'][0]}")
    bear_case_points.append(f"Technical thesis invalidates on a daily closing below ₹{invalidation_level}.")

    return {
        "symbol": clean_symbol,
        "company_name": fund_data.get("company_name", clean_symbol),
        "sector": sector,
        "composite_score": scoring.get("final_score"),
        "score_breakdown": scoring.get("breakdown"),
        "technicals": tech_data,
        "relative_strength": rs_data,
        "fundamentals": fund_data,
        "corporate_events": events_data,
        "news": news_items,
        "bear_case": bear_case_points
    }


def main():
    if len(sys.argv) < 2:
        symbol = "TRENT"
        print(f"No symbol provided. Defaulting to {symbol}")
    else:
        symbol = sys.argv[1].upper()

    print("=================================================================")
    print(f"       INDIAN EQUITIES SWING RESEARCH CARD: {symbol}            ")
    print("=================================================================")
    print(f"Aggregating live data from NSE, Screener.in & Technical scanner...")

    profile = get_complete_stock_profile(symbol)
    tech = profile.get("technicals", {})
    rs = profile.get("relative_strength", {})
    fund = profile.get("fundamentals", {})
    events = profile.get("corporate_events", {})
    score = profile.get("composite_score", 0)

    print(f"\n🏷 Company:  {profile.get('company_name')} ({profile.get('symbol')}) | Sector: {profile.get('sector')}")
    print(f"⭐ Composite Score: {score}/100")
    print(f"📈 Setup:    {tech.get('primary_setup') if tech else 'N/A'}")
    print(f"💰 Price:    ₹{tech.get('close', 'N/A')} ({tech.get('change_pct_1d', 0):+.2f}%)")
    
    print("\n--- 1. TECHNICAL SCAN ---")
    if tech:
        print(f"  20 EMA: ₹{tech.get('ema_20')} | 50 EMA: ₹{tech.get('ema_50')} | 200 EMA: ₹{tech.get('ema_200')}")
        print(f"  EMA Stack: {'Bullish (20>50>200)' if tech.get('is_ema_bullish_stack') else 'Mixed/Developing'}")
        print(f"  RSI (14): {tech.get('rsi')} | MACD Hist: {tech.get('macd_hist')} | 20d ROC: {tech.get('roc_20')}%")
        print(f"  Volume: {tech.get('volume_multiplier')}x of 20-Day SMA ({'Surge 🔥' if tech.get('volume_multiplier', 1) >= 2.0 else 'Normal'})")
        print(f"  52W High: ₹{tech.get('high_52w')} ({tech.get('pct_from_52w_high')}% from high)")
        print(f"  ATR: ₹{tech.get('atr')} ({tech.get('atr_pct')}% of price)")
    
    print("\n--- 2. RELATIVE STRENGTH VS NIFTY 50 ---")
    if rs:
        print(f"  20-Day Alpha: {rs.get('alpha_20d'):+.2f}% (Stock: {rs.get('stock_return_20d'):+.2f}% vs Nifty: {rs.get('nifty_return_20d'):+.2f}%)")
        print(f"  50-Day Alpha: {rs.get('alpha_50d'):+.2f}% | Mansfield RS: {rs.get('mansfield_rs'):+.2f}")
        print(f"  Outperforming Nifty: {'YES ✓' if rs.get('is_outperforming_nifty') else 'NO ✗'} | RS Rank: {rs.get('rs_percentile')}")

    print("\n--- 3. SCREENER.IN FUNDAMENTALS ---")
    ratios = fund.get("ratios", {})
    print(f"  P/E: {ratios.get('Stock P/E', 'N/A')} | ROCE: {ratios.get('ROCE', 'N/A')} | ROE: {ratios.get('ROE', 'N/A')} | Market Cap: {ratios.get('Market Cap', 'N/A')}")
    growth = fund.get("growth_metrics", {})
    if growth:
        print(f"  YoY Sales Growth: {growth.get('sales_yoy_growth_pct', 'N/A')}% | YoY PAT Growth: {growth.get('pat_yoy_growth_pct', 'N/A')}%")

    print("\n--- 4. NSE RESULTS CALENDAR & EVENT RISK ---")
    print(f"  Results Calendar: {events.get('next_results_date')} ({events.get('days_to_results_display')})")
    print(f"  Event Risk:       {events.get('event_risk_badge')} (Level: {events.get('event_risk_level')})")
    print(f"  Assessment:       {events.get('event_risk_description')}")

    print("\n--- 5. SWING TRADE STRUCTURE ---")
    trade = tech.get("trade_structure", {}) if tech else {}
    if trade:
        print(f"  Entry:        ₹{trade.get('entry')}")
        print(f"  Stop Loss:    ₹{trade.get('stop_loss')} ({trade.get('stop_loss_pct')}%)")
        print(f"  Target 1:     ₹{trade.get('target_1')} ({trade.get('target_1_pct')}%) [2R]")
        print(f"  Target 2:     ₹{trade.get('target_2')} ({trade.get('target_2_pct')}%) [3R]")
        print(f"  Risk/Reward:  {trade.get('risk_reward')}")

    print("\n--- 6. BEAR CASE & THESIS INVALIDATION ---")
    for b in profile.get("bear_case", []):
        print(f"  ⚠ {b}")

    print("\n--- 7. LATEST NEWS ---")
    for n in profile.get("news", [])[:3]:
        print(f"  • [{n.get('event_tag')}] {n.get('title')} ({n.get('source')})")

    print("=================================================================")


if __name__ == "__main__":
    main()
