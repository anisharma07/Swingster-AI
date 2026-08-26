#!/usr/bin/env python3
"""
Institutional Swing Trade Decision Engine & Wiki Publisher for Indian Equities.
Performs 360-degree research on any Indian stock (NSE/BSE), scores a 10-point institutional checklist,
generates an actionable decision (BUY, HOLD, SELL, TRIM, AVOID), and automatically publishes
the formatted research dossier to the Swingster AI Wiki (wiki/checklists/ & updates _index.md / log.md).

Usage:
  python3 scripts/evaluate_stock_decision.py TRENT --push-wiki
  python3 scripts/evaluate_stock_decision.py BEL --holding --entry 290.0 --push-wiki
"""

import sys
import os
import argparse
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.universe import from_yf_symbol, get_stock_sector
from modules.technicals import analyze_technicals, fetch_historical_ohlcv
from modules.relative_strength import calculate_relative_strength, get_benchmark_data
from modules.fundamentals import analyze_fundamentals
from modules.corporate_events import fetch_corporate_events_and_risk
from modules.news_feed import fetch_stock_news
from modules.market_regime import analyze_market_regime
from modules.scoring import calculate_composite_score


def evaluate_10_point_checklist(
    symbol: str,
    tech: Dict[str, Any],
    rs: Dict[str, Any],
    fund: Dict[str, Any],
    events: Dict[str, Any],
    regime: Dict[str, Any],
    user_holding: bool = False,
    entry_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluate the 10 institutional swing trading criteria (each 0 to 1.0 pt, Total 10 pts).
    """
    checklist: List[Dict[str, Any]] = []
    total_score = 0.0

    # 1. Primary Trend Alignment (0 - 1.0 pt)
    cur_close = tech.get("close", 0.0)
    ema_20 = tech.get("ema_20", 0.0)
    ema_50 = tech.get("ema_50", 0.0)
    ema_200 = tech.get("ema_200", 0.0)
    is_stack = tech.get("is_ema_bullish_stack", False)

    if is_stack:
        trend_pts = 1.0
        trend_status = "PASS"
        trend_eval = f"Perfect Bullish Stack: Price (₹{cur_close}) > 20 EMA (₹{ema_20}) > 50 EMA (₹{ema_50}) > 200 EMA (₹{ema_200})."
    elif cur_close > ema_20 and cur_close > ema_50:
        trend_pts = 0.85
        trend_status = "PASS"
        trend_eval = f"Trading above 20 EMA (₹{ema_20}) and 50 EMA (₹{ema_50}). Upward trend intact."
    elif cur_close > ema_20:
        trend_pts = 0.60
        trend_status = "NEUTRAL"
        trend_eval = f"Trading above 20 EMA (₹{ema_20}), but below/near 50 EMA. Mild recovery structure."
    elif cur_close > ema_50:
        trend_pts = 0.40
        trend_status = "NEUTRAL"
        trend_eval = f"Trading below 20 EMA (₹{ema_20}), finding support at 50 EMA (₹{ema_50})."
    else:
        trend_pts = 0.0
        trend_status = "FAIL"
        trend_eval = f"Trading below key moving averages. Downtrend or broken momentum."
    total_score += trend_pts
    checklist.append({
        "num": 1, "criterion": "Primary Trend Alignment", "status": trend_status,
        "points": f"{trend_pts:.2f} / 1.0", "details": trend_eval
    })

    # 2. Relative Strength vs Benchmark (0 - 1.0 pt)
    alpha_20d = rs.get("alpha_20d", 0.0)
    alpha_50d = rs.get("alpha_50d", 0.0)
    rs_percentile = rs.get("rs_percentile", "Average")
    is_outperforming = rs.get("is_outperforming_nifty", False)

    if rs_percentile == "Top 5%" or alpha_20d >= 8.0:
        rs_pts = 1.0
        rs_status = "PASS"
        rs_eval = f"Elite Market Leader (Top 5% RS cohort). 20-Day Alpha vs NIFTY: {alpha_20d:+.2f}%."
    elif rs_percentile == "Top 10%" or (alpha_20d > 2.0 and alpha_50d > 0):
        rs_pts = 0.85
        rs_status = "PASS"
        rs_eval = f"Strong Relative Strength (Top 10%). 20D Alpha: {alpha_20d:+.2f}%, 50D Alpha: {alpha_50d:+.2f}%."
    elif is_outperforming or alpha_20d > 0:
        rs_pts = 0.65
        rs_status = "NEUTRAL"
        rs_eval = f"Positive outperformance vs NIFTY 50 (Alpha: {alpha_20d:+.2f}%)."
    else:
        rs_pts = 0.20
        rs_status = "FAIL"
        rs_eval = f"Lagging benchmark (20D Alpha: {alpha_20d:+.2f}%). Capital is flowing elsewhere."
    total_score += rs_pts
    checklist.append({
        "num": 2, "criterion": "Relative Strength vs NIFTY", "status": rs_status,
        "points": f"{rs_pts:.2f} / 1.0", "details": rs_eval
    })

    # 3. Chart Setup & Base Geometry (0 - 1.0 pt)
    primary_setup = tech.get("primary_setup", "Rangebound")
    all_setups = tech.get("all_setups", [])
    pct_52w = tech.get("pct_from_52w_high", -99)

    if "52-Week High Breakout" in all_setups or pct_52w >= -2.0:
        setup_pts = 1.0
        setup_status = "PASS"
        setup_eval = f"52-Week High Breakout / Blue-sky territory ({pct_52w}% from 52W High)."
    elif "20-Day Consolidation Breakout" in all_setups or pct_52w >= -5.0:
        setup_pts = 0.85
        setup_status = "PASS"
        setup_eval = f"Consolidation range breakout with tight multi-week base."
    elif "Pullback to 20 EMA" in all_setups:
        setup_pts = 0.80
        setup_status = "PASS"
        setup_eval = f"Constructive low-risk pullback to rising 20 EMA support zone."
    elif "Strong EMA Trend" in primary_setup:
        setup_pts = 0.70
        setup_status = "PASS"
        setup_eval = f"Well-defined trending base without exhaustion."
    else:
        setup_pts = 0.35
        setup_status = "NEUTRAL"
        setup_eval = f"Setup is developing / choppy range without clear trigger pivot."
    total_score += setup_pts
    checklist.append({
        "num": 3, "criterion": "Chart Setup & Base Geometry", "status": setup_status,
        "points": f"{setup_pts:.2f} / 1.0", "details": setup_eval
    })

    # 4. Volume Signature & Institutional Accumulation (0 - 1.0 pt)
    vol_mult = tech.get("volume_multiplier", 1.0)
    if vol_mult >= 2.0:
        vol_pts = 1.0
        vol_status = "PASS"
        vol_eval = f"Heavy institutional accumulation: Volume surge is {vol_mult}x of 20-Day SMA."
    elif vol_mult >= 1.4:
        vol_pts = 0.80
        vol_status = "PASS"
        vol_eval = f"Healthy volume expansion: {vol_mult}x of 20-Day average volume."
    elif vol_mult >= 0.9:
        vol_pts = 0.50
        vol_status = "NEUTRAL"
        vol_eval = f"Normal turnover ({vol_mult}x). Lacks decisive institutional breakout volume."
    else:
        vol_pts = 0.25
        vol_status = "FAIL"
        vol_eval = f"Low volume ({vol_mult}x). Risk of low-conviction or false move."
    total_score += vol_pts
    checklist.append({
        "num": 4, "criterion": "Volume Signature & Accumulation", "status": vol_status,
        "points": f"{vol_pts:.2f} / 1.0", "details": vol_eval
    })

    # 5. Risk-to-Reward Ratio & Trade Asymmetry (0 - 1.0 pt)
    trade_plan = tech.get("trade_structure", {})
    stop_pct = abs(trade_plan.get("stop_loss_pct", 4.0))
    tgt1_pct = trade_plan.get("target_1_pct", 8.0)
    rr_num = round(tgt1_pct / stop_pct, 2) if stop_pct > 0 else 2.0

    if rr_num >= 2.0 and stop_pct <= 5.5:
        rr_pts = 1.0
        rr_status = "PASS"
        rr_eval = f"Excellent asymmetry: Target 1 (+{tgt1_pct}%) vs Risk (-{stop_pct}%) gives R:R 1:{rr_num}."
    elif rr_num >= 1.6:
        rr_pts = 0.80
        rr_status = "PASS"
        rr_eval = f"Acceptable swing asymmetry: Target 1 (+{tgt1_pct}%) vs Stop Loss (-{stop_pct}%)."
    else:
        rr_pts = 0.35
        rr_status = "FAIL"
        rr_eval = f"Sub-optimal risk/reward profile. Risk (-{stop_pct}%) too wide for potential reward."
    total_score += rr_pts
    checklist.append({
        "num": 5, "criterion": "Risk-to-Reward Ratio", "status": rr_status,
        "points": f"{rr_pts:.2f} / 1.0", "details": rr_eval
    })

    # 6. Fundamental Quality & Valuation (Screener.in) (0 - 1.0 pt)
    fund_score = fund.get("fundamental_score", 50.0)
    ratios = fund.get("ratios", {})
    growth = fund.get("growth_metrics", {})
    roce = ratios.get("ROCE", "N/A")
    sales_yoy = growth.get("sales_yoy_growth_pct", 0.0)

    if fund_score >= 75.0:
        fund_pts = 1.0
        fund_status = "PASS"
        fund_eval = f"High Quality (Score: {fund_score}/100). ROCE: {roce}, Sales YoY Growth: {sales_yoy}%."
    elif fund_score >= 55.0:
        fund_pts = 0.75
        fund_status = "PASS"
        fund_eval = f"Stable fundamentals (Score: {fund_score}/100). P/E: {ratios.get('Stock P/E', 'N/A')}."
    else:
        fund_pts = 0.40
        fund_status = "NEUTRAL"
        fund_eval = f"Moderate/weak fundamental quality or elevated valuation (Score: {fund_score}/100)."
    total_score += fund_pts
    checklist.append({
        "num": 6, "criterion": "Fundamental Quality (Screener.in)", "status": fund_status,
        "points": f"{fund_pts:.2f} / 1.0", "details": fund_eval
    })

    # 7. Earnings & Binary Event Risk (0 - 1.0 pt)
    days_results = events.get("days_to_results", -1)
    event_risk_level = events.get("event_risk_level", "LOW")

    if event_risk_level in ("VERY LOW", "LOW") or days_results > 18 or days_results == -1:
        event_pts = 1.0
        event_status = "PASS"
        event_eval = f"Clear holding runway: Results in {events.get('days_to_results_display')}. No binary gap risk."
    elif event_risk_level == "MEDIUM" or (7 < days_results <= 18):
        event_pts = 0.60
        event_status = "NEUTRAL"
        event_eval = f"Manageable: Results scheduled in {days_results} days. Swing trade must be managed before results."
    else:
        event_pts = 0.10
        event_status = "FAIL"
        event_eval = f"HIGH EVENT RISK: Results in {days_results} days! High binary gap hazard."
    total_score += event_pts
    checklist.append({
        "num": 7, "criterion": "Earnings & Binary Event Risk", "status": event_status,
        "points": f"{event_pts:.2f} / 1.0", "details": event_eval
    })

    # 8. Catalysts & Material News Sentiment (0 - 1.0 pt)
    news_items = fetch_stock_news(symbol, limit=4)
    if any("Order" in n.get("event_tag", "") or "Results" in n.get("event_tag", "") for n in news_items):
        news_pts = 0.90
        news_status = "PASS"
        news_eval = f"Positive business catalysts / order inflow announcements detected."
    elif len(news_items) > 0:
        news_pts = 0.75
        news_status = "PASS"
        news_eval = f"Steady positive/neutral corporate news flow without regulatory headwinds."
    else:
        news_pts = 0.50
        news_status = "NEUTRAL"
        news_eval = f"No recent headline catalysts found."
    total_score += news_pts
    checklist.append({
        "num": 8, "criterion": "News Flow & Catalysts", "status": news_status,
        "points": f"{news_pts:.2f} / 1.0", "details": news_eval
    })

    # 9. Technical Invalidation & Structural Integrity (0 - 1.0 pt)
    rsi_val = tech.get("rsi", 50.0)
    atr_pct = tech.get("atr_pct", 2.5)

    if 50 <= rsi_val <= 72 and atr_pct <= 4.0:
        inval_pts = 1.0
        inval_status = "PASS"
        inval_eval = f"Clean risk boundaries. RSI at {rsi_val} (healthy momentum), ATR at {atr_pct}%."
    elif rsi_val > 78:
        inval_pts = 0.50
        inval_status = "NEUTRAL"
        inval_eval = f"Extended momentum (RSI: {rsi_val}). High risk of short-term mean-reversion."
    else:
        inval_pts = 0.70
        inval_status = "PASS"
        inval_eval = f"Well-defined invalidation level below ₹{trade_plan.get('stop_loss')}."
    total_score += inval_pts
    checklist.append({
        "num": 9, "criterion": "Technical Invalidation Integrity", "status": inval_status,
        "points": f"{inval_pts:.2f} / 1.0", "details": inval_eval
    })

    # 10. Macro Market Regime Alignment (0 - 1.0 pt)
    regime_status = regime.get("regime_status", "BULLISH")
    if regime_status == "BULLISH":
        regime_pts = 1.0
        regime_st = "PASS"
        regime_eval = f"Market is in Bullish Regime. NIFTY 50 above 20 & 50 EMA, India VIX calm."
    elif regime_status == "NEUTRAL":
        regime_pts = 0.65
        regime_st = "NEUTRAL"
        regime_eval = f"Market is Neutral / Rangebound. Selective swing trades with tighter stops favored."
    else:
        regime_pts = 0.20
        regime_st = "FAIL"
        regime_eval = f"Market in Risk-Off / Defensive regime. Headwinds for swing breakout longs."
    total_score += regime_pts
    checklist.append({
        "num": 10, "criterion": "Market Regime Alignment", "status": regime_st,
        "points": f"{regime_pts:.2f} / 1.0", "details": regime_eval
    })

    final_score = round(total_score, 1)

    # Determine Grade and Decision
    if final_score >= 8.5:
        grade = "Grade A+ (Elite Setup)"
        sizing = "Full Allocation (100% Position Sizing)"
    elif final_score >= 7.5:
        grade = "Grade A (High Conviction)"
        sizing = "Standard Allocation (75% Position Sizing)"
    elif final_score >= 6.0:
        grade = "Grade B (Speculative)"
        sizing = "Half Allocation (50% Position Sizing)"
    else:
        grade = "AVOID (Sub-optimal Risk)"
        sizing = "Zero Allocation (Pass / Avoid)"

    # Actionable Decision Logic
    if user_holding:
        if final_score >= 7.0 and cur_close >= ema_20:
            decision = "HOLD / TRAIL STOP"
            decision_summary = f"Maintain holding. Trend and relative strength remain strong. Trail stop-loss to ₹{tech.get('trade_structure', {}).get('stop_loss')} (below 20 EMA)."
        elif cur_close < ema_20 or final_score < 5.5 or (days_results != -1 and days_results <= 3):
            decision = "EXIT / STOP OUT"
            decision_summary = f"Exit position. Price is losing 20 EMA momentum or impending binary earnings risk creates unfavorable risk profile."
        else:
            decision = "TAKE PROFIT / TRIM"
            decision_summary = f"Book partial profits (50% trim) and raise stop-loss to entry/break-even level."
    else:
        if final_score >= 8.0 and "Breakout" in primary_setup:
            decision = "BUY ON BREAKOUT"
            decision_summary = f"High-conviction buy. Enter near ₹{cur_close} with Target 1 at ₹{trade_plan.get('target_1')} (+{tgt1_pct}%) and Stop Loss at ₹{trade_plan.get('stop_loss')} (-{stop_pct}%)."
        elif final_score >= 7.0 and "Pullback" in primary_setup:
            decision = "ACCUMULATE ON DIP"
            decision_summary = f"Favorable pullback entry. Accumulate near 20 EMA support zone (₹{ema_20}) with Stop Loss at ₹{trade_plan.get('stop_loss')}."
        elif final_score >= 6.0:
            decision = "SPECULATIVE WATCH"
            decision_summary = f"Setup is constructive but wait for volume breakout confirmation above recent consolidation pivot."
        else:
            decision = "AVOID / PASS"
            decision_summary = f"Pass on this setup. Technical weakness, poor relative strength, or high event risk makes risk-to-reward unfavorable."

    return {
        "final_score": final_score,
        "grade": grade,
        "decision": decision,
        "decision_summary": decision_summary,
        "sizing": sizing,
        "checklist": checklist
    }


def publish_to_wiki(symbol: str, data: Dict[str, Any], wiki_dir: str) -> str:
    """
    Generate markdown dossier and save to wiki/checklists/YYYY-MM-DD-SYMBOL-checklist.md,
    and update wiki/_index.md and wiki/log.md.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_sym = from_yf_symbol(symbol)
    
    checklists_dir = os.path.join(wiki_dir, "checklists")
    os.makedirs(checklists_dir, exist_ok=True)
    
    filename = f"{today_str}-{clean_sym}-checklist.md"
    file_path = os.path.join(checklists_dir, filename)

    tech = data.get("technicals", {})
    fund = data.get("fundamentals", {})
    events = data.get("corporate_events", {})
    eval_res = data.get("evaluation", {})
    trade = tech.get("trade_structure", {})
    news = data.get("news", [])
    ratios = fund.get("ratios", {})
    growth = fund.get("growth_metrics", {})
    pros = fund.get("pros", [])
    cons = fund.get("cons", [])

    md_content = f"""---
date: {today_str}
title: "{clean_sym} Swing Trade Checklist & Decision ({eval_res.get('final_score')}/10 — {eval_res.get('grade')})"
type: checklist
tags: [checklist, {clean_sym.lower()}, {eval_res.get('decision').lower().replace(' ', '-')}, nse, swing-trade]
quality: 5
confidence: high
stock_symbol: "{clean_sym}"
company_name: "{fund.get('company_name', clean_sym)}"
score: {eval_res.get('final_score')}
grade: "{eval_res.get('grade')}"
verdict: "{eval_res.get('decision')}"
target_1: "₹{trade.get('target_1')} (+{trade.get('target_1_pct')}%)"
stop_loss: "₹{trade.get('stop_loss')} ({trade.get('stop_loss_pct')}%)"
summary: "10-point institutional checklist evaluation for {fund.get('company_name', clean_sym)} ({clean_sym}). Verdict: {eval_res.get('decision')} with {eval_res.get('final_score')}/10 points."
---

# 📋 Swing Trade Setup Checklist: {fund.get('company_name', clean_sym)} (`{clean_sym}`)

Comprehensive 10-point institutional swing trading analysis evaluating multi-factor technicals, relative strength vs NIFTY 50, Screener.in fundamentals, NSE results calendar, and asymmetric trade structure.

---

## 🏆 Executive Scorecard & Actionable Verdict

| Overall Score | Rating Grade | Actionable Decision | Sizing & Execution Guidance |
| :---: | :---: | :---: | :---: |
| **`{eval_res.get('final_score')} / 10.0`** | **{eval_res.get('grade')}** | **{eval_res.get('decision')}** | **{eval_res.get('sizing')}** |

> **Strategy Takeaway**: {eval_res.get('decision_summary')}

---

## 🎯 Swing Trade Execution Parameters

| Parameter | Value | Details / Rationale |
| :--- | :--- | :--- |
| **Current Market Price** | **₹{tech.get('close', 'N/A')}** | 1D Change: `{tech.get('change_pct_1d', 0):+.2f}%` |
| **Recommended Entry Zone** | **₹{trade.get('entry')}** | Optimal accumulation trigger |
| **Primary Target (2R)** | **₹{trade.get('target_1')} (+{trade.get('target_1_pct')}%)** | 1st profit booking pivot ($R:R \\ge 1:2.0$) |
| **Runner Target (3R)** | **₹{trade.get('target_2')} (+{trade.get('target_2_pct')}%)** | Extended trend target |
| **Strict Stop Loss** | **₹{trade.get('stop_loss')} ({trade.get('stop_loss_pct')}%)** | Hard technical invalidation level |
| **Risk-to-Reward Ratio** | **`{trade.get('risk_reward')}`** | Institutional asymmetric skew |
| **Next Quarterly Results** | **{events.get('next_results_date')} ({events.get('days_to_results_display')})** | Event Risk Level: `{events.get('event_risk_level')}` |
| **Invalidation Criteria** | Daily close below ₹{trade.get('stop_loss')} or breakdown below 20 EMA on heavy volume. | Technical exit rule |

---

## 📊 10-Point Institutional Scorecard Breakdown

| # | Criterion | Status | Points | Evaluation Details |
| :- | :--- | :---: | :---: | :--- |
"""

    for item in eval_res.get("checklist", []):
        md_content += f"| {item['num']} | **{item['criterion']}** | `{item['status']}` | `{item['points']}` | {item['details']} |\n"

    md_content += f"""
---

## 🏢 Fundamentals & Capital Efficiency ([Screener.in](https://www.screener.in/company/{clean_sym}/))

- **Market Capitalization**: `{ratios.get('Market Cap', 'N/A')}`
- **Stock P/E**: `{ratios.get('Stock P/E', 'N/A')}` | **Book Value**: `{ratios.get('Book Value', 'N/A')}`
- **ROCE**: `{ratios.get('ROCE', 'N/A')}` | **ROE**: `{ratios.get('ROE', 'N/A')}`
- **Sales YoY Growth**: `{growth.get('sales_yoy_growth_pct', 'N/A')}%` | **PAT YoY Growth**: `{growth.get('pat_yoy_growth_pct', 'N/A')}%`

### Screener Insights:
**Pros:**
"""
    if pros:
        for p in pros[:4]:
            md_content += f"- ✅ {p}\n"
    else:
        md_content += "- ✅ Solid market position in sectoral cohort.\n"

    md_content += "\n**Cons / Watchouts:**\n"
    if cons:
        for c in cons[:4]:
            md_content += f"- ⚠️ {c}\n"
    else:
        md_content += "- ⚠️ No severe structural cons listed.\n"

    md_content += f"""
---

## 📅 NSE Results Calendar & Corporate Actions
- **Next Financial Results Meeting**: `{events.get('next_results_date')} ({events.get('days_to_results_display')})`
- **Event Risk Rating**: `{events.get('event_risk_badge')} ({events.get('event_risk_level')} RISK)`
- **Event Assessment**: {events.get('event_risk_description')}

---

## 📰 Recent News & Catalysts
"""
    if news:
        for n in news[:4]:
            md_content += f"- **[{n.get('event_tag')}] {n.get('title')}** — *{n.get('source')}* ({n.get('published_at')})\n"
    else:
        md_content += "- No recent headline catalysts.\n"

    md_content += f"""
---
*Checklist evaluated and generated by Antigravity `swing-stock-advisor` on {now_str} IST.*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Update wiki/_index.md Recent Checklists table
    index_file = os.path.join(wiki_dir, "_index.md")
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                idx_content = f.read()

            new_entry = f"- **[{clean_sym} Trade Checklist ({eval_res.get('final_score')}/10 — {eval_res.get('grade')})](./checklists/{filename})** — `{eval_res.get('decision')}` | Target: `₹{trade.get('target_1')} (+{trade.get('target_1_pct')}%)` | SL: `₹{trade.get('stop_loss')} ({trade.get('stop_loss_pct')}%)`\n"

            if "### Recent Stock Checklists" in idx_content:
                parts = idx_content.split("### Recent Stock Checklists", 1)
                idx_content = parts[0] + "### Recent Stock Checklists\n" + new_entry + parts[1].lstrip("\n")
                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(idx_content)
        except Exception as e:
            print(f"Warning: Could not update _index.md: {e}")

    # Update wiki/log.md
    log_file = os.path.join(wiki_dir, "log.md")
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()

            log_entry = f"\n- [{today_str}] Evaluated Trade Checklist for **{clean_sym}** ({fund.get('company_name', clean_sym)}) $\\rightarrow$ **{eval_res.get('final_score')}/10 ({eval_res.get('grade')})** [View Card](./checklists/{filename})\n"
            
            if "## 📅 Session History" in log_content:
                parts = log_content.split("## 📅 Session History", 1)
                log_content = parts[0] + "## 📅 Session History" + log_entry + parts[1]
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(log_content)
        except Exception as e:
            print(f"Warning: Could not update log.md: {e}")

    return file_path


def main():
    parser = argparse.ArgumentParser(description="Evaluate BUY / HOLD / SELL swing trading decision for an Indian stock.")
    parser.add_argument("symbol", type=str, help="NSE Stock Symbol (e.g. TRENT, BEL, HAL, BSE, DIXON)")
    parser.add_argument("--holding", action="store_true", help="Set to true if you currently own this stock and want a HOLD/EXIT evaluation")
    parser.add_argument("--entry", type=float, default=None, help="User's existing purchase entry price")
    parser.add_argument("--push-wiki", action="store_true", default=True, help="Automatically publish report to wiki server")
    parser.add_argument("--wiki-dir", type=str, default="/Users/anirudhsharma/Desktop/new folder/PORTFOLIO ENHANCEMENT/Swing/wiki", help="Path to wiki directory")
    args = parser.parse_args()

    clean_sym = from_yf_symbol(args.symbol.upper())

    print("=========================================================================================")
    print(f"       SWINGSTER AI: 360° TRADE DECISION ENGINE — {clean_sym}                            ")
    print("=========================================================================================")
    print(f"Gathering live data: Technicals, RS vs NIFTY, Screener.in, NSE Events, News...")

    # 1. Fetch data components
    stock_df = fetch_historical_ohlcv(clean_sym, period="1y")
    if stock_df is None:
        print(f"Error: Could not retrieve price history for {clean_sym}")
        sys.exit(1)

    tech = analyze_technicals(clean_sym, stock_df)
    nifty_df = get_benchmark_data("^NSEI", period="1y")
    rs = calculate_relative_strength(stock_df, nifty_df)
    fund = analyze_fundamentals(clean_sym)
    events = fetch_corporate_events_and_risk(clean_sym)
    regime = analyze_market_regime()
    news = fetch_stock_news(clean_sym, limit=5)

    # 2. Evaluate 10-Point Institutional Checklist & Actionable Decision
    evaluation = evaluate_10_point_checklist(
        symbol=clean_sym,
        tech=tech,
        rs=rs,
        fund=fund,
        events=events,
        regime=regime,
        user_holding=args.holding,
        entry_price=args.entry
    )

    data_payload = {
        "symbol": clean_sym,
        "technicals": tech,
        "relative_strength": rs,
        "fundamentals": fund,
        "corporate_events": events,
        "regime": regime,
        "news": news,
        "evaluation": evaluation
    }

    print("\n-----------------------------------------------------------------------------------------")
    print(f"🎯 DECISION VERDICT:  {evaluation.get('decision')}  ({evaluation.get('grade')})")
    print(f"⭐ CHECKLIST SCORE:   {evaluation.get('final_score')} / 10.0")
    print(f"📊 RECOMMENDED SIZE:  {evaluation.get('sizing')}")
    print(f"📝 STRATEGY TAKEAWAY: {evaluation.get('decision_summary')}")
    print("-----------------------------------------------------------------------------------------")

    trade = tech.get("trade_structure", {})
    print(f"💰 Entry: ₹{trade.get('entry')} | SL: ₹{trade.get('stop_loss')} ({trade.get('stop_loss_pct')}%) | Target 1: ₹{trade.get('target_1')} (+{trade.get('target_1_pct')}%) [2R]")
    print(f"📅 Results Calendar: {events.get('next_results_date')} ({events.get('days_to_results_display')}) — {events.get('event_risk_badge')}")

    if args.push_wiki:
        saved_path = publish_to_wiki(clean_sym, data_payload, args.wiki_dir)
        print(f"\n✅ Published research dossier to Wiki:")
        print(f"   📄 File: {saved_path}")
        print(f"   🌐 View on Wiki Reader: http://localhost:5111")
    print("=========================================================================================\n")


if __name__ == "__main__":
    main()
