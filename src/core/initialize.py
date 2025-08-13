
#!/usr/bin/env python3
"""
System Initialization Module
Initializes all system components and ensures proper startup
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def initialize_application():
    """Initialize the complete application"""
    try:
        logger.info("🔧 Initializing Fusion Stock Analyst Application")
        
        # Create required directories
        create_required_directories()
        
        # Initialize data files
        initialize_data_files()
        
        # Initialize models directory
        initialize_models_directory()
        
        # Set up Python path
        setup_python_path()
        
        logger.info("✅ Application initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Application initialization failed: {str(e)}")
        return False

def create_required_directories():
    """Create all required directories"""
    directories = [
        "data/fixtures",
        "data/persistent", 
        "data/cache",
        "data/historical/downloaded_historical_data",
        "data/kpi",
        "data/agents",
        "data/tracking",
        "models_trained",
        "models_trained/scalers",
        "logs",
        "web/static/css",
        "web/static/js",
        "web/templates"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"✅ Directory created/verified: {directory}")

def initialize_data_files():
    """Initialize essential data files with defaults if they don't exist"""
    
    # KPI metrics
    kpi_metrics_path = "data/kpi/kpi_metrics.json"
    if not os.path.exists(kpi_metrics_path):
        default_kpi = {
            "metrics": {
                "total_signals": 0,
                "active_positions": 0,
                "portfolio_value": 100000.0,
                "daily_pnl": 0.0,
                "success_rate": 0.0,
                "sharpe_ratio": 0.0
            },
            "last_updated": datetime.now().isoformat(),
            "timeframes": {
                "1D": {"signals": 0, "accuracy": 0.0},
                "5D": {"signals": 0, "accuracy": 0.0},
                "10D": {"signals": 0, "accuracy": 0.0},
                "All": {"signals": 0, "accuracy": 0.0}
            }
        }
        
        with open(kpi_metrics_path, 'w') as f:
            json.dump(default_kpi, f, indent=2)
        logger.info(f"✅ Created default KPI metrics: {kpi_metrics_path}")
    
    # Pins
    pins_path = "data/persistent/pins.json"
    if not os.path.exists(pins_path):
        default_pins = {
            "pinned_items": [],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(pins_path, 'w') as f:
            json.dump(default_pins, f, indent=2)
        logger.info(f"✅ Created default pins: {pins_path}")
    
    # Locks
    locks_path = "data/persistent/locks.json"
    if not os.path.exists(locks_path):
        default_locks = {
            "locked_items": [],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(locks_path, 'w') as f:
            json.dump(default_locks, f, indent=2)
        logger.info(f"✅ Created default locks: {locks_path}")
    
    # Agents registry
    agents_registry_path = "data/agents/registry.json"
    if not os.path.exists(agents_registry_path):
        default_agents = {
            "agents": [
                {
                    "id": "equity_analyzer",
                    "name": "Equity Analyzer",
                    "type": "analysis",
                    "status": "active",
                    "last_run": datetime.now().isoformat()
                },
                {
                    "id": "options_strategist", 
                    "name": "Options Strategist",
                    "type": "strategy",
                    "status": "active",
                    "last_run": datetime.now().isoformat()
                }
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(agents_registry_path, 'w') as f:
            json.dump(default_agents, f, indent=2)
        logger.info(f"✅ Created default agents registry: {agents_registry_path}")

def initialize_models_directory():
    """Initialize models directory structure"""
    models_dir = "models_trained"
    scalers_dir = os.path.join(models_dir, "scalers")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(scalers_dir, exist_ok=True)
    
    # Create model registry
    registry_path = os.path.join(models_dir, "model_registry.json")
    if not os.path.exists(registry_path):
        registry = {
            "models": {},
            "last_training": {},
            "performance_metrics": {},
            "created": datetime.now().isoformat()
        }
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        logger.info(f"✅ Created model registry: {registry_path}")

def setup_python_path():
    """Set up Python path for imports"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(current_dir, '..', '..')
    src_dir = os.path.join(root_dir, 'src')
    
    # Add paths if not already present
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    logger.debug("✅ Python path configured for imports")

def initialize_system():
    """Legacy function name for backward compatibility"""
    return initialize_application()

if __name__ == "__main__":
    # Allow running this module directly for initialization
    logging.basicConfig(level=logging.INFO)
    success = initialize_application()
    sys.exit(0 if success else 1)
