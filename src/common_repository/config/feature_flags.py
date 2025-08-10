"""
Feature Flags Configuration
Dynamic feature toggling for the application
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FeatureFlags:
    """Feature flags manager"""

    def __init__(self):
        self.config_file = "src/common_repository/config/feature_flags.json"
        self._flags = self._load_flags()

    def _load_flags(self) -> Dict[str, Any]:
        """Load feature flags from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default flags
                default_flags = {
                    "enable_dynamic_confidence": True,
                    "enable_ml_predictions": True,
                    "enable_advanced_scoring": True,
                    "enable_risk_management": True,
                    "enable_sentiment_analysis": False,
                    "enable_caching": True,
                    "debug_mode": False,
                    # Performance and reliability flags (heavy features OFF by default)
                    "enable_dynamic_confidence": False,
                    "enable_smart_agent_validation": True,
                    "enable_enhanced_verdict_logic": True,  # kept lightweight
                    "enable_visual_roi_trends": False,
                    "enable_complete_timeframe_support": False,
                    "enable_all_timeframes_concurrent": False,
                    "enable_realtime_agents": False,
                    "enable_autorefresh": True,
                }
                self._save_flags(default_flags)
                return default_flags
        except Exception as e:
            logger.error(f"Error loading feature flags: {e}")
            return {}

    def _save_flags(self, flags: Dict[str, Any]):
        """Save flags to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(flags, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feature flags: {e}")

    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags"""
        return self._flags.copy()

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag_name, False)

    def set_flag(self, flag_name: str, value: bool):
        """Set feature flag at runtime (in-memory only)"""
        if flag_name in self._flags:
            old_value = self._flags[flag_name]
            self._flags[flag_name] = value
            logger.info(f"Feature flag '{flag_name}' changed from {old_value} to {value}")
        else:
            logger.warning(f"Unknown feature flag: {flag_name}")

    def get_all_runtime_flags(self) -> Dict[str, bool]:
        """Get all current runtime flag states"""
        return self._flags.copy()

# Global singleton instance
feature_flags = FeatureFlags()