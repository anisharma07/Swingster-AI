#!/usr/bin/env python3
"""
CLI Script: Fetch upcoming results dates, board meetings, and corporate actions from NSE.
Usage: python3 scripts/fetch_events.py <SYMBOL>
Example: python3 scripts/fetch_events.py TRENT
"""

import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.corporate_events import fetch_corporate_events_and_risk
from modules.nse_client import nse_client


def main():
    if len(sys.argv) < 2:
        symbol = "TRENT"
        print(f"No symbol provided. Defaulting to {symbol}")
    else:
        symbol = sys.argv[1].upper()

    print(f"==================================================")
    print(f"     NSE CORPORATE EVENTS & CALENDAR: {symbol}    ")
    print(f"==================================================")
    
    events = fetch_corporate_events_and_risk(symbol)
    
    print(f"Event Risk Status:  {events.get('event_risk_badge')}")
    print(f"Risk Level:         {events.get('event_risk_level')} ({events.get('event_risk_score')}/10)")
    print(f"Assessment:         {events.get('event_risk_description')}")
    print(f"Next Results Date:  {events.get('next_results_date')} ({events.get('days_to_results_display')})")
    print(f"Purpose:            {events.get('next_results_purpose')}\n")

    meetings = events.get("upcoming_board_meetings", [])
    if meetings:
        print("--- RECENT & UPCOMING BOARD MEETINGS ---")
        for m in meetings:
            print(f"  📅 {m.get('meeting_date')}: {m.get('purpose')} - {m.get('details')}")
    else:
        print("No recent board meetings found on NSE.")

    actions = events.get("corporate_actions", [])
    if actions:
        print("\n--- CORPORATE ACTIONS (Dividends, Splits, Bonus) ---")
        for a in actions:
            print(f"  💰 Ex-Date: {a.get('ex_date')} | Purpose: {a.get('purpose')}")

    # Also fetch recent official announcements
    announcements = nse_client.get_announcements(symbol, limit=5)
    if announcements:
        print("\n--- LATEST NSE OFFICIAL FILINGS & ANNOUNCEMENTS ---")
        for ann in announcements:
            print(f"  📄 [{ann.get('date')}] {ann.get('subject')} ({ann.get('category')})")

    print("==================================================")


if __name__ == "__main__":
    main()
