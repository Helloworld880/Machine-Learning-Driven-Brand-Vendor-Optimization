import os
import json
from datetime import datetime

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "app": {
                "name": "Vendor Performance Dashboard",
                "version": "1.0.0",
                "debug": True,
                "port": 8501
            },
            "database": {
                "path": "Data layer/vendors.db",
                "backup_path": "Data layer/backup",
                "backup_interval_days": 7
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": ""
            },
            "security": {
                "session_timeout_minutes": 60,
                "password_min_length": 8,
                "max_login_attempts": 5
            },
            "analytics": {
                "performance_threshold": 70,
                "risk_threshold_high": 70,
                "risk_threshold_medium": 40,
                "auto_refresh_minutes": 5
            },
            "reports": {
                "auto_generate": True,
                "default_format": "PDF",
                "save_path": "reports/generated"
            }
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default