"""
Configuration management for the ETL pipeline
"""

import pandas as pd
from typing import Dict, Any
import os


class ConfigManager:
    """Centralized configuration management for solar plant data processing"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or set defaults"""
        if self.config_path and os.path.exists(self.config_path):
            # Load from CSV or other format
            self._config = self._load_from_file()
        else:
            self._config = self._get_default_config()
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from CSV file"""
        try:
            df = pd.read_csv(self.config_path)
            return df.set_index(df.columns[0]).to_dict('dict')
        except Exception:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration settings"""
        return {
            'file_settings': {
                'separator': ';',
                'decimal': ',',
                'datetime_format': '%d/%m/%Y %H:%M',
                'header_row': 0,
                'skip_rows': [1],
                'date_first': True
            },
            'data_cleaning': {
                'irradiance_max': 1500,
                'irradiance_min': 0,
                'temperature_max': 70,
                'temperature_min': -20,
                'frozen_threshold': 4
            },
            'processing': {
                'min_irradiance': 50,
                'aggregation_methods': ['sum', 'mean', 'max', 'min'],
                'default_resolution': 5  # minutes
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_file_settings(self) -> Dict[str, Any]:
        """Get file reading settings"""
        return self.get('file_settings', {})
    
    def get_cleaning_params(self) -> Dict[str, Any]:
        """Get data cleaning parameters"""
        return self.get('data_cleaning', {})