"""
Deterministic Composite Scoring Engine for Indian Equities Swing Scanner.
Combines Technicals, Relative Strength, Fundamentals, Liquidity, and Event Risk
into a transparent, rule-based ranking score (0 to 100).
"""

from typing import Dict, Any


def calculate_composite_score(
    tech_score: float,
    rs_score: float,
    fundamental_score: float,
    volume_multiplier: float,
    event_risk_score: float,
    days_to_results: int
) -> Dict[str, Any]:
    """
    Compute a mathematically rigorous composite swing score (0 to 100).
    
    Weights:
      - Technical Score: 35%
      - Relative Strength vs NIFTY: 25%
      - Fundamental Quality (Screener): 20%
      - Liquidity / Volume surge: 10%
      - Event Risk / Earnings penalty: 10%
    """
    # 1. Base weights
    w_tech = 0.35
    w_rs = 0.25
    w_fund = 0.20
    w_liq = 0.10

    # Liquidity score based on volume multiplier
    if volume_multiplier >= 2.0:
        liq_score = 95.0
    elif volume_multiplier >= 1.5:
        liq_score = 85.0
    elif volume_multiplier >= 1.0:
        liq_score = 70.0
    else:
        liq_score = 50.0

    raw_score = (
        (tech_score * w_tech) +
        (rs_score * w_rs) +
        (fundamental_score * w_fund) +
        (liq_score * w_liq)
    )

    # 2. Event Risk Deduction
    # High event risk (earnings in < 7 days) heavily penalizes the candidate
    risk_penalty = 0.0
    if 0 <= days_to_results <= 3:
        risk_penalty = 18.0  # Major penalty for results in 1-3 days
    elif 0 <= days_to_results <= 7:
        risk_penalty = 12.0  # Penalty for results within a week
    elif 0 <= days_to_results <= 14:
        risk_penalty = 5.0   # Slight penalty for 1-2 weeks
    elif days_to_results > 21 or days_to_results == -1:
        risk_penalty = -3.0  # Small bonus for clear earnings runway (> 3 weeks)

    final_score = round(min(100.0, max(0.0, raw_score - risk_penalty)), 1)

    return {
        "final_score": final_score,
        "breakdown": {
            "technical": round(tech_score, 1),
            "relative_strength": round(rs_score, 1),
            "fundamentals": round(fundamental_score, 1),
            "liquidity": round(liq_score, 1),
            "event_risk_penalty": round(risk_penalty, 1),
        }
    }
