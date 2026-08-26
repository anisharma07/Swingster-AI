"""
Screener.in Client module.
Scrapes and structures financial statements, valuation ratios, quarterly performance,
shareholding patterns, and pros/cons for Indian stocks directly from Screener.in.
"""

import re
import logging
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
from modules.universe import from_yf_symbol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class ScreenerClient:
    """Client for fetching comprehensive fundamental data from Screener.in for Indian stocks."""

    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.timeout = timeout

    def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company profile, ratios, quarterly results, shareholding, and pros/cons.
        """
        clean_symbol = from_yf_symbol(symbol)
        
        # Try consolidated first, fallback to standalone
        urls_to_try = [
            f"https://www.screener.in/company/{clean_symbol}/consolidated/",
            f"https://www.screener.in/company/{clean_symbol}/"
        ]
        
        soup = None
        for url in urls_to_try:
            try:
                resp = self.session.get(url, headers=HEADERS, timeout=self.timeout)
                if resp.status_code == 200 and "Company not found" not in resp.text:
                    soup = BeautifulSoup(resp.text, "lxml")
                    break
            except Exception as e:
                logger.warning(f"Screener request error for {url}: {e}")

        if not soup:
            logger.warning(f"Could not load Screener page for {clean_symbol}")
            return None

        profile: Dict[str, Any] = {
            "symbol": clean_symbol,
            "company_name": "",
            "about": "",
            "ratios": {},
            "pros": [],
            "cons": [],
            "quarterly_results": {},
            "shareholding": {},
            "growth_metrics": {}
        }

        # 1. Company Name & About
        h1 = soup.find("h1")
        if h1:
            profile["company_name"] = h1.text.strip()
        
        about_div = soup.find("div", class_="about")
        if about_div:
            # Clean up text
            p_tag = about_div.find("p")
            if p_tag:
                profile["about"] = p_tag.text.strip()

        # 2. Key Ratios (Top Ratios list)
        for li in soup.select("#top-ratios li"):
            name_elem = li.find("span", class_="name")
            val_elem = li.find("span", class_="nowrap") or li.find("span", class_="number")
            if name_elem and val_elem:
                clean_name = name_elem.text.strip()
                clean_val = val_elem.text.strip().replace("\n", "").replace("  ", " ")
                profile["ratios"][clean_name] = clean_val

        # 3. Pros and Cons
        pros_card = soup.find("div", class_="pros")
        if pros_card:
            profile["pros"] = [li.text.strip() for li in pros_card.find_all("li")]

        cons_card = soup.find("div", class_="cons")
        if cons_card:
            profile["cons"] = [li.text.strip() for li in cons_card.find_all("li")]

        # 4. Quarterly Results Table
        quarters_section = soup.find("section", id="quarters")
        if quarters_section:
            table = quarters_section.find("table", class_="data-table")
            if table:
                headers = [th.text.strip() for th in table.find_all("th") if th.text.strip()]
                rows_data = {}
                for tr in table.find_all("tr"):
                    tds = [td.text.strip() for td in tr.find_all("td")]
                    if len(tds) > 1:
                        metric_name = tds[0]
                        values = tds[1:]
                        rows_data[metric_name] = values

                profile["quarterly_results"] = {
                    "quarters": headers[1:] if len(headers) > 1 else [],
                    "sales": rows_data.get("Sales +", rows_data.get("Sales", [])),
                    "expenses": rows_data.get("Expenses +", rows_data.get("Expenses", [])),
                    "operating_profit": rows_data.get("Operating Profit", []),
                    "opm_percent": rows_data.get("OPM %", []),
                    "net_profit": rows_data.get("Net Profit +", rows_data.get("Net Profit", [])),
                    "eps": rows_data.get("EPS in Rs", rows_data.get("EPS", []))
                }

                # Calculate YoY & QoQ Growth if numbers available
                sales_list = profile["quarterly_results"]["sales"]
                profit_list = profile["quarterly_results"]["net_profit"]
                
                def parse_num(val_str: str) -> Optional[float]:
                    try:
                        clean = re.sub(r"[^\d.-]", "", val_str)
                        return float(clean) if clean else None
                    except Exception:
                        return None

                if len(sales_list) >= 5:
                    latest_sales = parse_num(sales_list[-1])
                    yoy_sales = parse_num(sales_list[-5])
                    prev_sales = parse_num(sales_list[-2])
                    if latest_sales and yoy_sales and yoy_sales > 0:
                        profile["growth_metrics"]["sales_yoy_growth_pct"] = round(((latest_sales - yoy_sales) / yoy_sales) * 100, 2)
                    if latest_sales and prev_sales and prev_sales > 0:
                        profile["growth_metrics"]["sales_qoq_growth_pct"] = round(((latest_sales - prev_sales) / prev_sales) * 100, 2)

                if len(profit_list) >= 5:
                    latest_pat = parse_num(profit_list[-1])
                    yoy_pat = parse_num(profit_list[-5])
                    prev_pat = parse_num(profit_list[-2])
                    if latest_pat and yoy_pat and yoy_pat > 0:
                        profile["growth_metrics"]["pat_yoy_growth_pct"] = round(((latest_pat - yoy_pat) / yoy_pat) * 100, 2)
                    if latest_pat and prev_pat and prev_pat > 0:
                        profile["growth_metrics"]["pat_qoq_growth_pct"] = round(((latest_pat - prev_pat) / prev_pat) * 100, 2)

        # 5. Shareholding Pattern
        sh_section = soup.find("section", id="shareholding")
        if sh_section:
            table = sh_section.find("table", class_="data-table")
            if table:
                headers = [th.text.strip() for th in table.find_all("th") if th.text.strip()]
                sh_data = {}
                for tr in table.find_all("tr"):
                    tds = [td.text.strip() for td in tr.find_all("td")]
                    if len(tds) > 1:
                        holder_type = tds[0].replace("+", "").strip()
                        values = tds[1:]
                        sh_data[holder_type] = values
                profile["shareholding"] = {
                    "periods": headers[1:] if len(headers) > 1 else [],
                    "patterns": sh_data
                }

        return profile


# Global singleton instance
screener_client = ScreenerClient()
