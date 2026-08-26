# 🚀 Swingster AI — Indian Equities Swing Trading Dashboard & Research Engine

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Swingster AI** is an institutional-grade swing trading decision and market research platform tailored for Indian equities (NSE/BSE). It aggregates real-time technicals, relative strength against NIFTY 50, multi-quarter fundamentals, NSE corporate actions & board meeting calendars, and market regime analysis into high-conviction swing trade scorecards.

---

## 🌟 Key Features

- **📊 10-Point Swing Scorecard**: Deterministic 0–10 scoring engine weighing technical trends, volume breakouts, relative strength (RS), valuation, earnings momentum, and corporate catalysts.
- **⚡ Market Regime Analysis**: Live tracking of benchmark indices (NIFTY 50, NIFTY Next 50, Midcap 100, Smallcap 100, India VIX, Advance/Decline ratio) to determine market posture (**AGGRESSIVE RISK-ON**, **SELECTIVE LONG**, **NEUTRAL / DEFENSIVE**, **CAPITAL PRESERVATION**).
- **📈 Relative Strength (Mansfield RS)**: Benchmarks stock price performance directly against NIFTY 50 across 1-month, 3-month, and 6-month horizons.
- **🏢 Deep Fundamental Insights**: Financial statement analysis, PE vs Industry PE, ROCE/ROE, quarterly sales & profit CAGR, and shareholding pattern tracking.
- **📅 NSE Events & Catalysts**: Real-time tracking of upcoming earnings dates, board meetings, dividends, bonus/splits, and AGMs.
- **📚 Interactive Trading Wiki**: Built-in markdown-based wiki documenting checklists, trade playbooks, sector deep-dives, and decision logs.

---

## 🛠️ Project Structure

```text
├── app.py                      # Main Flask application & REST API server
├── run_app.sh                  # Startup script with automated port management
├── requirements.txt            # Python dependencies
├── modules/                    # Core analytical modules
│   ├── market_regime.py        # Benchmark indices, regime detection, VIX analysis
│   ├── nse_client.py           # NSE India live quote & corporate events client
│   ├── screener_client.py      # Fundamental data scraper & parser
│   ├── relative_strength.py    # RS calculations vs NIFTY 50
│   ├── technicals.py           # EMA (20/50/200), RSI, ATR, Support/Resistance
│   ├── scoring.py              # 10-point scoring algorithm & trade decision engine
│   ├── corporate_events.py     # Results calendar & corporate action filters
│   ├── fundamentals.py         # Financial ratios & growth score metrics
│   ├── news_feed.py            # Live market news aggregation
│   └── universe.py             # Nifty 500 / Midcap stock universe definitions
├── scripts/                    # Standalone CLI tools for analysis & scanning
│   ├── evaluate_stock_decision.py  # Run single stock deepdive scorecard from CLI
│   ├── scan_universe.py            # Scan watchlist for swing setups
│   ├── fetch_market_regime.py      # Print market regime report
│   ├── fetch_events.py             # Fetch upcoming corporate events
│   ├── fetch_screener.py           # Test fundamental extraction
│   └── fetch_news.py               # Test news aggregation
├── static/                     # Frontend assets (CSS, JS, UI components)
├── templates/                  # HTML templates (Dashboard UI)
└── wiki/                       # Research wiki, logs, checklists & playbooks
```

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/anisharma07/Swingster-AI.git
cd Swingster-AI
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch the Application

```bash
chmod +x run_app.sh
./run_app.sh
```

Open [http://localhost:5001](http://localhost:5001) in your browser.

---

## 📡 API Endpoints

- `GET /api/market-regime` — Returns current market posture, index breadths, and VIX status.
- `GET /api/stock/<symbol>` — Generates a full 10-point evaluation and decision for a stock symbol (e.g. `TATAMOTORS`, `RELIANCE`, `TCS`).
- `GET /api/universe` — Returns available stock symbols and sectors in the tracking universe.
- `GET /api/events` — Upcoming board meetings, earnings dates, and dividend declarations.

---

## 📄 License

MIT License. Designed for swing traders and investors.
