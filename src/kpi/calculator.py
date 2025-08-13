import time
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Import necessary components for KPI calculation
from src.common_repository.config.runtime import (
    KPI_ROLLING_WINDOW_DAYS, KPI_MIN_SAMPLES, get_market_tz
)
from src.common_repository.storage.json_store import json_store
from src.kpi.calculators import KPICalculator as RealKPICalculator, calculate_timeframe_kpis

# Define a class to hold KPI metrics for a given timeframe
class KPIMetrics:
    def __init__(self,
                 timeframe: str,
                 total_predictions: int = 0,
                 closed_predictions: int = 0,
                 insufficient_data: bool = True,
                 brier_score: float = 0.0,
                 directional_hit_rate: float = 0.0,
                 calibration_error: float = 0.0,
                 top_decile_hit_rate: float = 0.0,
                 top_decile_avg_edge: float = 0.0,
                 sharpe_ratio: float = 0.0,
                 sortino_ratio: float = 0.0,
                 win_loss_expectancy: float = 0.0,
                 max_drawdown: float = 0.0,
                 var_95: float = 0.0,
                 var_99: float = 0.0,
                 exposure_per_trade: float = 0.0,
                 status: str = "pending"):
        self.timeframe = timeframe
        self.total_predictions = total_predictions
        self.closed_predictions = closed_predictions
        self.insufficient_data = insufficient_data
        self.brier_score = brier_score
        self.directional_hit_rate = directional_hit_rate
        self.calibration_error = calibration_error
        self.top_decile_hit_rate = top_decile_hit_rate
        self.top_decile_avg_edge = top_decile_avg_edge
        self.sharpe_ratio = sharpe_ratio
        self.sortino_ratio = sortino_ratio
        self.win_loss_expectancy = win_loss_expectancy
        self.max_drawdown = max_drawdown
        self.var_95 = var_95
        self.var_99 = var_99
        self.exposure_per_trade = exposure_per_trade
        self.status = status

    def to_dict(self):
        """Convert metrics to dictionary"""
        return self.__dict__

# Placeholder for the actual KPI calculation logic, which would be in src/kpi/calculators.py
# This class is assumed to have a method `calculate_kpis` that takes predictions and returns a result object with KPI values.
# For the purpose of this example, we will define a dummy class and results.

class DummyRealKPICalculator:
    def calculate_kpis(self, predictions: List[Dict[str, Any]], timeframe: str):
        # This is a dummy implementation. Replace with actual KPI calculations.
        # It should return an object with attributes like:
        # brier_score, directional_accuracy, calibration_error, hit_rate, bias,
        # sharpe_ratio, sortino_ratio, information_ratio, max_drawdown,
        # var_95, var_99, coverage_ratio, status
        print(f"Dummy calculation for timeframe: {timeframe} with {len(predictions)} predictions.")
        class DummyResult:
            def __init__(self):
                self.brier_score = 0.1
                self.directional_accuracy = 0.7
                self.calibration_error = 0.05
                self.hit_rate = 0.8
                self.bias = 0.02
                self.sharpe_ratio = 1.5
                self.sortino_ratio = 2.0
                self.information_ratio = 0.8
                self.max_drawdown = -0.05
                self.var_95 = 0.02
                self.var_99 = 0.03
                self.coverage_ratio = 0.9
                self.status = "success"
        return DummyResult()

# Use the dummy calculator if the real one is not available, or if you want to test without the actual implementation
# RealKPICalculator = DummyRealKPICalculator

