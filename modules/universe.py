"""
Universe module for Indian Equities.
Contains curated lists of liquid universe stocks:
- NIFTY 50 (Large Caps)
- NIFTY 100 (Large & Midcaps)
- NIFTY Midcap 100 (High-Growth Midcaps)
- NIFTY Smallcap 100 / Momentum Smallcaps (High-Beta / High-Alpha Smallcaps)
- NIFTY 500 Curated Liquid Universe
- Sector / Thematic Baskets (Defense & Rail, IT & Tech, Banking & NBFC, Auto & EV, Pharma)
"""

from typing import List, Dict

# Major Sector Indices and their Yahoo Finance tickers
SECTORS: Dict[str, str] = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY INFRA": "^CNXINFRA",
    "INDIA VIX": "^INDIAVIX",
}

# 1. NIFTY 50 (Large Caps)
NIFTY_50: List[str] = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "LICI",
    "LT", "KOTAKBANK", "HCLTECH", "AXISBANK", "ASIANPAINT",
    "MARUTI", "SUNPHARMA", "TITAN", "BAJFINANCE", "TATAMOTORS",
    "ULTRACEMCO", "NTPC", "ONGC", "JSWSTEEL", "POWERGRID",
    "TATASTEEL", "M&M", "ADANIENT", "COALINDIA", "BAJAJFINSV",
    "ADANIPORTS", "HINDALCO", "GRASIM", "TECHM", "NESTLEIND",
    "WIPRO", "CIPLA", "SBILIFE", "DRREDDY", "BRITANNIA",
    "EICHERMOT", "TATACONSUM", "APOLLOHOSP", "HEROMOTOCO", "BAJAJ-AUTO",
    "DIVISLAB", "HDFCLIFE", "BPCL", "TRENT", "BEL"
]

# 2. Top Swing & Momentum 30 (Curated High RS Leaders)
TOP_SWING_WATCHLIST: List[str] = [
    "TRENT", "BEL", "HAL", "BSE", "DIXON", "SIEMENS", "ABB", "POLYCAB",
    "KALYANKJIL", "SOLARINDS", "PERSISTENT", "COFORGE", "MAXHEALTH",
    "MOTHERSON", "VEDL", "INDHOTEL", "CHOLAFIN", "CDSL", "MAZDOCK",
    "TVSMOTOR", "CUMMINSIND", "VOLTAS", "FEDERALBNK", "AUBANK",
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL"
]

# 3. NIFTY Midcap 100 Leaders
NIFTY_MIDCAP_100: List[str] = [
    "TRENT", "BEL", "HAL", "DIXON", "SIEMENS", "ABB", "POLYCAB",
    "PERSISTENT", "COFORGE", "CUMMINSIND", "VOLTAS", "SOLARINDS",
    "MAXHEALTH", "FEDERALBNK", "AUBANK", "INDHOTEL", "TVSMOTOR",
    "MOTHERSON", "CHOLAFIN", "VEDL", "JINDALSTEL", "AMBUJACEM",
    "HAVELLS", "PIDILITIND", "BOSCHLTD", "SHREECEM", "NAUKRI",
    "IRCTC", "LUPIN", "AUROPHARMA", "ZYDUSLIFE", "TORNTPHARM",
    "PRESTIGE", "OBEROIRLTY", "JSWENERGY", "DLF", "IOC", "BANKBARODA",
    "PNB", "CANBK", "INDIGO", "GAIL", "SRF", "COLPAL", "KALYANKJIL"
]

# 4. NIFTY Smallcap 100 / High-Beta Momentum Small Caps
NIFTY_SMALLCAP_100: List[str] = [
    "BSE", "CDSL", "MCX", "KALYANKJIL", "ANGELONE", "CAMS", "KFINTECH",
    "MAZDOCK", "COCHINSHIP", "GRSE", "RVNL", "IREDA", "SUZLON",
    "TITAGARH", "RAILTEL", "TEJASNET", "KAYNES", "CYIENT", "SONACOMS",
    "APARINDS", "JYOTICNC", "ANANDRATHI", "MOTILALOFS", "MANAPPURAM",
    "IIFL", "PPLPHARMA", "NATCOPHARM", "JBCHEPHARM", "GRINDWELL",
    "ECLERX", "BLS", "CASTROLIND", "WELCORP", "NCC", "RADICO",
    "CENTURYPLY", "HUDCO", "NBCC", "BEML", "BDL", "KPITTECH",
    "TATAELXSI", "EXIDEIND", "AMBER", "GLENMARK", "CENTRALBK",
    "IOB", "UCOBANK", "KARURVYSYA", "RBLBANK"
]

