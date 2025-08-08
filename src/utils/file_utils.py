
import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def load_json_safe(path: str, default: Any = None) -> Any:
    """
    Safely load JSON file with fallback to default value
    """
    if default is None:
        default = {}
    
    try:
        if not os.path.exists(path):
            logger.debug(f"File not found: {path}, using default")
            return default
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Empty file: {path}, using default")
                return default
                
            return json.loads(content)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {path}: {e}")
        return default
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return default

def save_json_safe(path: str, data: Any) -> bool:
    """
    Safely save JSON file with error handling
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving {path}: {e}")
        return False

def ensure_file_exists(path: str, default_content: Any = None) -> bool:
    """
    Ensure file exists with default content
    """
    if default_content is None:
        default_content = {}
        
    try:
        if not os.path.exists(path):
            return save_json_safe(path, default_content)
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring file exists {path}: {e}")
        return False
