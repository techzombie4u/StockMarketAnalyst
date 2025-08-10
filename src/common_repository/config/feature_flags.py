
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
                    "debug_mode": False
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
        """Set a feature flag value"""
        self._flags[flag_name] = value
        self._save_flags(self._flags)

# Global singleton instance
feature_flags = FeatureFlags()
