#!/usr/bin/env python3
"""
CLI Script: Fetch real-time market news and announcements for an Indian stock.
Usage: python3 scripts/fetch_news.py <SYMBOL>
Example: python3 scripts/fetch_news.py TRENT
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.news_feed import fetch_stock_news


def main():
    if len(sys.argv) < 2:
        symbol = "TRENT"
        print(f"No symbol provided. Defaulting to {symbol}")
    else:
        symbol = sys.argv[1].upper()

    print(f"==================================================")
    print(f"       LATEST MATERIAL NEWS: {symbol}             ")
    print(f"==================================================")
    
    news = fetch_stock_news(symbol, limit=10)
    
    if not news:
        print(f"No recent news found for {symbol}.")
    else:
        for idx, item in enumerate(news, 1):
            print(f"\n{idx}. [{item.get('event_tag')}] {item.get('title')}")
            print(f"   Source: {item.get('source')} | Date: {item.get('published_at')}")
            print(f"   URL: {item.get('link')}")

    print("\n==================================================")


if __name__ == "__main__":
    main()
