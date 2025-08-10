
"""
Rate Limiting Module for AI Agents
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Per-agent rate limiter with QPM (queries per minute) limits"""
    
    def __init__(self):
        self.requests = defaultdict(deque)  # agent_name -> deque of timestamps
        self.limits = {}  # agent_name -> qpm_limit
        
    def set_limit(self, agent_name: str, qpm_limit: int):
        """Set rate limit for an agent"""
        self.limits[agent_name] = qpm_limit
        logger.info(f"Set rate limit for {agent_name}: {qpm_limit} QPM")
    
    def is_allowed(self, agent_name: str) -> bool:
        """Check if request is allowed under rate limit"""
        try:
            now = time.time()
            limit = self.limits.get(agent_name, 6)  # Default 6 QPM
            
            # Clean old requests (older than 1 minute)
            requests_queue = self.requests[agent_name]
            while requests_queue and requests_queue[0] < now - 60:
                requests_queue.popleft()
            
            # Check if under limit
            if len(requests_queue) < limit:
                requests_queue.append(now)
                return True
            else:
                logger.warning(f"Rate limit exceeded for {agent_name}: {len(requests_queue)}/{limit}")
                return False
                
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            return True  # Allow on error
    
    def get_reset_time(self, agent_name: str) -> Optional[datetime]:
        """Get when rate limit will reset"""
        try:
            requests_queue = self.requests[agent_name]
            if requests_queue:
                oldest_request = requests_queue[0]
                return datetime.fromtimestamp(oldest_request + 60)
            return None
        except Exception as e:
            logger.error(f"Error getting reset time: {e}")
            return None

# Global instance
rate_limiter = RateLimiter()
