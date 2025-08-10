
from datetime import datetime, timezone
from typing import Dict, Any
import math, statistics

TIMEFRAMES = ["All","3D","5D","10D","15D","30D"]

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

# --- Adapters (replace data loaders with your actual repositories if present) ---
def load_predictions():
    # Return list of dicts with fields:
    # symbol, timeframe, predicted_prob, actual (0/1), edge, resolved(True/False)
    # For now: safe sample data so pipeline runs
    return [
        {"symbol":"RELIANCE","timeframe":"5D","predicted_prob":0.74,"actual":1,"edge":0.004,"resolved":True},
        {"symbol":"TCS","timeframe":"3D","predicted_prob":0.68,"actual":1,"edge":0.0035,"resolved":True},
        {"symbol":"INFY","timeframe":"10D","predicted_prob":0.61,"actual":0,"edge":-0.001,"resolved":True},
        {"symbol":"HDFC","timeframe":"15D","predicted_prob":0.72,"actual":1,"edge":0.003,"resolved":True},
        {"symbol":"SBIN","timeframe":"30D","predicted_prob":0.65,"actual":0,"edge":-0.002,"resolved":True},
        {"symbol":"ICICIBANK","timeframe":"5D","predicted_prob":0.69,"actual":1,"edge":0.0025,"resolved":True},
        {"symbol":"WIPRO","timeframe":"3D","predicted_prob":0.58,"actual":0,"edge":-0.0015,"resolved":True},
        {"symbol":"TATASTEEL","timeframe":"10D","predicted_prob":0.71,"actual":1,"edge":0.0032,"resolved":True},
    ]

def load_trades():
    # closed trades with pnl series for sharpe/sortino (placeholder)
    return {"pnl_daily": [0.002, -0.001, 0.0015, 0.0003, -0.0005, 0.0018, -0.0012, 0.0021, 0.0007, -0.0008]}

def load_risk_inputs():
    # placeholder risk inputs
    return {"var_95_1d": 0.0042, "var_99_1d": 0.010, "slippage_bps": 6, "exposure_pct": 0.25, "max_drawdown": 0.038}

# --- KPI math helpers ---
def brier(scores):
    return sum((p - a)**2 for p,a in scores)/len(scores) if scores else 0.0

def hit_rate(outcomes):
    return sum(outcomes)/len(outcomes) if outcomes else 0.0

def calibration_error(scores):
    # simple absolute error between average prob and actual rate (placeholder)
    if not scores: return 0.0
    pbar = sum(p for p,_ in scores)/len(scores)
    abar = sum(a for _,a in scores)/len(scores)
    return abs(pbar - abar)

def sharpe_approx(pnl_daily):
    if not pnl_daily: return 0.0
    mu = statistics.mean(pnl_daily)
    sd = statistics.pstdev(pnl_daily) or 1e-9
    return (mu / sd) * math.sqrt(252)

def sortino_approx(pnl_daily):
    if not pnl_daily: return 0.0
    downside = [x for x in pnl_daily if x < 0]
    ds_sd = statistics.pstdev(downside) or 1e-9
    mu = statistics.mean(pnl_daily)
    return (mu / ds_sd) * math.sqrt(252)

def compute():
    preds = load_predictions()
    trades = load_trades()
    risk = load_risk_inputs()

    # group by tf (include All)
    frames = {tf: [] for tf in TIMEFRAMES}
    for p in preds:
        tf = p.get("timeframe","5D")
        frames.setdefault(tf, [])
        frames[tf].append(p)
    frames["All"] = preds[:]

    payload = {"last_updated_utc": _now(), "timeframes":{}, "kill_switch":{"active": False, "reasons":[]}}

    for tf, lst in frames.items():
        closed = [p for p in lst if p.get("resolved")]
        scores = [(float(p.get("predicted_prob",0.5)), int(p.get("actual",0))) for p in closed]
        outcomes = [int(p.get("actual",0)) for p in closed]
        edges = [float(p.get("edge",0.0)) for p in closed]
        top_decile = edges[:max(1, len(edges)//10)] if edges else []

        pred_kpis = {
            "brier": round(brier(scores), 4),
            "hit_rate": round(hit_rate(outcomes), 4),
            "calibration_error": round(calibration_error(scores), 4),
            "top_decile_hit_rate": round(hit_rate([1 if e>0 else 0 for e in top_decile]), 4) if top_decile else 0.0,
            "top_decile_avg_edge": round(sum(top_decile)/len(top_decile), 4) if top_decile else 0.0,
        }

        fin_kpis = {
            "sharpe_90d": round(sharpe_approx(trades.get("pnl_daily",[])), 2),
            "sortino_90d": round(sortino_approx(trades.get("pnl_daily",[])), 2),
            "win_loss_expectancy": 0.0012,   # placeholder
            "max_drawdown": round(risk.get("max_drawdown", 0.0), 4)
        }

        risk_kpis = {
            "var_95_1d": round(risk.get("var_95_1d",0.0), 4),
            "var_99_1d": round(risk.get("var_99_1d",0.0), 4),
            "slippage_bps": int(risk.get("slippage_bps", 0)),
            "exposure_pct": round(risk.get("exposure_pct", 0.0), 3)
        }

        payload["timeframes"][tf] = {
            "prediction_kpis": pred_kpis,
            "financial_kpis": fin_kpis,
            "risk_kpis": risk_kpis
        }

    # Kill-switch evaluation (global, based on risk inputs)
    reasons = []
    if risk.get("var_95_1d", 0) > 0.005: reasons.append("VaR(95%) > 0.5%")
    if risk.get("var_99_1d", 0) > 0.012: reasons.append("VaR(99%) > 1.2%")
    if risk.get("max_drawdown", 0) > 0.05: reasons.append("Max drawdown > 5%")
    payload["kill_switch"]["active"] = len(reasons) > 0
    payload["kill_switch"]["reasons"] = reasons

    return payload
