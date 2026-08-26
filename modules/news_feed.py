"""
News Feed and Corporate Announcements Aggregator for Indian Equities.
Fetches real-time market news from Google News RSS feeds and financial portals
for specific Indian tickers (e.g. TRENT, BEL, RELIANCE, TCS).
"""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import quote
from typing import Dict, List, Any
import requests
from modules.universe import from_yf_symbol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/xml,text/xml,*/*;q=0.9",
}


def tag_news_event(title: str) -> str:
    """Classify the likely nature of a news event for quick scanning."""
    lower_t = title.lower()
    if any(k in lower_t for k in ["order", "contract", "bagged", "awarded", "deal", "secures"]):
        return "📦 Order / Contract"
    if any(k in lower_t for k in ["q1", "q2", "q3", "q4", "results", "profit", "revenue", "loss", "earnings", "pat"]):
        return "📊 Financial Results"
    if any(k in lower_t for k in ["dividend", "bonus", "split", "buyback"]):
        return "💰 Corporate Action"
    if any(k in lower_t for k in ["acquire", "acquisition", "merger", "stake", "jv", "joint venture"]):
        return "🤝 M&A / Partnership"
    if any(k in lower_t for k in ["target", "brokerage", "upgrade", "downgrade", "buy", "rating"]):
        return "🎯 Brokerage / Target"
    if any(k in lower_t for k in ["sebi", "rbi", "penalty", "notice", "tax", "court", "probe"]):
        return "⚠ Regulatory / Legal"
    return "📰 Corporate News"


def fetch_stock_news(symbol: str, company_name: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch the latest material news articles for an Indian stock ticker.
    """
    clean_symbol = from_yf_symbol(symbol)
    
    # Construct targeted search query for Indian market
    search_terms = f"{clean_symbol} NSE OR \"{clean_symbol}\" share"
    if company_name and company_name != clean_symbol:
        search_terms = f"\"{company_name}\" OR {clean_symbol} NSE"

    encoded_query = quote(search_terms)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

    news_items: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall("./channel/item")
            for item in items[:limit]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_elem = item.find("pubDate")
                source_elem = item.find("source")

                raw_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                # Google News titles usually end with ' - Source Name'
                source_name = source_elem.text.strip() if source_elem is not None and source_elem.text else "Financial Media"
                if " - " in raw_title and source_elem is None:
                    parts = raw_title.rsplit(" - ", 1)
                    clean_title = parts[0]
                    source_name = parts[1]
                else:
                    clean_title = raw_title

                news_items.append({
                    "title": clean_title,
                    "source": source_name,
                    "published_at": pub_elem.text.strip() if pub_elem is not None and pub_elem.text else "",
                    "link": link_elem.text.strip() if link_elem is not None and link_elem.text else "#",
                    "event_tag": tag_news_event(clean_title)
                })
    except Exception as e:
        logger.warning(f"Error fetching news for {clean_symbol}: {e}")

    return news_items
