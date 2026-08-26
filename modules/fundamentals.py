"""
Fundamental Analysis and Quality Scoring Engine for Indian Equities.
Uses Screener.in client to evaluate business health, profitability, quarterly growth,
and calculate a rule-based Fundamental Quality Score (0 to 100).
"""

import re
import logging
from typing import Dict, Any, Optional
from modules.universe import from_yf_symbol
from modules.screener_client import screener_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_numeric(val: Any) -> Optional[float]:
    """Helper to extract clean float from strings like '₹ 1,58,797 Cr.', '18.5 %', etc."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        clean = re.sub(r"[^\d.-]", "", str(val))
        return float(clean) if clean else None
    except Exception:
        return None


def analyze_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Fetch and analyze fundamental metrics for an Indian stock from Screener.in.
    Returns structured ratios, quarterly growth, shareholding, and a 0-100 Quality Score.
    """
    clean_symbol = from_yf_symbol(symbol)
    profile = screener_client.get_company_profile(clean_symbol)
    
    if not profile:
        return {
            "symbol": clean_symbol,
            "company_name": clean_symbol,
            "about": "Fundamental data unavailable",
            "ratios": {},
            "pros": [],
            "cons": [],
            "quarterly_results": {},
            "shareholding": {},
            "growth_metrics": {},
            "fundamental_score": 50.0,
            "summary": "Data unavailable"
        }

    ratios = profile.get("ratios", {})
    growth = profile.get("growth_metrics", {})
    
    # Parse key ratios
    pe_ratio = parse_numeric(ratios.get("Stock P/E"))
    roce = parse_numeric(ratios.get("ROCE"))
    roe = parse_numeric(ratios.get("ROE"))
    market_cap_str = ratios.get("Market Cap", "")
    div_yield = parse_numeric(ratios.get("Dividend Yield"))
    
    sales_yoy = growth.get("sales_yoy_growth_pct", 0.0)
    pat_yoy = growth.get("pat_yoy_growth_pct", 0.0)

    # Calculate Fundamental Quality Score (0 to 100)
    fund_score = 40.0  # Base neutral score

    # 1. ROCE & ROE (max 25 pts)
    if roce is not None:
        if roce >= 20.0:
            fund_score += 15
        elif roce >= 12.0:
            fund_score += 10
        elif roce < 5.0:
            fund_score -= 5

    if roe is not None:
        if roe >= 18.0:
            fund_score += 10
        elif roe >= 12.0:
            fund_score += 6

    # 2. Growth metrics (max 30 pts)
    if sales_yoy > 20.0:
        fund_score += 15
    elif sales_yoy > 10.0:
        fund_score += 10
    elif sales_yoy < 0:
        fund_score -= 5

    if pat_yoy > 20.0:
        fund_score += 15
    elif pat_yoy > 10.0:
        fund_score += 10
    elif pat_yoy < 0:
        fund_score -= 5

    # 3. Screener Pros vs Cons balance (max 15 pts)
    pros_cnt = len(profile.get("pros", []))
    cons_cnt = len(profile.get("cons", []))
    if pros_cnt > cons_cnt:
        fund_score += 10
    elif cons_cnt > pros_cnt + 2:
        fund_score -= 5

    fund_score = min(100.0, max(0.0, fund_score))

    return {
        "symbol": clean_symbol,
        "company_name": profile.get("company_name", clean_symbol),
        "about": profile.get("about", ""),
        "ratios": ratios,
        "key_metrics": {
            "pe_ratio": pe_ratio,
            "roce": roce,
            "roe": roe,
            "market_cap": market_cap_str,
            "dividend_yield": div_yield,
            "sales_yoy_growth_pct": sales_yoy,
            "pat_yoy_growth_pct": pat_yoy
        },
        "pros": profile.get("pros", []),
        "cons": profile.get("cons", []),
        "quarterly_results": profile.get("quarterly_results", {}),
        "shareholding": profile.get("shareholding", {}),
        "growth_metrics": growth,
        "fundamental_score": round(fund_score, 1)
    }