# 5. NIFTY 100 (Large & Midcaps)
NIFTY_100: List[str] = list(dict.fromkeys(NIFTY_50 + NIFTY_MIDCAP_100))

# 6. NIFTY 500 Curated Liquid Universe
NIFTY_500: List[str] = list(dict.fromkeys(NIFTY_50 + NIFTY_MIDCAP_100 + NIFTY_SMALLCAP_100))

# 7. Sector / Thematic Baskets
THEMATIC_DEFENSE_RAIL: List[str] = [
    "HAL", "BEL", "MAZDOCK", "COCHINSHIP", "GRSE", "SOLARINDS",
    "RVNL", "RAILTEL", "TITAGARH", "BEML", "BDL", "SIEMENS", "ABB"
]

THEMATIC_IT_TECH: List[str] = [
    "TCS", "INFY", "HCLTECH", "TECHM", "WIPRO", "PERSISTENT",
    "COFORGE", "LTIM", "KPITTECH", "TATAELXSI", "CYIENT", "NAUKRI", "KAYNES"
]

THEMATIC_BANK_FINANCE: List[str] = [
    "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "BANKBARODA",
    "FEDERALBNK", "AUBANK", "BAJFINANCE", "BAJAJFINSV", "CHOLAFIN",
    "BSE", "CDSL", "MCX", "ANGELONE", "CAMS", "KFINTECH", "MOTILALOFS"
]

# Universes map
UNIVERSES: Dict[str, List[str]] = {
    "swing_top30": TOP_SWING_WATCHLIST,
    "nifty_smallcap": NIFTY_SMALLCAP_100,
    "nifty_midcap": NIFTY_MIDCAP_100,
    "nifty50": NIFTY_50,
    "nifty100": NIFTY_100,
    "nifty500": NIFTY_500,
    "theme_defense": THEMATIC_DEFENSE_RAIL,
    "theme_it": THEMATIC_IT_TECH,
    "theme_fin": THEMATIC_BANK_FINANCE,
}

