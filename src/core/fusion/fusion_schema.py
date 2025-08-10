
"""
Fusion Schema - Data contracts for KPI + AI Verdict Dashboard
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class MarketSession(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TrendDirection(Enum):
    UP = "↑"
    DOWN = "↓"
    FLAT = "→"
    UNKNOWN = "?"


@dataclass
class KPIMetric:
    """Individual KPI metric with threshold coloring"""
    name: str
    value: float
    target: Optional[float] = None
    color: str = "neutral"  # green, amber, red, neutral
    trend: str = TrendDirection.UNKNOWN.value
    description: str = ""


@dataclass
class TimeframeKPIs:
    """KPIs for a specific timeframe"""
    timeframe: str  # "3D", "5D", "10D", "15D", "30D", "All"
    prediction_kpis: List[KPIMetric]  # Brier, Hit Rate, Calibration
    financial_kpis: List[KPIMetric]   # Sharpe, Sortino, Max DD
    risk_kpis: List[KPIMetric]        # VaR 95, VaR 99, Exposure
    total_predictions: int = 0
    active_predictions: int = 0


@dataclass
class AIVerdictCount:
    """AI verdict distribution"""
    STRONG_BUY: int = 0
    BUY: int = 0
    HOLD: int = 0
    CAUTIOUS: int = 0
    AVOID: int = 0
    
    @property
    def total(self) -> int:
        return self.STRONG_BUY + self.BUY + self.HOLD + self.CAUTIOUS + self.AVOID
    
    def get_percentage(self, verdict: str) -> float:
        if self.total == 0:
            return 0.0
        return (getattr(self, verdict, 0) / self.total) * 100


@dataclass
class ProductBreakdown:
    """Product-specific breakdown"""
    total_predictions: int
    active_predictions: int
    success_rate: float
    avg_confidence: float
    verdict_distribution: AIVerdictCount


@dataclass
class TopSignal:
    """Top performing signal/prediction"""
    symbol: str
    product: str  # "equities", "options", "comm"
    timeframe: str
    ai_verdict: str
    ai_verdict_normalized: str
    confidence: float
    score: float
    predicted_value: Optional[float] = None
    current_value: Optional[float] = None
    outcome_status: str = "IN_PROGRESS"  # MET, NOT_MET, IN_PROGRESS
    start_date: str = ""
    due_date: str = ""
    is_pinned: bool = False


@dataclass
class PinnedSummary:
    """Summary of pinned predictions"""
    total: int = 0
    met: int = 0
    not_met: int = 0
    in_progress: int = 0
    
    @property
    def success_rate(self) -> Optional[float]:
        completed = self.met + self.not_met
        if completed == 0:
            return None
        return (self.met / completed) * 100


@dataclass
class Alert:
    """System alert"""
    type: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    source: str = ""  # GoAhead, Trainer, System


@dataclass
class FusionDashboardPayload:
    """Complete fusion dashboard data payload"""
    last_updated_utc: str
    market_session: MarketSession
    timeframes: List[TimeframeKPIs]
    ai_verdict_summary: Dict[str, AIVerdictCount]  # by product
    product_breakdown: Dict[str, ProductBreakdown]
    pinned_summary: PinnedSummary
    top_signals: List[TopSignal]
    alerts: List[Alert]
    generation_time_ms: float = 0.0
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        
        # Convert enums and datetime objects
        data['market_session'] = self.market_session.value
        
        for alert in data['alerts']:
            alert['severity'] = alert['severity'].value if hasattr(alert['severity'], 'value') else alert['severity']
            if isinstance(alert['timestamp'], datetime):
                alert['timestamp'] = alert['timestamp'].isoformat()
                
        return data


# Utility functions
def create_kpi_metric(name: str, value: float, target: Optional[float] = None, 
                     trend_values: Optional[List[float]] = None) -> KPIMetric:
    """Create a KPI metric with automatic coloring and trend detection"""
    
    # Determine color based on target
    color = "neutral"
    if target is not None:
        if name.lower() in ['brier', 'calibration_error', 'max_drawdown', 'var']:
            # Lower is better
            if value <= target * 0.9:
                color = "green"
            elif value <= target:
                color = "amber"
            else:
                color = "red"
        else:
            # Higher is better (hit_rate, sharpe, etc.)
            if value >= target * 1.1:
                color = "green"
            elif value >= target:
                color = "amber"
            else:
                color = "red"
    
    # Determine trend
    trend = TrendDirection.UNKNOWN.value
    if trend_values and len(trend_values) >= 2:
        recent = trend_values[-1]
        previous = trend_values[-2]
        if recent > previous * 1.05:  # 5% threshold
            trend = TrendDirection.UP.value
        elif recent < previous * 0.95:
            trend = TrendDirection.DOWN.value
        else:
            trend = TrendDirection.FLAT.value
    
    return KPIMetric(
        name=name,
        value=value,
        target=target,
        color=color,
        trend=trend,
        description=f"{name}: {value:.2f}" + (f" (target: {target:.2f})" if target else "")
    )
