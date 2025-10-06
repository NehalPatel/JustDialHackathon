"""
Configuration Manager for Video Auto-Moderation System
Handles application configuration, settings persistence, and validation
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "moderation_config.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "moderation_settings": {
                "nudity_sensitivity": "moderate",  # lenient, moderate, strict
                "fraud_sensitivity": "strict",     # lenient, moderate, strict
                "copyright_threshold": 60,         # 0-100 percentage
                "reject_poor_quality": False,
                "blur_faces": True,
                "blur_violence": True,
                "delete_rejected_files": False
            },
            "detection_thresholds": {
                "nudity": {
                    "lenient": 80,
                    "moderate": 60,
                    "strict": 40
                },
                "fraud": {
                    "lenient": 80,
                    "moderate": 60,
                    "strict": 40
                },
                "violence": {
                    "threshold": 70,
                    "enabled": True
                },
                "quality": {
                    "min_resolution": "480p",
                    "min_bitrate": 500,  # kbps
                    "max_compression": 80
                }
            },
            "file_settings": {
                "max_file_size": 500 * 1024 * 1024,  # 500MB
                "supported_formats": ["mp4", "mov", "avi", "wmv", "mkv", "flv", "webm"],
                "upload_timeout": 300,  # seconds
                "processing_timeout": 600  # seconds
            },
            "system_settings": {
                "max_concurrent_uploads": 5,
                "cleanup_interval": 24,  # hours
                "backup_retention": 30,  # days
                "log_level": "INFO",
                "enable_analytics": True
            },
            "ui_settings": {
                "theme": "light",
                "language": "en",
                "items_per_page": 20,
                "auto_refresh": True,
                "refresh_interval": 30  # seconds
            },
            "notification_settings": {
                "email_notifications": False,
                "webhook_url": "",
                "notify_on_approval": False,
                "notify_on_rejection": True
            },
            "metadata": {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "update_count": 0
            }
        }
        
        # Load or create configuration
        self.config = self.load_config()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_config = self._merge_configs(self.default_config, config)
                
                # Validate configuration
                if self._validate_config(merged_config):
                    return merged_config
                else:
                    self.logger.warning("Invalid configuration found, using defaults")
                    return self.default_config.copy()
            else:
                # Create default configuration file
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file"""
        try:
            if config is None:
                config = self.config
            
            # Update metadata
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            config["metadata"]["update_count"] = config["metadata"].get("update_count", 0) + 1
            
            # Create backup before saving
            self._create_backup()
            
            # Save configuration
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            self.config = config
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get setting value using dot notation
        Example: get_setting('moderation_settings.nudity_sensitivity')
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        Set setting value using dot notation
        Example: set_setting('moderation_settings.nudity_sensitivity', 'strict')
        """
        try:
            keys = key_path.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            
            # Validate and save
            if self._validate_config(self.config):
                return self.save_config()
            else:
                self.logger.error(f"Invalid value for {key_path}: {value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set setting {key_path}: {e}")
            return False
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update multiple settings at once"""
        try:
            # Create a copy of current config
            new_config = self.config.copy()
            
            # Update settings
            for key_path, value in settings.items():
                keys = key_path.split('.')
                config = new_config
                
                for key in keys[:-1]:
                    if key not in config:
                        config[key] = {}
                    config = config[key]
                
                config[keys[-1]] = value
            
            # Validate and save
            if self._validate_config(new_config):
                return self.save_config(new_config)
            else:
                self.logger.error("Invalid configuration update")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        try:
            default_config = self.default_config.copy()
            default_config["metadata"]["created_at"] = datetime.now().isoformat()
            default_config["metadata"]["update_count"] = 0
            
            return self.save_config(default_config)
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to specified path"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from specified path"""
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                self.logger.error(f"Import file does not exist: {import_path}")
                return False
            
            with open(import_file, 'r') as f:
                imported_config = json.load(f)
            
            # Validate imported configuration
            if self._validate_config(imported_config):
                return self.save_config(imported_config)
            else:
                self.logger.error("Invalid imported configuration")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def get_moderation_config(self) -> Dict[str, Any]:
        """Get moderation-specific configuration"""
        return {
            "nudity_sensitivity": self.get_setting("moderation_settings.nudity_sensitivity"),
            "fraud_sensitivity": self.get_setting("moderation_settings.fraud_sensitivity"),
            "copyright_threshold": self.get_setting("moderation_settings.copyright_threshold"),
            "reject_poor_quality": self.get_setting("moderation_settings.reject_poor_quality"),
            "blur_faces": self.get_setting("moderation_settings.blur_faces"),
            "blur_violence": self.get_setting("moderation_settings.blur_violence"),
            "delete_rejected_files": self.get_setting("moderation_settings.delete_rejected_files"),
            "thresholds": self.get_setting("detection_thresholds")
        }
    
    def get_threshold_for_sensitivity(self, detection_type: str, sensitivity: str) -> float:
        """Get threshold value for specific detection type and sensitivity"""
        try:
            thresholds = self.get_setting(f"detection_thresholds.{detection_type}")
            if isinstance(thresholds, dict) and sensitivity in thresholds:
                return float(thresholds[sensitivity])
            return 60.0  # Default threshold
        except Exception:
            return 60.0
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available configuration backups"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                try:
                    stat = backup_file.stat()
                    backups.append({
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "size": stat.st_size
                    })
                except Exception:
                    continue
            
            return sorted(backups, key=lambda x: x["created_at"], reverse=True)
            
        except Exception:
            return []
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore configuration from backup"""
        try:
            backup_file = self.backup_dir / backup_filename
            
            if not backup_file.exists():
                self.logger.error(f"Backup file does not exist: {backup_filename}")
                return False
            
            with open(backup_file, 'r') as f:
                backup_config = json.load(f)
            
            if self._validate_config(backup_config):
                return self.save_config(backup_config)
            else:
                self.logger.error("Invalid backup configuration")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Clean up old backup files"""
        try:
            cleaned = 0
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
            
            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                try:
                    if backup_file.stat().st_ctime < cutoff_time:
                        backup_file.unlink()
                        cleaned += 1
                except Exception:
                    continue
            
            return cleaned
            
        except Exception:
            return 0
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with default config"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure and values"""
        try:
            # Check required sections
            required_sections = ["moderation_settings", "detection_thresholds", "file_settings"]
            for section in required_sections:
                if section not in config:
                    return False
            
            # Validate moderation settings
            mod_settings = config.get("moderation_settings", {})
            
            # Check sensitivity values
            valid_sensitivities = ["lenient", "moderate", "strict"]
            if mod_settings.get("nudity_sensitivity") not in valid_sensitivities:
                return False
            if mod_settings.get("fraud_sensitivity") not in valid_sensitivities:
                return False
            
            # Check copyright threshold
            copyright_threshold = mod_settings.get("copyright_threshold", 0)
            if not isinstance(copyright_threshold, (int, float)) or not (0 <= copyright_threshold <= 100):
                return False
            
            # Validate boolean settings
            bool_settings = ["reject_poor_quality", "blur_faces", "blur_violence", "delete_rejected_files"]
            for setting in bool_settings:
                if setting in mod_settings and not isinstance(mod_settings[setting], bool):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _create_backup(self) -> bool:
        """Create backup of current configuration"""
        try:
            if not self.config_file.exists():
                return True
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            with open(self.config_file, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False