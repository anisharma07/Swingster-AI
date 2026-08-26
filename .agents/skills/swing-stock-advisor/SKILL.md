---
name: swing-stock-advisor
description: Institutional Swing Trading Decision & Wiki Research Skill for Indian Equities (NSE/BSE). Evaluates BUY, HOLD, SELL, TRIM, or AVOID decisions for any Indian stock using live price technicals, relative strength vs NIFTY 50, Screener.in fundamentals, NSE board meetings & results calendar, and publishes complete 10-point research scorecards into the Swingster Trading Wiki. Trigger whenever the user asks whether to buy, hold, or sell a stock, asks for swing trading research, evaluates trade setups, or wants to publish stock research dossiers to the wiki.
---

# 🇮🇳 Swing Stock Decision & Wiki Research Advisor

This skill empowers Antigravity to perform institutional-grade swing trade research for Indian Equities (NSE/BSE), calculate a 10-point scorecard, provide an unambiguous **BUY / HOLD / SELL / TRIM / AVOID** verdict, and publish the complete research dossier to the Swingster AI Wiki.

---

## 🎯 When to Trigger

Use this skill whenever:
- The user asks whether to **BUY, HOLD, SELL, TRIM, or AVOID** an Indian stock (e.g. *"Should I buy TRENT?"*, *"I am holding BEL at 290, should I hold or sell?"*, *"Analyze HAL for swing trade"*).
- The user asks for a **10-point checklist evaluation** or **stock scorecard**.
- The user asks to **publish or push stock research** to the Wiki server (`wiki/`).
- The user wants trade execution parameters (Entry, Stop Loss, Target 1 [2R], Target 2 [3R], and Risk:Reward).

---

## ⚙️ Workflow & Execution Protocol

### Step 1: Execute 360° Data Gathering & Decision Engine

Run the decision pipeline directly using the bundled Python CLI script:

```bash
# Case A: User evaluating a new trade (BUY / AVOID decision)
.venv/bin/python3 scripts/evaluate_stock_decision.py <SYMBOL> --push-wiki

# Case B: User already holding the stock (HOLD / TRIM / EXIT decision)
.venv/bin/python3 scripts/evaluate_stock_decision.py <SYMBOL> --holding --entry <ENTRY_PRICE> --push-wiki
```

*Example:*
```bash
.venv/bin/python3 scripts/evaluate_stock_decision.py TRENT --push-wiki
.venv/bin/python3 scripts/evaluate_stock_decision.py BEL --holding --entry 290.0 --push-wiki
```

The script automatically:
1. Fetches real-time price & daily OHLCV from NSE via Yahoo Finance (`modules/technicals.py`).
2. Calculates 20/50/200 EMAs, RSI-14, MACD, ATR, Volume Multiplier vs 20-Day SMA, and 52W High distance.
3. Computes Mansfield Relative Strength and 20d/50d Alpha vs NIFTY 50 (`modules/relative_strength.py`).
4. Scrapes Screener.in for P/E, ROCE, ROE, YoY/QoQ Sales & Profit growth, and Pros/Cons (`modules/screener_client.py`).
5. Pulls official NSE corporate filings, board meetings, upcoming results dates, and Event Risk (`modules/corporate_events.py`).
6. Fetches latest material catalysts from Google News RSS (`modules/news_feed.py`).
7. Checks overarching Indian Market Regime (`modules/market_regime.py`).
8. Generates the formatted markdown dossier in `wiki/checklists/YYYY-MM-DD-SYMBOL-checklist.md` and updates `wiki/_index.md` & `wiki/log.md`.

---

## 📊 10-Point Institutional Checklist Standard

