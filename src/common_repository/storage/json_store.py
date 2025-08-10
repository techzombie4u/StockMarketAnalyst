
"""
JSON-based Storage Implementation
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class JsonStore:
    """JSON-based storage manager"""
    
    def __init__(self, storage_dir: str = "data/runtime"):
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating storage directory: {e}")
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for a key"""
        # Sanitize key to be filesystem-safe
        safe_key = "".join(c for c in key if c.isalnum() or c in "._-")
        return os.path.join(self.storage_dir, f"{safe_key}.json")
    
    def save(self, key: str, data: Any) -> bool:
        """Save data to storage"""
        try:
            file_path = self._get_file_path(key)
            
            # Add metadata
            storage_data = {
                'key': key,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved data for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data for key {key}: {e}")
            return False
    
    def load(self, key: str, default: Any = None) -> Any:
        """Load data from storage"""
        try:
            file_path = self._get_file_path(key)
            
            if not os.path.exists(file_path):
                return default
            
            with open(file_path, 'r', encoding='utf-8') as f:
                storage_data = json.load(f)
            
            # Return the actual data, not the metadata wrapper
            return storage_data.get('data', default)
            
        except Exception as e:
            logger.error(f"Error loading data for key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete data from storage"""
        try:
            file_path = self._get_file_path(key)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Deleted data for key: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting data for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in storage"""
        file_path = self._get_file_path(key)
        return os.path.exists(file_path)
    
    def list_keys(self) -> List[str]:
        """List all keys in storage"""
        try:
            if not os.path.exists(self.storage_dir):
                return []
            
            keys = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    # Remove .json extension to get the key
                    key = filename[:-5]
                    keys.append(key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []

# Global singleton instance
json_store = JsonStore()
