import json
import os
import datetime as dt
from typing import Dict, Any, List
from pathlib import Path

class FinalizationService:
    def __init__(self):
        self.data_dir = Path("data/tracking")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.options_file = self.data_dir / "options_tracking.json"

    def load_tracking_data(self) -> Dict[str, Any]:
        """Load options tracking data"""
        if self.options_file.exists():
            try:
                with open(self.options_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"strategies": [], "finalized": []}

    def save_tracking_data(self, data: Dict[str, Any]):
        """Save options tracking data"""
        try:
            with open(self.options_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tracking data: {e}")

    def add_strategy(self, strategy: Dict[str, Any]):
        """Add a new strategy to tracking"""
        data = self.load_tracking_data()

        # Add tracking metadata
        strategy.update({
            "created_at": dt.datetime.now().isoformat(),
            "final_outcome": "IN_PROGRESS",
            "finalized_at": None,
            "target_roi": strategy.get("roi_on_margin", 0),
            "stop_loss_pct": 50.0  # Default 50% stop loss
        })

        data["strategies"].append(strategy)
        self.save_tracking_data(data)

    def finalize_strategies(self, provider=None):
        """Finalize strategies based on rules"""
        data = self.load_tracking_data()
        today = dt.date.today()

        for strategy in data["strategies"]:
            if strategy.get("final_outcome") != "IN_PROGRESS":
                continue

            # Parse due date
            try:
                due_date = dt.datetime.strptime(strategy["due_date"], "%Y-%m-%d").date()
            except (ValueError, KeyError):
                continue

            # Check if past due date
            if today > due_date:
                # Finalize based on final settlement
                current_roi = self._calculate_current_roi(strategy, provider)
                target_roi = strategy.get("target_roi", 0)

                if current_roi >= target_roi:
                    strategy["final_outcome"] = "MET"
                else:
                    strategy["final_outcome"] = "NOT_MET"

                strategy["finalized_at"] = dt.datetime.now().isoformat()
                strategy["actual_roi"] = current_roi

        self.save_tracking_data(data)

    def _calculate_current_roi(self, strategy: Dict[str, Any], provider) -> float:
        """Calculate current ROI for a strategy"""
        if not provider:
            return 0.0

        try:
            # Get current spot price
            symbol = strategy.get("stock")
            if not symbol:
                return 0.0

            current_spot = provider.get_spot(symbol)
            call_strike = strategy.get("call", 0)
            put_strike = strategy.get("put", 0)
            net_credit = strategy.get("net_credit", 0)

            # Calculate P&L for short strangle
            call_value = max(0, current_spot - call_strike)
            put_value = max(0, put_strike - current_spot)

            total_payout = call_value + put_value
            pnl = net_credit - total_payout

            # Calculate ROI
            margin = strategy.get("roi_on_margin", 25) / 100 * net_credit if net_credit > 0 else 1
            roi = (pnl / margin * 100) if margin > 0 else 0

            return round(roi, 2)

        except Exception:
            return 0.0

    def get_accuracy_stats(self, window_days: int = 30) -> Dict[str, Any]:
        """Get accuracy statistics for finalized strategies"""
        data = self.load_tracking_data()
        cutoff_date = dt.date.today() - dt.timedelta(days=window_days)

        # Filter strategies within window that are finalized
        relevant_strategies = []
        for strategy in data["strategies"]:
            if strategy.get("final_outcome") in ["MET", "NOT_MET"]:
                try:
                    created_date = dt.datetime.fromisoformat(strategy["created_at"]).date()
                    if created_date >= cutoff_date:
                        relevant_strategies.append(strategy)
                except (ValueError, KeyError):
                    continue

        total = len(relevant_strategies)
        success = len([s for s in relevant_strategies if s.get("final_outcome") == "MET"])
        failed = total - success

        micro_accuracy = (success / total * 100) if total > 0 else 0.0
        macro_accuracy = micro_accuracy  # Simplified for now

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "micro_accuracy": round(micro_accuracy, 1),
            "macro_accuracy": round(macro_accuracy, 1),
            "by_timeframe": [
                {
                    "timeframe": f"{window_days}D",
                    "success": success,
                    "failed": failed,
                    "total": total
                }
            ]
        }

    def get_active_predictions(self) -> List[Dict[str, Any]]:
        """Get active (in-progress) predictions"""
        data = self.load_tracking_data()
        active = []

        for strategy in data["strategies"]:
            if strategy.get("final_outcome") == "IN_PROGRESS":
                active.append({
                    "due": strategy.get("due_date", "—"),
                    "stock": strategy.get("stock", "—"),
                    "predicted": "Profitable",
                    "current": "In Progress",
                    "proi": strategy.get("target_roi", 0),
                    "croi": "—",
                    "reason": "—"
                })

        return active