| # | Criterion | Benchmark for 1.0 Point |
| :- | :--- | :--- |
| **1** | **Primary Trend Alignment** | Bullish EMA stack ($Close > 20 > 50 > 200\text{ EMA}$) or price $> 20\text{ EMA} > 50\text{ EMA}$. |
| **2** | **Relative Strength vs NIFTY** | Positive 20-day alpha $> +2.0\%$ vs NIFTY 50 (Top 10% or Top 5% RS cohort). |
| **3** | **Chart Setup & Base Geometry** | 52-Week High Breakout, 20-Day Range Breakout, or 20 EMA Pullback support. |
| **4** | **Volume Signature & Accumulation** | Breakout volume $\ge 1.4\times$ to $2.0\times$ 20-day SMA volume. |
| **5** | **Risk-to-Reward Ratio ($R:R$)** | Target 1 (2R) to Stop Loss ratio $\ge 1:1.8$ (ideally $1:2.0+$) with stop $\le 5\%$. |
| **6** | **Fundamental Quality (Screener.in)** | ROCE $> 15\%$, ROE $> 15\%$, positive YoY revenue/profit growth, healthy balance sheet. |
| **7** | **Earnings & Binary Event Risk** | No quarterly results or major board meeting in next 14+ days ($> 2\text{ weeks}$ clear runway). |
| **8** | **Catalysts & Material News** | Order wins, capacity expansion, sector tailwinds, no adverse SEBI/regulatory probe. |
| **9** | **Technical Invalidation Integrity** | Clean structural stop-loss below 20 EMA / swing low; RSI not severely overbought ($< 78$). |
| **10** | **Macro Market Regime Alignment** | Indian market in 🟢 Bullish Regime (NIFTY $> 20/50\text{ EMA}$, India VIX $< 18$). |

---

## 🎯 Decision Matrix & Verdict Rules

### 1. New Trade Decisions:
- **BUY ON BREAKOUT** (Score $\ge 8.0/10$ | Grade A+ / A): Entering blue-sky or range breakout with strong volume and $>14$ days to results.
- **ACCUMULATE ON DIP** (Score $\ge 7.0/10$ | Grade A / B): Pullback to rising 20 EMA / 50 EMA in strong uptrend.
- **SPECULATIVE WATCH** (Score $6.0 - 6.9/10$): Constructive setup, but wait for volume breakout confirmation above resistance.
- **AVOID / PASS** (Score $< 6.0/10$): Poor relative strength, broken moving averages, unfavorable R:R, or high earnings gap hazard ($<7$ days).

### 2. Existing Holding Decisions:
- **HOLD / TRAIL STOP**: Price holding above rising 20 EMA, RS strong, trail stop to recent swing low / 20 EMA.
- **TAKE PROFIT / TRIM**: Target 1 reached or RSI $> 78$; trim 50% position and raise stop-loss to entry price.
- **EXIT / STOP OUT**: Daily close below 20 EMA / stop-loss, or quarterly results scheduled in $\le 3$ days.

---

## 📝 Presenting the Result to the User

Always present a clean, executive summary in chat:

```markdown
### 🎯 Decision Verdict: [BUY / ACCUMULATE / HOLD / TRIM / EXIT / AVOID]
**Stock**: COMPANY NAME (`SYMBOL`) | **Sector**: Sector Name  
**Scorecard**: **`X.X / 10.0`** — **[Grade A+ / Grade A / Grade B / AVOID]**  
**Position Sizing**: Full / Standard (75%) / Half (50%) / Pass  

---

### 📊 Trade Execution Parameters:
- **Current Price**: ₹XXX.XX (`+X.XX%` today)
- **Recommended Entry**: ₹XXX.XX
- **Stop Loss**: ₹XXX.XX (`-X.X%` risk)
- **Target 1 (2R)**: ₹XXX.XX (`+X.X%`)
- **Target 2 (3R)**: ₹XXX.XX (`+X.X%`)
- **Risk:Reward**: `1 : X.X`
- **Next Quarterly Results**: DD-Mon-YYYY (`X days away`) — 🟢 Low Risk / ⚠ High Risk

---

### 🔍 Key Strengths & Watchouts:
- **Technicals & RS**: 20D Alpha vs NIFTY: `+X.X%` | Volume: `X.Xx` 20-SMA | Setup: `Setup Name`
- **Fundamentals ([Screener.in](https://www.screener.in/company/SYMBOL/))**: P/E: `XX.X` | ROCE: `XX%` | Sales Growth: `+XX%`
- **Invalidation Level**: Daily close below ₹XXX.XX.

---
📄 **Published to Wiki**: [`wiki/checklists/YYYY-MM-DD-SYMBOL-checklist.md`](file:///Users/anirudhsharma/Desktop/new%20folder/PORTFOLIO%20ENHANCEMENT/Swing/wiki/checklists/YYYY-MM-DD-SYMBOL-checklist.md)  
🌐 **Interactive Wiki Reader**: [http://localhost:5111](http://localhost:5111)
```
