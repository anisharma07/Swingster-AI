"""
Corporate Events, Results Calendar, and Event Risk Module for Indian Equities.
Tracks upcoming Quarterly Results dates, Board meetings from NSE, and computes
an Event Risk Score to protect swing trades against earnings gap risk.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import yfinance as yf
from modules.universe import to_yf_symbol, from_yf_symbol
from modules.nse_client import nse_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> Optional[date]:
    """Parse various date formats from NSE or Yahoo Finance."""
    if not date_str:
        return None
    # Try multiple formats
    formats = [
        "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y",
        "%d-%b-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except Exception:
            continue
    return None


def fetch_corporate_events_and_risk(symbol: str) -> Dict[str, Any]:
    """
    Fetch upcoming board meetings, earnings dates, and corporate actions from NSE and Yahoo Finance.
    Computes an Event Risk Score (1-10) and Days to Results.
    """
    clean_symbol = from_yf_symbol(symbol)
    today = date.today()

    # 1. Fetch Board Meetings from NSE
    nse_meetings = nse_client.get_board_meetings(clean_symbol)
    
    # 2. Fetch Corporate Actions from NSE
    nse_actions = nse_client.get_corporate_actions(clean_symbol)

    # 3. Check for Earnings / Results Date
    next_results_date_str = None
    next_results_purpose = None
    days_to_results = None

    for meeting in nse_meetings:
        m_date_str = meeting.get("meeting_date")
        purpose = meeting.get("purpose", "")
        m_date = parse_date(m_date_str)
        
        if m_date and m_date >= today:
            if "financial result" in purpose.lower() or "accounts" in purpose.lower() or "dividend" in purpose.lower() or not next_results_date_str:
                next_results_date_str = m_date_str
                next_results_purpose = purpose
                days_to_results = (m_date - today).days
                break

    # Fallback to Yahoo Finance earnings calendar if NSE board meeting not scheduled yet
    if days_to_results is None:
        try:
            yf_ticker = yf.Ticker(to_yf_symbol(clean_symbol))
            cal = yf_ticker.calendar
            if cal is not None and not (isinstance(cal, dict) and len(cal) == 0):
                # Check for Earnings Date
                earnings_val = None
                if isinstance(cal, dict):
                    earnings_val = cal.get("Earnings Date") or cal.get("Earnings High")
                elif hasattr(cal, "get"):
                    earnings_val = cal.get("Earnings Date")
                
                if earnings_val:
                    if isinstance(earnings_val, (list, tuple)) and len(earnings_val) > 0:
                        e_date = earnings_val[0]
                    else:
                        e_date = earnings_val
                    
                    if hasattr(e_date, "date"):
                        e_date = e_date.date()
                    elif isinstance(e_date, str):
                        e_date = parse_date(e_date)
                    
                    if isinstance(e_date, date) and e_date >= today:
                        days_to_results = (e_date - today).days
                        next_results_date_str = e_date.strftime("%d-%b-%Y")
                        next_results_purpose = "Financial Results (Estimated)"
        except Exception as e:
            logger.debug(f"YF Calendar lookup exception for {clean_symbol}: {e}")

    # Compute Event Risk Level and Score (1 to 10)
    # Higher score = HIGHER RISK (worse for entering swing trades)
    if days_to_results is not None:
        if days_to_results <= 3:
            event_risk_level = "VERY HIGH"
            event_risk_score = 9.5
            risk_badge = "🚨 Results in 1-3 Days"
            risk_desc = "Earnings announcement imminent. High probability of volatile gap opening."
        elif days_to_results <= 7:
            event_risk_level = "HIGH"
            event_risk_score = 8.0
            risk_badge = "⚠ Results in < 7 Days"
            risk_desc = "Results within 1 week. Caution: swing holding might get caught in earnings gap."
        elif days_to_results <= 14:
            event_risk_level = "MEDIUM"
            event_risk_score = 5.0
            risk_badge = "⚡ Results in 1-2 Weeks"
            risk_desc = "Sufficient time for quick swing, but plan to exit or tighten stops before result."
        elif days_to_results <= 30:
            event_risk_level = "LOW"
            event_risk_score = 2.5
            risk_badge = "🟢 Results ~1 Month Away"
            risk_desc = "Good runway for swing setup to play out without earnings disruption."
        else:
            event_risk_level = "VERY LOW"
            event_risk_score = 1.0
            risk_badge = f"🟢 Results in {days_to_results} Days"
            risk_desc = "Ample clear runway for swing trade."
    else:
        # Default when no imminent board meeting announced
        event_risk_level = "LOW"
        event_risk_score = 2.0
        days_to_results_label = "Not Announced"
        risk_badge = "🟢 No Immediate Board Meeting"
        risk_desc = "No immediate results meeting scheduled by company on NSE."

    return {
        "symbol": clean_symbol,
        "next_results_date": next_results_date_str or "Not Scheduled",
        "next_results_purpose": next_results_purpose or "N/A",
        "days_to_results": days_to_results if days_to_results is not None else -1,
        "days_to_results_display": f"{days_to_results} days" if days_to_results is not None else "Not Scheduled",
        "event_risk_level": event_risk_level,
        "event_risk_score": event_risk_score,
        "event_risk_badge": risk_badge,
        "event_risk_description": risk_desc,
        "upcoming_board_meetings": nse_meetings[:5],
        "corporate_actions": nse_actions[:5]
    }
