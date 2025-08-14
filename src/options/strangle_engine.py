"""
Enhanced Short Strangle Engine with advanced calculations
Implements Monte Carlo breakout probability, dynamic stop loss, and proper ROI calculations
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
import random

logger = logging.getLogger(__name__)

class StrangleEngine:
    """Enhanced Short Strangle Engine with proper calculations"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "feature_flags": {
                "options_v2_enabled": True
            },
            "iv_rank_threshold_high": 55,
            "iv_percent_high": 30,
            "default_stop_loss_factor_min": 0.75,
            "default_stop_loss_factor_max": 1.0,
            "dte_min": 20,
            "dte_max": 45,
            "monte_carlo_paths": 50000
        }

    def compute_roi_on_margin(self, net_credit_per_lot: float, lot_size: int, margin_required: float) -> float:
        """
        Compute ROI on margin percentage
        Formula: (net_credit_total / margin_required) * 100
        """
        try:
            if margin_required <= 0:
                return 0.0

            net_credit_total = net_credit_per_lot * lot_size
            roi_percent = (net_credit_total / margin_required) * 100
            return round(roi_percent, 2)
        except Exception as e:
            logger.error(f"Error computing ROI on margin: {e}")
            return 0.0

    def monte_carlo_breakout_prob(self, spot: float, put_strike: float, call_strike: float, 
                                 iv_percent: float, dte_days: int, paths: int = None) -> Dict[str, float]:
        """
        Monte Carlo simulation for breakout probability using lognormal returns
        """
        try:
            if paths is None:
                paths = self.config["monte_carlo_paths"]

            if iv_percent <= 0 or dte_days <= 0:
                return {"breakout_prob_percent": 50.0, "prob_stay_in_range_percent": 50.0}

            T = dte_days / 365.0
            sigma = iv_percent / 100.0
            mu = 0.0  # Risk-neutral drift

            # Generate random normal values
            np.random.seed(42)  # For reproducible results
            Z = np.random.normal(0, 1, paths)

            # Simulate final stock prices
            S_T = spot * np.exp((mu - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)

            # Count paths outside the breakeven range
            outside_range = (S_T < put_strike) | (S_T > call_strike)
            breakout_count = np.sum(outside_range)

            breakout_prob_percent = (breakout_count / paths) * 100
            prob_stay_in_range_percent = 100 - breakout_prob_percent

            return {
                "breakout_prob_percent": round(breakout_prob_percent, 1),
                "prob_stay_in_range_percent": round(prob_stay_in_range_percent, 1)
            }

        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            return {"breakout_prob_percent": 50.0, "prob_stay_in_range_percent": 50.0}

    def stress_max_loss_two_sigma(self, spot: float, put_strike: float, call_strike: float, 
                                 iv_percent: float, dte_days: int, net_credit_per_lot: float, 
                                 lot_size: int) -> float:
        """
        Calculate max loss at 2-sigma stress scenario
        """
        try:
            if iv_percent <= 0 or dte_days <= 0:
                return 0.0

            T = dte_days / 365.0
            sigma = iv_percent / 100.0
            sigma_T = sigma * np.sqrt(T)

            # Stressed prices
            S_down = spot * np.exp(-2 * sigma_T)
            S_up = spot * np.exp(2 * sigma_T)

            # Payoffs at stressed prices (per lot)
            # At S_down
            call_payoff_down = 0
            put_payoff_down = max(put_strike - S_down, 0)
            PL_down = net_credit_per_lot - put_payoff_down

            # At S_up
            call_payoff_up = max(S_up - call_strike, 0)
            put_payoff_up = 0
            PL_up = net_credit_per_lot - call_payoff_up

            # Worst case (most negative) multiplied by lot size
            max_loss_two_sigma = min(PL_down, PL_up) * lot_size

            return round(max_loss_two_sigma, 2)

        except Exception as e:
            logger.error(f"Error calculating max loss 2-sigma: {e}")
            return 0.0

    def compute_theta_per_day(self, theta_call: float, theta_put: float, lot_size: int) -> float:
        """
        Compute theta per day from greeks
        Formula: (|theta_call| + |theta_put|) * lot_size
        """
        try:
            theta_net_per_contract = abs(theta_call) + abs(theta_put)
            theta_per_day_per_lot = theta_net_per_contract * lot_size
            return round(theta_per_day_per_lot, 2)
        except Exception as e:
            logger.error(f"Error computing theta per day: {e}")
            return 0.0

    def dynamic_stop_loss_percent(self, iv_rank: int) -> int:
        """
        Calculate dynamic stop loss percentage based on IV rank
        Higher IV rank = tighter stop loss
        """
        try:
            if iv_rank >= 80:
                return 150  # Tight stop loss for very high IV
            elif iv_rank >= 60:
                return 180  # Normal stop loss
            elif iv_rank >= 40:
                return 200  # Looser stop loss for lower IV
            else:
                return 250  # Very loose stop loss for low IV
        except Exception as e:
            logger.error(f"Error calculating dynamic stop loss: {e}")
            return 180  # Default

    def market_stability_score(self, rv20_pct: float, adx: float, event_flag: str, iv_rank: int) -> int:
        """
        Calculate market stability score (0-100)
        30%: Realized vol percentile (lower vol → higher score)
        30%: Trendiness (inverse of ADX)
        20%: Gap risk (0 if events, else 100)
        20%: IV rank stability
        """
        try:
            # Realized vol component (30%)
            rv_score = max(0, min(100, 100 - rv20_pct)) * 0.3

            # ADX component (30%) - lower ADX = higher stability
            adx_score = max(0, min(100, 100 - adx)) * 0.3

            # Gap risk component (20%)
            gap_risk_score = (0 if event_flag != "CLEAR" else 100) * 0.2

            # IV rank stability (20%)
            iv_stability = (1 - abs(iv_rank - 50) / 50) * 100 * 0.2

            stability_score = rv_score + adx_score + gap_risk_score + iv_stability
            return round(max(0, min(100, stability_score)))

        except Exception as e:
            logger.error(f"Error calculating market stability score: {e}")
            return 50

    def enrich_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate all calculations for a single stock row
        """
        try:
            enriched = row.copy()

            # Extract required fields
            symbol = row.get('symbol', '')
            spot_price = row.get('spot', 0) # Renamed from 'spot' to 'spot_price' for clarity
            call_strike = row.get('call_strike', 0)
            put_strike = row.get('put_strike', 0)
            dte_days = row.get('dte_days', 30)
            iv_percent = row.get('iv_percent', 25.0)
            iv_rank = row.get('iv_rank', 50)
            net_credit = row.get('net_credit_per_lot', 0) # Renamed from 'net_credit_per_lot' to 'net_credit'
            lot_size = row.get('lot_size', 250)
            margin_required = row.get('margin_required', 0)
            event_flag = row.get('event_flag', 'CLEAR')

            # Greeks
            theta_call = row.get('theta_call', -0.05)
            theta_put = row.get('theta_put', -0.05)

            # Mock additional data for stability score
            rv20_pct = row.get('rv20_pct', 50.0)
            adx = row.get('adx', 25.0)

            # Compute all metrics
            roi_on_margin = self.compute_roi_on_margin(
                net_credit, lot_size, margin_required
            )

            breakout_data = self.monte_carlo_breakout_prob(
                spot_price, put_strike, call_strike, iv_percent, dte_days
            )
            enriched.update(breakout_data)

            theta_per_day = self.compute_theta_per_day(
                theta_call, theta_put, lot_size
            )

            max_loss_2sigma = self.stress_max_loss_two_sigma(
                spot_price, put_strike, call_strike, iv_percent, dte_days, 
                net_credit, lot_size
            )

            stop_loss_percent = self.dynamic_stop_loss_percent(iv_rank)

            market_stability_score_num = self.market_stability_score(
                rv20_pct, adx, event_flag, iv_rank
            )

            # Breakeven calculations
            credit_per_share = net_credit / lot_size if lot_size > 0 else 0
            breakeven_lower = put_strike - credit_per_share
            breakeven_upper = call_strike + credit_per_share

            # Generate verdicts
            verdict = self._generate_verdict(enriched)
            ai_verdict = self._generate_ai_verdict(enriched)

            # Map numerical stability score to text
            if market_stability_score_num >= 80:
                market_stability = "High"
            elif market_stability_score_num >= 60:
                market_stability = "Med"
            else:
                market_stability = "Low"
            
            enriched['market_stability_score'] = market_stability
            enriched['market_stability'] = market_stability  # Additional mapping

            # Populate enriched dictionary with all computed values (with multiple field mappings)
            enriched['symbol'] = symbol
            enriched['spot'] = spot_price
            enriched['spot_price'] = spot_price
            enriched['current_price'] = spot_price
            enriched['call_strike'] = call_strike
            enriched['put_strike'] = put_strike
            enriched['net_credit_per_lot'] = net_credit
            enriched['total_premium'] = net_credit
            enriched['breakeven_lower'] = breakeven_lower
            enriched['breakeven_upper'] = breakeven_upper
            enriched['breakeven_low'] = breakeven_lower
            enriched['breakeven_high'] = breakeven_upper
            enriched['breakout_prob_percent'] = breakout_data.get('breakout_prob_percent', 50.0)
            enriched['breakout_probability'] = breakout_data.get('breakout_prob_percent', 50.0) / 100.0
            enriched['max_loss_two_sigma'] = max_loss_2sigma
            enriched['max_loss_2_sigma'] = max_loss_2sigma
            enriched['roi_on_margin_percent'] = roi_on_margin
            enriched['roi_on_margin'] = roi_on_margin
            enriched['theta_per_day_per_lot'] = theta_per_day
            enriched['theta_per_day'] = theta_per_day
            enriched['dte_days'] = dte_days
            enriched['days_to_expiry'] = dte_days
            enriched['iv_percent'] = iv_percent
            enriched['implied_volatility'] = iv_percent / 100.0
            enriched['iv_rank'] = iv_rank
            enriched['stop_loss_percent_of_credit'] = stop_loss_percent
            enriched['stop_loss_percent'] = stop_loss_percent
            enriched['verdict'] = verdict
            enriched['ai_agent_verdict'] = ai_verdict
            enriched['ai_verdict'] = ai_verdict
            enriched['event_flag'] = event_flag
            enriched['has_event_risk'] = (event_flag == 'EARNINGS')


            return enriched

        except Exception as e:
            logger.error(f"Error enriching row for {row.get('symbol', 'UNKNOWN')}: {e}")
            return row

    def _generate_verdict(self, row: Dict[str, Any]) -> str:
        """Generate trading verdict based on multiple factors"""
        try:
            score = 0

            # ROI component
            roi = row.get('roi_on_margin_percent', 0)
            if roi >= 3.0:
                score += 25
            elif roi >= 2.0:
                score += 15
            elif roi >= 1.0:
                score += 5

            # IV conditions
            iv_rank = row.get('iv_rank', 50)
            iv_percent = row.get('iv_percent', 25)
            if iv_rank >= 70 and iv_percent >= 30:
                score += 25
            elif iv_rank >= 60 and iv_percent >= 25:
                score += 15

            # Breakout probability
            breakout_prob = row.get('breakout_prob_percent', 50)
            if breakout_prob <= 25:
                score += 20
            elif breakout_prob <= 35:
                score += 10
            elif breakout_prob >= 50:
                score -= 15

            # Event risk
            event_flag = row.get('event_flag', 'CLEAR')
            if event_flag == 'CLEAR':
                score += 15
            elif event_flag == 'EARNINGS':
                score -= 20

            # Market stability
            # Use the original numerical score for verdict generation logic
            stability = row.get('market_stability_score', 50) 
            # Check if stability is already a string, if so, convert back for calculation
            if isinstance(stability, str):
                if stability == "High":
                    stability_num = 80 # Example mapping, adjust as needed
                elif stability == "Med":
                    stability_num = 60
                else:
                    stability_num = 40
            else:
                stability_num = stability # Assume it's the numerical score

            if stability_num >= 80:
                score += 15
            elif stability_num >= 60:
                score += 5
            elif stability_num < 40:
                score -= 10

            # Generate verdict
            if score >= 70:
                return "Top Pick"
            elif score >= 50:
                return "Buy"
            elif score >= 30:
                return "Hold"
            elif score >= 10:
                return "Cautious"
            else:
                return "Avoid"

        except Exception as e:
            logger.error(f"Error generating verdict: {e}")
            return "Hold"

    def _generate_ai_verdict(self, row: Dict[str, Any]) -> str:
        """Generate AI agent verdict with enhanced logic"""
        try:
            # Enhanced AI scoring with more sophisticated logic
            base_verdict = self._generate_verdict(row)

            # AI adjustments based on advanced factors
            ai_adjustments = 0

            # Theta efficiency
            theta_per_day = row.get('theta_per_day_per_lot', 0)
            credit = row.get('net_credit_per_lot', 0)
            if credit > 0:
                theta_efficiency = theta_per_day / credit
                if theta_efficiency > 0.05:  # High theta decay
                    ai_adjustments += 1

            # Risk-adjusted returns
            max_loss = abs(row.get('max_loss_two_sigma', 0))
            roi = row.get('roi_on_margin_percent', 0)
            if max_loss > 0 and roi > 0:
                risk_return_ratio = roi / (max_loss / 1000)  # Normalize
                if risk_return_ratio > 2.0:
                    ai_adjustments += 1

            # Upgrade/downgrade based on AI analysis
            verdict_hierarchy = ["Avoid", "Cautious", "Hold", "Buy", "Strong Buy"]
            current_index = verdict_hierarchy.index(base_verdict) if base_verdict in verdict_hierarchy else 2

            # Apply AI adjustments
            if ai_adjustments >= 2:
                current_index = min(len(verdict_hierarchy) - 1, current_index + 1)
            elif ai_adjustments <= -1:
                current_index = max(0, current_index - 1)

            ai_verdict = verdict_hierarchy[current_index]
            return "Strong Buy" if ai_verdict == "Buy" and ai_adjustments >= 2 else ai_verdict

        except Exception as e:
            logger.error(f"Error generating AI verdict: {e}")
            return "Hold"

    def process_strangle_recommendations(self, universe_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process the entire universe and return enriched recommendations with summary
        """
        try:
            enriched_rows = []

            # Filter by DTE range
            dte_min = self.config["dte_min"]
            dte_max = self.config["dte_max"]

            for row in universe_data:
                dte = row.get('dte_days', 30)
                if dte_min <= dte <= dte_max:
                    enriched_row = self.enrich_row(row)
                    enriched_rows.append(enriched_row)

            # Calculate summary metrics
            summary = self._calculate_summary(enriched_rows)

            return {
                "summary": summary,
                "rows": enriched_rows,
                "total_rows": len(enriched_rows),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing strangle recommendations: {e}")
            return {
                "summary": {"error": str(e)},
                "rows": [],
                "total_rows": 0
            }

    def _calculate_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary cards correctly"""
        try:
            total_strategies = len(rows)

            # Avg ROI (exclude nulls/zeros)
            valid_rois = [r.get('roi_on_margin_percent', 0) for r in rows if r.get('roi_on_margin_percent', 0) > 0]
            avg_roi = sum(valid_rois) / len(valid_rois) if valid_rois else 0.0

            # High IV Opportunities
            iv_threshold_rank = self.config["iv_rank_threshold_high"]
            iv_threshold_percent = self.config["iv_percent_high"]
            high_iv_count = sum(
                1 for r in rows 
                if r.get('iv_rank', 0) >= iv_threshold_rank or r.get('iv_percent', 0) >= iv_threshold_percent
            )

            # Event-Free Trades
            event_free_count = sum(1 for r in rows if r.get('event_flag', '') == 'CLEAR')

            return {
                "total_strategies": total_strategies,
                "avg_roi": round(avg_roi, 1),
                "high_iv_opportunities": high_iv_count,
                "event_free_trades": event_free_count
            }

        except Exception as e:
            logger.error(f"Error calculating summary: {e}")
            return {
                "total_strategies": 0,
                "avg_roi": 0.0,
                "high_iv_opportunities": 0,
                "event_free_trades": 0
            }


# Global instance
strangle_engine = StrangleEngine()