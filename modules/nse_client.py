"""
NSE India Client module.
Handles session management, cookies, and fetches official corporate announcements,
board meetings (results dates), corporate actions (dividends/splits), and shareholding patterns.
"""

import time
import logging
from typing import Dict, List, Any, Optional
import requests
from modules.universe import from_yf_symbol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

API_HEADERS = {
    "User-Agent": DEFAULT_HEADERS["User-Agent"],
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
}


class NSEClient:
    """Client for fetching structured corporate data from NSE India."""

    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.timeout = timeout
        self._last_cookie_refresh = 0.0
        self._refresh_cookies()

    def _refresh_cookies(self, force: bool = False) -> None:
        """Establish or refresh session cookies by visiting NSE home page."""
        now = time.time()
        # Refresh every 5 minutes or on demand
        if force or (now - self._last_cookie_refresh > 300) or len(self.session.cookies) == 0:
            try:
                self.session.cookies.clear()
                resp = self.session.get(
                    "https://www.nseindia.com",
                    headers=DEFAULT_HEADERS,
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    self._last_cookie_refresh = now
                    logger.info("NSE session cookies initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to refresh NSE cookies: {e}")

    def _get_api(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Perform authenticated GET request with auto-retry and cookie renewal."""
        for attempt in range(2):
            try:
                self._refresh_cookies()
                resp = self.session.get(
                    url,
                    headers=API_HEADERS,
                    params=params,
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (401, 403):
                    logger.warning(f"NSE returned {resp.status_code}, refreshing cookies and retrying...")
                    self._refresh_cookies(force=True)
                    time.sleep(0.5)
                else:
                    logger.warning(f"NSE API error {resp.status_code} for {url}")
            except Exception as e:
                logger.warning(f"NSE request failed: {e}")
                time.sleep(0.5)
        return None

    def get_announcements(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch corporate announcements for a symbol.
        Returns list of announcements with date, description, attachment, and category.
        """
        clean_symbol = from_yf_symbol(symbol)
        url = "https://www.nseindia.com/api/corporate-announcements"
        params = {
            "index": "equities",
            "symbol": clean_symbol
        }
        data = self._get_api(url, params=params)
        announcements = []
        if isinstance(data, list):
            for item in data[:limit]:
                announcements.append({
                    "date": item.get("an_dt") or item.get("sort_date"),
                    "subject": item.get("desc", "").strip(),
                    "category": item.get("attchmntText", "").strip(),
                    "broadcast_time": item.get("bcast_dt"),
                    "attachment_url": item.get("attachment")
                })
        return announcements

    def get_board_meetings(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch upcoming and recent board meetings (crucial for Earnings Results dates).
        """
        clean_symbol = from_yf_symbol(symbol)
        url = "https://www.nseindia.com/api/corporate-board-meetings"
        params = {
            "index": "equities",
            "symbol": clean_symbol
        }
        data = self._get_api(url, params=params)
        meetings = []
        if isinstance(data, list):
            for item in data:
                meetings.append({
                    "meeting_date": item.get("bm_date"),
                    "purpose": item.get("bm_purpose", "").strip(),
                    "details": item.get("bm_desc", "").strip()
                })
        return meetings

    def get_corporate_actions(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch corporate actions (dividends, splits, bonuses, rights issues).
        """
        clean_symbol = from_yf_symbol(symbol)
        url = "https://www.nseindia.com/api/corporates-corporateActions"
        params = {
            "index": "equities",
            "symbol": clean_symbol
        }
        data = self._get_api(url, params=params)
        actions = []
        if isinstance(data, list):
            for item in data:
                actions.append({
                    "ex_date": item.get("exDate"),
                    "record_date": item.get("recordDate"),
                    "purpose": item.get("subject", "").strip(),
                    "series": item.get("series", "").strip()
                })
        return actions

    def get_shareholding_pattern(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch latest shareholding pattern from NSE.
        """
        clean_symbol = from_yf_symbol(symbol)
        url = "https://www.nseindia.com/api/corporate-share-holding-equities"
        params = {"symbol": clean_symbol}
        data = self._get_api(url, params=params)
        if isinstance(data, dict):
            return data
        elif isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time official NSE equity quote and price info.
        """
        clean_symbol = from_yf_symbol(symbol)
        url = f"https://www.nseindia.com/api/quote-equity?symbol={clean_symbol}"
        data = self._get_api(url)
        if isinstance(data, dict):
            price_info = data.get("priceInfo", {})
            security_info = data.get("securityInfo", {})
            return {
                "symbol": clean_symbol,
                "company_name": data.get("info", {}).get("companyName"),
                "industry": data.get("industryInfo", {}).get("macro"),
                "last_price": price_info.get("lastPrice"),
                "change": price_info.get("change"),
                "pChange": price_info.get("pChange"),
                "open": price_info.get("open"),
                "day_high": price_info.get("intraDayHighLow", {}).get("max"),
                "day_low": price_info.get("intraDayHighLow", {}).get("min"),
                "previous_close": price_info.get("previousClose"),
                "vwap": price_info.get("vwap"),
                "week_52_high": price_info.get("weekHighLow", {}).get("max"),
                "week_52_low": price_info.get("weekHighLow", {}).get("min"),
            }
        return None


# Global singleton instance for easy import
nse_client = NSEClient()
