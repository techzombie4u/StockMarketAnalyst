
"""
Agent Outputs Repository - Manages persistence of agent execution results
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...common_repository.storage.json_store import json_store
from ...common_repository.utils.date_utils import get_ist_now

logger = logging.getLogger(__name__)

class AgentOutputsRepository:
    """Repository for managing agent execution outputs"""
    
    def __init__(self):
        self.base_path = "agents/outputs"
    
    def save_output(self, agent: str, scope: str, payload: Dict[str, Any]) -> bool:
        """Save agent output with timestamp and metadata"""
        try:
            now = get_ist_now()
            date_str = now.strftime('%Y%m%d')
            
            # Create structured output
            output_data = {
                'agent': agent,
                'scope': scope,
                'timestamp_ist': now.isoformat(),
                'timestamp_utc': datetime.utcnow().isoformat(),
                'payload': payload,
                'version': '1.0'
            }
            
            # Save to date-partitioned structure
            file_path = f"{self.base_path}/{agent}/{date_str}/{scope}.json"
            success = json_store.save(file_path, output_data)
            
            if success:
                # Also save as 'latest' for quick access
                latest_path = f"{self.base_path}/{agent}/latest/{scope}.json"
                json_store.save(latest_path, output_data)
                
            logger.info(f"Saved agent output: {agent}/{scope}")
            return success
            
        except Exception as e:
            logger.error(f"Error saving agent output: {e}")
            return False
    
    def load_latest(self, agent: str, scope: str) -> Optional[Dict[str, Any]]:
        """Load latest output for agent and scope"""
        try:
            file_path = f"{self.base_path}/{agent}/latest/{scope}.json"
            data = json_store.load(file_path)
            
            if data:
                logger.debug(f"Loaded latest output: {agent}/{scope}")
                return data
            else:
                logger.debug(f"No latest output found: {agent}/{scope}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading latest output: {e}")
            return None
    
    def list_runs(self, agent: str, scope: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent runs for agent and scope"""
        try:
            runs = []
            
            # Get dates from directory structure
            agent_path = f"{self.base_path}/{agent}"
            dates = self._get_available_dates(agent_path)
            
            # Collect runs from most recent dates
            for date in sorted(dates, reverse=True):
                if len(runs) >= limit:
                    break
                    
                date_path = f"{agent_path}/{date}/{scope}.json"
                data = json_store.load(date_path)
                
                if data:
                    # Add summary info
                    run_summary = {
                        'date': date,
                        'timestamp': data.get('timestamp_ist'),
                        'verdict': data.get('payload', {}).get('verdict', 'UNKNOWN'),
                        'confidence': data.get('payload', {}).get('confidence', 0),
                        'agent': agent,
                        'scope': scope
                    }
                    runs.append(run_summary)
            
            return runs[:limit]
            
        except Exception as e:
            logger.error(f"Error listing runs: {e}")
            return []
    
    def _get_available_dates(self, agent_path: str) -> List[str]:
        """Get available date directories for an agent"""
        try:
            # This would need to be implemented based on json_store capabilities
            # For now, return current date as fallback
            return [datetime.now().strftime('%Y%m%d')]
        except Exception as e:
            logger.error(f"Error getting available dates: {e}")
            return []
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get statistics for agent executions"""
        try:
            # Basic stats - would be enhanced with actual data
            return {
                'total_runs': 0,
                'last_run': None,
                'success_rate': 100.0,
                'avg_confidence': 75.0
            }
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {}

# Global repository instance
agent_outputs_repo = AgentOutputsRepository()
