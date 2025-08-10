
"""
Feature Flags Configuration Loader
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

class FeatureFlags:
    def __init__(self):
        self.flags = {}
        self.load_flags()
    
    def load_flags(self):
        """Load feature flags from JSON configuration"""
        try:
            flags_path = os.path.join(os.path.dirname(__file__), 'feature_flags.json')
            with open(flags_path, 'r') as f:
                self.flags = json.load(f)
            logger.info(f"Loaded {len(self.flags)} feature flags")
        except Exception as e:
            logger.error(f"Error loading feature flags: {e}")
            # Default flags for fallback
            self.flags = {
                "enable_dynamic_confidence": True,
                "enable_real_time_trends": True,
                "enable_all_timeframes": True,
                "enable_ai_agents": False
            }
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self.flags.get(flag_name, False)
    
    def get_flag(self, flag_name: str, default=False):
        """Get feature flag value with default"""
        return self.flags.get(flag_name, default)
    
    def set_flag(self, flag_name: str, value: bool):
        """Set feature flag value (runtime only)"""
        self.flags[flag_name] = value
    
    def get_all_flags(self):
        """Get all feature flags"""
        return self.flags.copy()

# Global instance
feature_flags = FeatureFlags()
