# GEMINI.md — Swingster AI Trading Research Wiki Instructions

This document acts as persistent instructions and memory for Google Antigravity / Gemini when performing equity research, technical screening, swing trade checklists, and updating the Trading Research Wiki.

---

## 📌 Project Overview & Wiki Purpose

- **Platform**: Swingster AI Swing Trading Intelligence Platform (Indian Equities - NSE/BSE).
- **Wiki Location**: `wiki/`
- **Wiki Web UI**: High-performance local interactive reader running at `http://localhost:5111` (start via `./run_wiki.sh`).
- **Core Data Feeds**:
  - **Financials & Live Quotes**: Scraped exclusively via Screener.in.
  - **Technicals & Charts**: Screener Chart API + Technical Indicator Engine (20/50/200 DMA, RSI, Supertrend, ATR, BB, Volume Multipliers).
  - **News & Catalysts**: Real-time RSS feeds, corporate filings, quarterly earnings calendar.

---

## 📁 Wiki Directory Structure

```
wiki/
├── _index.md                                    # Main Trading Hub & Session Index
├── log.md                                       # Chronological Research & Screening Log
├── GEMINI.md                                    # This Guidelines Document
├── market-regimes/                              # Large vs Mid vs Small Cap Market Analysis
│   └── YYYY-MM-DD-market-regime.md
├── daily-reports/                               # 150-Stock Pre-Market Swing Screening Reports
│   └── YYYY-MM-DD-swing-report.md
└── checklists/                                  # Individual Stock 10-Point Trade Checklists & Scorecards
    └── YYYY-MM-DD-SYMBOL-checklist.md
```

---

## 📝 Frontmatter Standards

Every `.md` file created in `wiki/` must begin with YAML frontmatter:

```yaml
---
date: YYYY-MM-DD
title: "Descriptive Title (e.g., Daily Swing Report - 2026-08-15 | RELIANCE Trade Checklist)"
type: daily-report | checklist | market-regime | hub
tags: [swing-trading, breakout, nse, large-cap, mid-cap, small-cap]
quality: 5
confidence: high
stocks_screened: 150
top_picks_count: 10
market_regime: "Bullish Trend"
summary: "1-2 sentence core takeaway summarizing key setups and market conditions."
---
```

---

## 🏆 10-Point Institutional Trade Checklist Standard

When evaluating individual stock setups for `wiki/checklists/`, score each of the 10 criteria on a scale of 0 or 1 point (Total Score out of 10):

1. **Primary Trend Alignment (0-1 pt)**: Price trading comfortably above rising 50 DMA and 200 DMA.
2. **Chart Pattern & Base Quality (0-1 pt)**: Clean classical consolidation (Cup & Handle, Ascending Triangle, Flat Base, VCP, Bull Flag).
3. **Volume Signature (0-1 pt)**: Breakout volume $\ge 1.5\times$ to $2.5\times$ 20-day average volume with contraction during pullbacks.
4. **Risk-to-Reward Ratio (0-1 pt)**: Expected target to stop-loss ratio $\ge 1:1.8$ (preferably $\ge 1:2.0$).
5. **Market & Cap Size Tailwinds (0-1 pt)**: Stock's market cap segment (Large, Mid, or Small) demonstrating positive relative strength.
6. **Fundamental Quality (0-1 pt)**: Screener.in ROCE $> 15\%$, positive 3-year profit growth, manageable debt.
7. **Earnings & Binary Event Risk (0-1 pt)**: No quarterly earnings or major board announcements scheduled within the holding window (5-15 days).
8. **Catalyst & News Sentiment (0-1 pt)**: Positive sectoral tailwinds, order inflows, or expansion news without regulatory overhang.
9. **Support & Invalidation Level (0-1 pt)**: Well-defined technical invalidation point (Swing Low, 20 EMA, or breakout pivot).
10. **Liquidity & Spread (0-1 pt)**: High average daily turnover ($> ₹10\text{ Cr}$) with narrow bid-ask spread.

### Rating Tiers:
- **Grade A+ (Elite Setup)**: 9 - 10 Points $\rightarrow$ Full Allocation (100% position size).
- **Grade A (High Conviction)**: 7.5 - 8.5 Points $\rightarrow$ Standard Allocation (75% position size).
- **Grade B (Speculative / Secondary)**: 6.0 - 7.0 Points $\rightarrow$ Half Allocation (50% position size).
- **AVOID (Sub-optimal Risk)**: $< 6.0$ Points $\rightarrow$ Pass.

---

## 🔄 Research Protocol

1. **Pre-Market 150-Stock Screening**:
   - Fetch prices & fundamentals from Screener.in.
   - Run technical indicators & compute Market Cap comparisons (Small vs Mid vs Large).
   - Classify chart patterns and calculate target/SL.
   - Write the full report to `wiki/daily-reports/YYYY-MM-DD-swing-report.md`.
   - Update `wiki/market-regimes/YYYY-MM-DD-market-regime.md`.
2. **On-Demand Stock Checklist**:
   - When user provides specific stock symbols, evaluate all 10 criteria.
   - Generate detailed markdown scorecard in `wiki/checklists/YYYY-MM-DD-SYMBOL-checklist.md`.
   - Update `wiki/log.md` and `wiki/_index.md` index tables.
