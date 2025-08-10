
"""
AI Agents Security and Safety Module
"""

import re
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SafetyManager:
    """Handles input sanitization, PII redaction, and safety checks"""
    
    def __init__(self):
        self.pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{10,12}\b',  # Phone numbers
            r'\bAPI[_\s]*KEY[_\s]*[:\s]*[A-Za-z0-9]{20,}\b',  # API keys
            r'\b[A-Z0-9]{20,}\b'  # Generic tokens
        ]
        
        self.dangerous_keywords = [
            'delete', 'drop', 'truncate', 'remove', 'kill',
            'leverage', 'margin', 'position_size', 'account'
        ]
    
    def sanitize_input(self, data: Dict[str, Any], redactions: List[str]) -> Dict[str, Any]:
        """Sanitize input data by removing PII and dangerous content"""
        try:
            sanitized = json.loads(json.dumps(data))  # Deep copy
            
            if 'api_keys' in redactions or 'credentials' in redactions:
                sanitized = self._redact_credentials(sanitized)
            
            if 'pii' in redactions or 'personal_info' in redactions:
                sanitized = self._redact_pii(sanitized)
                
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {e}")
            return data
    
    def _redact_credentials(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact API keys and credentials"""
        if isinstance(data, dict):
            for key, value in data.items():
                if 'key' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                    data[key] = '[REDACTED]'
                elif isinstance(value, (dict, list)):
                    data[key] = self._redact_credentials(value)
        elif isinstance(data, list):
            return [self._redact_credentials(item) for item in data]
        
        return data
    
    def _redact_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact personally identifiable information"""
        if isinstance(data, str):
            for pattern in self.pii_patterns:
                data = re.sub(pattern, '[PII_REDACTED]', data, flags=re.IGNORECASE)
        elif isinstance(data, dict):
            for key, value in data.items():
                data[key] = self._redact_pii(value)
        elif isinstance(data, list):
            return [self._redact_pii(item) for item in data]
            
        return data
    
    def check_safety(self, input_data: Dict[str, Any], safety_config: Dict[str, Any]) -> bool:
        """Check if input passes safety requirements"""
        try:
            # Check for dangerous keywords
            input_str = json.dumps(input_data).lower()
            for keyword in self.dangerous_keywords:
                if keyword in input_str and safety_config.get('disallow_position_sizing', True):
                    logger.warning(f"Dangerous keyword detected: {keyword}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            return False
    
    def truncate_tokens(self, data: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Truncate data to fit within token limits"""
        try:
            data_str = json.dumps(data)
            if len(data_str) <= max_tokens * 4:  # Rough estimate: 4 chars per token
                return data
            
            # Truncate large arrays first
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 10:
                        data[key] = value[:10] + ["... truncated"]
                        
            return data
            
        except Exception as e:
            logger.error(f"Error truncating tokens: {e}")
            return data

# Global instance
safety_manager = SafetyManager()
