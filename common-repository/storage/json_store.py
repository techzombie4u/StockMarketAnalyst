
"""
JSON-based Storage Implementation
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from common_repository.utils.error_handler import ErrorContext, safe_execute

logger = logging.getLogger(__name__)

class JSONStore:
    """JSON file-based storage implementation"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self) -> None:
        """Ensure the base directory exists"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, 'tracking'), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, 'backup'), exist_ok=True)
    
    def get_file_path(self, key: str) -> str:
        """Get full file path for a key"""
        # Handle nested keys (e.g., 'tracking/predictions')
        if '/' in key:
            return os.path.join(self.base_path, f"{key}.json")
        else:
            return os.path.join(self.base_path, f"{key}.json")
    
    def save(self, key: str, data: Any, create_backup: bool = True) -> bool:
        """Save data to JSON file"""
        file_path = self.get_file_path(key)
        
        try:
            # Create backup if file exists and backup is requested
            if create_backup and os.path.exists(file_path):
                self._create_backup(file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Saved data to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {str(e)}")
            return False
    
    def load(self, key: str, default: Any = None) -> Any:
        """Load data from JSON file"""
        file_path = self.get_file_path(key)
        
        try:
            if not os.path.exists(file_path):
                logger.debug(f"File not found: {file_path}, returning default")
                return default
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                if not content:
                    logger.warning(f"Empty file: {file_path}, returning default")
                    return default
                
                data = json.loads(content)
                logger.debug(f"Loaded data from {file_path}")
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {str(e)}")
            # Try to restore from backup
            if self._restore_from_backup(file_path):
                return self.load(key, default)
            return default
            
        except Exception as e:
            logger.error(f"Error loading from {file_path}: {str(e)}")
            return default
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        file_path = self.get_file_path(key)
        return os.path.exists(file_path)
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        file_path = self.get_file_path(key)
        
        try:
            if os.path.exists(file_path):
                # Create backup before deletion
                self._create_backup(file_path)
                os.remove(file_path)
                logger.info(f"Deleted {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {str(e)}")
            return False
    
    def list_keys(self, pattern: str = None) -> List[str]:
        """List all keys (file names without .json extension)"""
        try:
            keys = []
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.json'):
                        # Get relative path from base_path
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.base_path)
                        key = rel_path[:-5]  # Remove .json extension
                        
                        if pattern is None or pattern in key:
                            keys.append(key)
            
            return sorted(keys)
            
        except Exception as e:
            logger.error(f"Error listing keys: {str(e)}")
            return []
    
    def get_file_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        file_path = self.get_file_path(key)
        
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'path': file_path
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return None
    
    def _create_backup(self, file_path: str) -> bool:
        """Create backup of a file"""
        try:
            backup_dir = os.path.join(self.base_path, 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{filename.replace('.json', '')}_{timestamp}.json"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Copy file to backup
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            
            # Clean old backups (keep only last 5)
            self._cleanup_old_backups(backup_dir, filename)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {str(e)}")
            return False
    
    def _restore_from_backup(self, file_path: str) -> bool:
        """Restore file from most recent backup"""
        try:
            backup_dir = os.path.join(self.base_path, 'backup')
            filename = os.path.basename(file_path)
            prefix = filename.replace('.json', '')
            
            # Find most recent backup
            backup_files = []
            for backup_file in os.listdir(backup_dir):
                if backup_file.startswith(prefix + '_') and backup_file.endswith('.json'):
                    backup_path = os.path.join(backup_dir, backup_file)
                    backup_files.append((backup_path, os.path.getmtime(backup_path)))
            
            if not backup_files:
                logger.warning(f"No backup found for {filename}")
                return False
            
            # Get most recent backup
            most_recent = max(backup_files, key=lambda x: x[1])
            backup_path = most_recent[0]
            
            # Restore from backup
            import shutil
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path} from backup {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup for {file_path}: {str(e)}")
            return False
    
    def _cleanup_old_backups(self, backup_dir: str, filename: str, keep_count: int = 5) -> None:
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            prefix = filename.replace('.json', '')
            backup_files = []
            
            for backup_file in os.listdir(backup_dir):
                if backup_file.startswith(prefix + '_') and backup_file.endswith('.json'):
                    backup_path = os.path.join(backup_dir, backup_file)
                    backup_files.append((backup_path, os.path.getmtime(backup_path)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Delete old backups
            for backup_path, _ in backup_files[keep_count:]:
                os.remove(backup_path)
                logger.debug(f"Deleted old backup: {backup_path}")
                
        except Exception as e:
            logger.error(f"Error cleaning up backups: {str(e)}")

# Global instance
json_store = JSONStore()
