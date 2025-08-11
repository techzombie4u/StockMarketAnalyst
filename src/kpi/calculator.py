import time
from datetime import datetime, timezone
from typing import Dict, Any

def now_iso():
    """Return current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def compute_all(tf="All"):
    """
    Compute all KPIs for given timeframe
    Deterministic fixture-based numbers; replace later with real calcs
    """
    base = {
        "prediction_kpis": {
            "acc": 0.66,
            "precision": 0.64,
            "recall": 0.63,
            "mape": 0.12,
            "hitRatio": 0.65,
            "winExp": 0.012
        },
        "financial_kpis": {
            "sharpe": 1.18,
            "sortino": 1.95,
            "pnlGrowth": 0.07,
            "mdd": -0.08
        },
        "risk_kpis": {
            "volRegime": "MEDIUM",
            "var": 0.03,
            "dailyLossCap": 0.02
        }
    }

    # Slight tf variation
    mult = {
        "3D": 0.95,
        "5D": 0.98,
        "10D": 1.02,
        "15D": 1.04,
        "30D": 1.06,
        "All": 1.0
    }.get(tf, 1.0)

    base["prediction_kpis"]["acc"] *= mult
    base["financial_kpis"]["sharpe"] *= mult
    base["financial_kpis"]["sortino"] *= mult
    base["financial_kpis"]["mdd"] *= (1 if mult <= 1 else 1.0)  # keep sign

    return base

def get_kpi_summary(tf="All"):
    """Get simplified KPI summary for dashboard"""
    kpis = compute_all(tf)
    return {
        "acc": kpis["prediction_kpis"]["acc"],
        "sharpe": kpis["financial_kpis"]["sharpe"],
        "sortino": kpis["financial_kpis"]["sortino"],
        "mdd": kpis["financial_kpis"]["mdd"],
        "winExp": kpis["prediction_kpis"]["winExp"],
        "coverage": 0.89  # Fixed coverage value
    }

# Export for backwards compatibility
__all__ = ['compute_all', 'get_kpi_summary', 'KPICalculator', 'now_iso']