# Sector classification for key stocks
STOCK_SECTORS: Dict[str, str] = {
    "TCS": "IT", "INFY": "IT", "HCLTECH": "IT", "TECHM": "IT", "WIPRO": "IT", "LTIM": "IT", "PERSISTENT": "IT", "COFORGE": "IT", "NAUKRI": "IT", "KPITTECH": "IT", "TATAELXSI": "IT", "CYIENT": "IT", "ECLERX": "IT",
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "SBIN": "Banking", "KOTAKBANK": "Banking", "AXISBANK": "Banking", "BANKBARODA": "Banking", "PNB": "Banking", "FEDERALBNK": "Banking", "AUBANK": "Banking", "CANBK": "Banking", "KARURVYSYA": "Banking", "RBLBANK": "Banking",
    "BAJFINANCE": "Financials", "BAJAJFINSV": "Financials", "CHOLAFIN": "Financials", "BSE": "Financials", "CDSL": "Financials", "MCX": "Financials", "ANGELONE": "Financials", "CAMS": "Financials", "KFINTECH": "Financials", "MOTILALOFS": "Financials", "ANANDRATHI": "Financials", "MANAPPURAM": "Financials", "IIFL": "Financials", "LICI": "Financials", "SBILIFE": "Financials", "HDFCLIFE": "Financials",
    "MARUTI": "Auto", "TATAMOTORS": "Auto", "M&M": "Auto", "EICHERMOT": "Auto", "HEROMOTOCO": "Auto", "BAJAJ-AUTO": "Auto", "TVSMOTOR": "Auto", "MOTHERSON": "Auto", "BOSCHLTD": "Auto", "SONACOMS": "Auto", "EXIDEIND": "Auto",
    "SUNPHARMA": "Pharma", "CIPLA": "Pharma", "DRREDDY": "Pharma", "DIVISLAB": "Pharma", "APOLLOHOSP": "Pharma", "TORNTPHARM": "Pharma", "ZYDUSLIFE": "Pharma", "MAXHEALTH": "Pharma", "LUPIN": "Pharma", "AUROPHARMA": "Pharma", "PPLPHARMA": "Pharma", "NATCOPHARM": "Pharma", "JBCHEPHARM": "Pharma", "GLENMARK": "Pharma",
    "TATASTEEL": "Metal", "JSWSTEEL": "Metal", "HINDALCO": "Metal", "COALINDIA": "Metal", "VEDL": "Metal", "JINDALSTEL": "Metal",
    "RELIANCE": "Energy", "ONGC": "Energy", "NTPC": "Energy", "POWERGRID": "Energy", "BPCL": "Energy", "IOC": "Energy", "GAIL": "Energy", "JSWENERGY": "Energy", "SUZLON": "Energy", "IREDA": "Energy",
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "TATACONSUM": "FMCG", "COLPAL": "FMCG", "RADICO": "FMCG",
    "TRENT": "Retail/Consumer", "TITAN": "Retail/Consumer", "KALYANKJIL": "Retail/Consumer", "AMBER": "Consumer Durables", "VOLTAS": "Consumer Durables", "HAVELLS": "Consumer Durables",
    "BEL": "Defense/CapGoods", "HAL": "Defense/CapGoods", "MAZDOCK": "Defense/CapGoods", "COCHINSHIP": "Defense/CapGoods", "GRSE": "Defense/CapGoods", "BDL": "Defense/CapGoods", "BEML": "Defense/CapGoods", "SIEMENS": "Defense/CapGoods", "ABB": "Defense/CapGoods", "POLYCAB": "Defense/CapGoods", "DIXON": "Defense/CapGoods", "CUMMINSIND": "Defense/CapGoods", "SOLARINDS": "Defense/CapGoods", "APARINDS": "Defense/CapGoods", "KAYNES": "Defense/CapGoods", "JYOTICNC": "Defense/CapGoods",
    "RVNL": "Railways/Infra", "TITAGARH": "Railways/Infra", "RAILTEL": "Railways/Infra", "HUDCO": "Infra/Housing", "NBCC": "Infra/Construction", "NCC": "Infra/Construction",
    "LT": "Infrastructure", "ADANIENT": "Infrastructure", "ADANIPORTS": "Infrastructure", "ULTRACEMCO": "Infrastructure", "GRASIM": "Infrastructure", "AMBUJACEM": "Infrastructure", "SHREECEM": "Infrastructure", "DLF": "Infrastructure", "PRESTIGE": "Infrastructure", "OBEROIRLTY": "Infrastructure"
}


def to_yf_symbol(symbol: str) -> str:
    """Convert standard NSE symbol to Yahoo Finance ticker (.NS suffix)."""
    clean_sym = symbol.strip().upper()
    if clean_sym.startswith("^") or clean_sym.endswith(".NS") or clean_sym.endswith(".BO"):
        return clean_sym
    return f"{clean_sym}.NS"


def from_yf_symbol(ticker: str) -> str:
    """Convert Yahoo Finance ticker to clean NSE symbol."""
    sym = ticker.upper()
    if sym.endswith(".NS"):
        return sym[:-3]
    if sym.endswith(".BO"):
        return sym[:-3]
    return sym


def get_universe(name: str = "swing_top30") -> List[str]:
    """Retrieve list of stock symbols for a given universe name."""
    clean_name = name.lower().replace(" ", "_").replace("-", "_")
    return UNIVERSES.get(clean_name, TOP_SWING_WATCHLIST)


def get_stock_sector(symbol: str) -> str:
    """Get the primary sector for a stock symbol."""
    clean_sym = from_yf_symbol(symbol)
    return STOCK_SECTORS.get(clean_sym, "Diversified")
