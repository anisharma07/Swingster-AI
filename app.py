"""
Flask Web Application & REST API Server for Indian Equities Swing Trading Platform.
Serves interactive dashboard, live scanners, 360-degree stock research cards,
and manual fetcher testing studio.
"""

import os
import sys
import logging
from typing import Dict, Any
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from modules.universe import UNIVERSES, TOP_SWING_WATCHLIST, get_universe, from_yf_symbol, get_stock_sector
from modules.market_regime import analyze_market_regime
from modules.technicals import analyze_technicals, fetch_historical_ohlcv
from modules.relative_strength import calculate_relative_strength, get_benchmark_data, rank_universe_by_relative_strength
from modules.corporate_events import fetch_corporate_events_and_risk
from modules.fundamentals import analyze_fundamentals
from modules.news_feed import fetch_stock_news
from modules.scoring import calculate_composite_score
from modules.nse_client import nse_client
from scripts.scan_universe import run_scanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)


@app.route("/")
def index():
    """Render the main Swing Trading Research & Scanner Dashboard."""
    return render_template("index.html")


@app.route("/api/market-regime", methods=["GET"])
def get_market_regime():
    """Return live Indian Market Regime diagnosis and sector matrix."""
    try:
        regime_data = analyze_market_regime()
        return jsonify({"status": "success", "data": regime_data})
    except Exception as e:
        logger.exception("Error in /api/market-regime")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/universes", methods=["GET"])
def get_universes():
    """Return available liquid universe lists and counts."""
    universe_summary = {
        "swing_top30": {"name": "🔥 Top Swing & Momentum 30", "count": len(UNIVERSES["swing_top30"])},
        "nifty_smallcap": {"name": "🚀 NIFTY Smallcap 100 (High-Beta)", "count": len(UNIVERSES["nifty_smallcap"])},
        "nifty_midcap": {"name": "⚡ NIFTY Midcap 100 (Growth)", "count": len(UNIVERSES["nifty_midcap"])},
        "nifty50": {"name": "🏛 NIFTY 50 (Large Caps)", "count": len(UNIVERSES["nifty50"])},
        "nifty100": {"name": "📈 NIFTY 100 (Large & Mid)", "count": len(UNIVERSES["nifty100"])},
        "nifty500": {"name": "🌐 NIFTY 500 (Broad Market)", "count": len(UNIVERSES["nifty500"])},
        "theme_defense": {"name": "🛡 Defense & Railways Basket", "count": len(UNIVERSES["theme_defense"])},
        "theme_it": {"name": "💻 IT & Tech Basket", "count": len(UNIVERSES["theme_it"])},
        "theme_fin": {"name": "🏦 Banking & Capital Markets", "count": len(UNIVERSES["theme_fin"])},
    }
    return jsonify({"status": "success", "universes": universe_summary})


@app.route("/api/scan", methods=["POST"])
def scan_market():
    """
    Run market scanner across universe with customizable filters.
    Payload: { "universe": "swing_top30", "setup": "all", "min_score": 0, "min_vol": 1.0 }
    """
    try:
        data = request.get_json() or {}
        universe_name = data.get("universe", "swing_top30")
        setup_filter = data.get("setup", "all")
        min_score = float(data.get("min_score", 0.0))
        
        candidates = run_scanner(
            universe_name=universe_name,
            setup_filter=setup_filter,
            min_score=min_score,
            max_workers=10
        )
        return jsonify({
            "status": "success",
            "count": len(candidates),
            "universe": universe_name,
            "candidates": candidates
        })
    except Exception as e:
        logger.exception("Error in /api/scan")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stock/<symbol>", methods=["GET"])