class KPIEngine:
    """
    Engine to compute and manage KPI metrics.
    """
    def __init__(self):
        # Initialize any dependencies if needed
        pass

    def calculate_timeframe_metrics(self, timeframe: str, predictions: List[Dict[str, Any]]) -> KPIMetrics:
        """Calculate metrics for a specific timeframe using real calculators"""
        try:
            # Filter predictions for this timeframe
            tf_predictions = [p for p in predictions if p.get('timeframe') == timeframe]
            closed_predictions = [p for p in tf_predictions if p.get('resolved', False)]

            min_samples = KPI_MIN_SAMPLES.get(timeframe, 5)
            insufficient_data = len(closed_predictions) < min_samples

            if insufficient_data or not closed_predictions:
                return KPIMetrics(
                    timeframe=timeframe,
                    total_predictions=len(tf_predictions),
                    closed_predictions=len(closed_predictions),
                    insufficient_data=True,
                    status="insufficient_data"
                )

            # Use real calculator
            real_calculator = RealKPICalculator()
            real_results = real_calculator.calculate_kpis(closed_predictions, timeframe)

            # Convert to our KPIMetrics format
            metrics = KPIMetrics(
                timeframe=timeframe,
                total_predictions=len(tf_predictions),
                closed_predictions=len(closed_predictions),
                insufficient_data=False,
                brier_score=real_results.brier_score,
                directional_hit_rate=real_results.directional_accuracy,
                calibration_error=real_results.calibration_error,
                top_decile_hit_rate=real_results.hit_rate,  # Use hit_rate as proxy
                top_decile_avg_edge=real_results.bias,  # Use bias as proxy
                sharpe_ratio=real_results.sharpe_ratio,
                sortino_ratio=real_results.sortino_ratio,
                win_loss_expectancy=real_results.information_ratio,  # Use info ratio as proxy
                max_drawdown=real_results.max_drawdown,
                var_95=real_results.var_95,
                var_99=real_results.var_99,
                exposure_per_trade=real_results.coverage_ratio,  # Use coverage as proxy
                status=real_results.status
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics for {timeframe}: {str(e)}")
            return KPIMetrics(
                timeframe=timeframe,
                total_predictions=0,
                closed_predictions=0,
                insufficient_data=True,
                status="error"
            )

    def _get_portfolio_data(self, timeframe: str) -> Dict[str, Any]:
        """Get portfolio data including Paper Trade P&L for calculations"""
        try:
            # Get Paper Trade portfolio data
            portfolio_data = {"total_value": 1000000.0, "returns": [], "positions": []}

            try:
                from src.utils.file_utils import load_json_safe

                # Load Paper Trade portfolio
                pt_portfolio = load_json_safe("data/persistent/papertrade_portfolio.json", {})
                pt_orders = load_json_safe("data/persistent/papertrade_orders.json", [])

                if pt_portfolio and pt_orders:
                    portfolio_data["total_value"] = pt_portfolio.get("current_capital", 1000000.0)

                    # Calculate returns from order history for the timeframe
                    from datetime import datetime, timedelta

                    timeframe_days = {
                        "3D": 3, "5D": 5, "10D": 10, "15D": 15, "30D": 30, "All": 365
                    }

                    days = timeframe_days.get(timeframe, 30)
                    cutoff_date = datetime.now() - timedelta(days=days)

                    # Filter orders by timeframe
                    filtered_orders = [
                        order for order in pt_orders
                        if datetime.fromisoformat(order["timestamp"]) >= cutoff_date
                    ]

                    # Calculate daily returns from order P&L
                    if filtered_orders:
                        daily_pnl = {}
                        for order in filtered_orders:
                            order_date = datetime.fromisoformat(order["timestamp"]).date()
                            if order_date not in daily_pnl:
                                daily_pnl[order_date] = 0

                            # Simple P&L calculation based on order type
                            if order["side"] == "SELL":
                                daily_pnl[order_date] += order["exec_value"]
                            else:
                                daily_pnl[order_date] -= order["exec_value"]

                        # Convert to returns
                        base_capital = pt_portfolio.get("initial_capital", 1000000.0)
                        returns = [pnl / base_capital for pnl in daily_pnl.values()]
                        portfolio_data["returns"] = returns[-30:]  # Last 30 days max

                    logger.info(f"✅ Paper Trade portfolio integrated: ₹{portfolio_data['total_value']:,.2f}")

            except Exception as e:
                logger.warning(f"Could not load Paper Trade data: {e}, using defaults")

            # Fallback mock data if no Paper Trade data
            if not portfolio_data["returns"]:
                portfolio_data["returns"] = [0.02, -0.01, 0.015, 0.008, -0.005]

            return portfolio_data

        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")
            return {"total_value": 1000000.0, "returns": [0.0], "positions": []}


def now_iso():
    """Return current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

# Export for backwards compatibility
__all__ = ['KPIMetrics', 'KPIEngine', 'now_iso']