def get_stock_deepdive(symbol: str):
    """
    Return comprehensive 360-degree stock research card:
    Technicals, RS vs Nifty, Screener Fundamentals, NSE Board Meetings, News, Trade Plan.
    """
    clean_sym = from_yf_symbol(symbol)
    try:
        stock_df = fetch_historical_ohlcv(clean_sym, period="1y")
        if stock_df is None or len(stock_df) < 30:
            return jsonify({"status": "error", "message": f"Could not fetch price data for {clean_sym}"}), 404

        tech_data = analyze_technicals(clean_sym, stock_df)
        nifty_df = get_benchmark_data("^NSEI", period="1y")
        rs_data = calculate_relative_strength(stock_df, nifty_df)
        fund_data = analyze_fundamentals(clean_sym)
        events_data = fetch_corporate_events_and_risk(clean_sym)
        news_items = fetch_stock_news(clean_sym, company_name=fund_data.get("company_name", clean_sym), limit=8)

        # Composite score
        tech_score = tech_data.get("technical_score", 50.0) if tech_data else 50.0
        rs_score = rs_data.get("rs_score", 50.0)
        fund_score = fund_data.get("fundamental_score", 50.0)
        vol_mult = tech_data.get("volume_multiplier", 1.0) if tech_data else 1.0
        event_risk_score = events_data.get("event_risk_score", 2.0)
        days_results = events_data.get("days_to_results", -1)

        scoring = calculate_composite_score(
            tech_score=tech_score,
            rs_score=rs_score,
            fundamental_score=fund_score,
            volume_multiplier=vol_mult,
            event_risk_score=event_risk_score,
            days_to_results=days_results
        )

        # Prepare chart series data (last 90 trading days for fast interactive charting)
        recent_df = stock_df.tail(90).copy()
        close_series = recent_df['Close'].squeeze()
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]
        close_series = close_series.astype(float)

        ema20_series = close_series.ewm(span=20, adjust=False).mean()
        ema50_series = close_series.ewm(span=50, adjust=False).mean()
        
        vol_series = recent_df['Volume'].squeeze()
        if isinstance(vol_series, pd.DataFrame):
            vol_series = vol_series.iloc[:, 0]

        dates_list = [d.strftime("%d %b") for d in recent_df.index]
        close_list = [round(float(c), 2) for c in close_series]
        ema20_list = [round(float(e), 2) for e in ema20_series]
        ema50_list = [round(float(e), 2) for e in ema50_series]
        vol_list = [int(v) if not pd.isna(v) else 0 for v in vol_series]

        chart_data = {
            "dates": dates_list,
            "close": close_list,
            "ema_20": ema20_list,
            "ema_50": ema50_list,
            "volume": vol_list
        }

        # Bear case & Invalidation
        invalidation_level = tech_data.get("trade_structure", {}).get("stop_loss", "Below 20 EMA")
        bear_case_points = []
        if days_results != -1 and days_results <= 7:
            bear_case_points.append(f"Upcoming quarterly results in {days_results} days creates event binary risk.")
        if tech_data and tech_data.get("rsi", 50) > 75:
            bear_case_points.append("RSI is in overbought zone (>75), potential for mean reversion pullback.")
        if fund_data and fund_data.get("cons"):
            bear_case_points.append(f"Fundamental factor: {fund_data['cons'][0]}")
        bear_case_points.append(f"Setup invalidates on daily close below ₹{invalidation_level}.")

        return jsonify({
            "status": "success",
            "data": {
                "symbol": clean_sym,
                "company_name": fund_data.get("company_name", clean_sym),
                "sector": get_stock_sector(clean_sym),
                "composite_score": scoring.get("final_score"),
                "score_breakdown": scoring.get("breakdown"),
                "technicals": tech_data,
                "relative_strength": rs_data,
                "fundamentals": fund_data,
                "corporate_events": events_data,
                "news": news_items,
                "chart": chart_data,
                "bear_case": bear_case_points
            }
        })
    except Exception as e:
        logger.exception(f"Error fetching deepdive for {clean_sym}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/screener/<symbol>", methods=["GET"])
def get_screener_data(symbol: str):
    """Direct Screener.in fetch endpoint for manual testing."""
    clean_sym = from_yf_symbol(symbol)
    try:
        data = analyze_fundamentals(clean_sym)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/events/<symbol>", methods=["GET"])
def get_events_data(symbol: str):
    """Direct NSE corporate events and results calendar endpoint."""
    clean_sym = from_yf_symbol(symbol)
    try:
        events = fetch_corporate_events_and_risk(clean_sym)
        announcements = nse_client.get_announcements(clean_sym, limit=10)
        return jsonify({
            "status": "success",
            "events": events,
            "announcements": announcements
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/news/<symbol>", methods=["GET"])
def get_news_data(symbol: str):
    """Direct Google News RSS feed endpoint."""
    clean_sym = from_yf_symbol(symbol)
    try:
        news = fetch_stock_news(clean_sym, limit=12)
        return jsonify({"status": "success", "symbol": clean_sym, "news": news})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/test-fetch", methods=["POST"])
def manual_test_fetch():
    """
    On-Demand Manual Fetcher Studio Endpoint.
    Accepts: { "target": "technicals|screener|events|news|quote|regime", "symbol": "TRENT" }
    """
    req = request.get_json() or {}
    target = req.get("target", "technicals")
    symbol = req.get("symbol", "TRENT").upper().strip()
    clean_sym = from_yf_symbol(symbol)

    try:
        if target == "regime":
            res = analyze_market_regime()
        elif target == "technicals":
            stock_df = fetch_historical_ohlcv(clean_sym, period="1y")
            res = analyze_technicals(clean_sym, stock_df)
        elif target == "screener":
            res = analyze_fundamentals(clean_sym)
        elif target == "events":
            events = fetch_corporate_events_and_risk(clean_sym)
            announcements = nse_client.get_announcements(clean_sym, limit=8)
            res = {"events": events, "announcements": announcements}
        elif target == "news":
            res = fetch_stock_news(clean_sym, limit=10)
        elif target == "quote":
            res = nse_client.get_quote(clean_sym)
        else:
            return jsonify({"status": "error", "message": f"Unknown fetch target: {target}"}), 400

        return jsonify({
            "status": "success",
            "target": target,
            "symbol": clean_sym,
            "result": res
        })
    except Exception as e:
        logger.exception("Error in /api/test-fetch")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting Indian Equities Swing Research Server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
