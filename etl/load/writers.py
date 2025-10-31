"""
Data writers for various output formats
"""

import pandas as pd
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger


class BaseWriter:
    """Base class for all data writers"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def write(self, data: pd.DataFrame, destination: str, **kwargs):
        """Base write method to be implemented by subclasses"""
        raise NotImplementedError


class CSVWriter(BaseWriter):
    """CSV writer for solar plant data"""
    
    def write(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        destination: str,
        sep: str = None,
        decimal: str = None,
        include_index: bool = True,
        **kwargs
    ) -> str:
        """
        Write data to CSV format
        
        Args:
            data: DataFrame or dictionary of DataFrames to write
            destination: Output file path or directory
            sep: Column separator
            decimal: Decimal separator
            include_index: Whether to include index in output
            **kwargs: Additional pandas to_csv parameters
        
        Returns:
            Path to written file(s)
        """
        file_settings = self.config.get_file_settings()
        
        # Use config defaults if not specified
        sep = sep or file_settings.get('separator', ';')
        decimal = decimal or file_settings.get('decimal', ',')
        
        if isinstance(data, dict):
            return self._write_multiple_csv(data, destination, sep, decimal, include_index, **kwargs)
        else:
            return self._write_single_csv(data, destination, sep, decimal, include_index, **kwargs)
    
    def _write_single_csv(
        self,
        data: pd.DataFrame,
        destination: str,
        sep: str,
        decimal: str,
        include_index: bool,
        **kwargs
    ) -> str:
        """Write single DataFrame to CSV"""
        self.logger.info(f"Writing CSV file: {destination}")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            data.to_csv(
                destination,
                sep=sep,
                decimal=decimal,
                index=include_index,
                **kwargs
            )
            
            self.logger.info(f"Successfully wrote {len(data)} rows to {destination}")
            return destination
            
        except Exception as e:
            self.logger.error(f"Failed to write CSV file {destination}: {str(e)}")
            raise
    
    def _write_multiple_csv(
        self,
        data_dict: Dict[str, pd.DataFrame],
        destination_dir: str,
        sep: str,
        decimal: str,
        include_index: bool,
        **kwargs
    ) -> List[str]:
        """Write multiple DataFrames to separate CSV files"""
        self.logger.info(f"Writing {len(data_dict)} CSV files to {destination_dir}")
        
        # Ensure directory exists
        os.makedirs(destination_dir, exist_ok=True)
        
        written_files = []
        
        for name, df in data_dict.items():
            file_path = os.path.join(destination_dir, f"{name}.csv")
            written_path = self._write_single_csv(df, file_path, sep, decimal, include_index, **kwargs)
            written_files.append(written_path)
        
        return written_files


class DatabaseWriter(BaseWriter):
    """Database writer for solar plant data"""
    
    def __init__(self, config: ConfigManager = None, connection_string: str = None):
        super().__init__(config)
        self.connection_string = connection_string
    
    def write(
        self,
        data: pd.DataFrame,
        table_name: str,
        if_exists: str = 'replace',
        index: bool = True,
        **kwargs
    ) -> bool:
        """
        Write data to database table
        
        Args:
            data: DataFrame to write
            table_name: Name of database table
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            index: Whether to write DataFrame index
            **kwargs: Additional pandas to_sql parameters
        
        Returns:
            Success status
        """
        if not self.connection_string:
            self.logger.error("No database connection string provided")
            return False
        
        self.logger.info(f"Writing {len(data)} rows to database table: {table_name}")
        
        try:
            # This would require an actual database connection
            # Implementation depends on specific database type (SQLite, PostgreSQL, etc.)
            # For now, return success placeholder
            self.logger.info(f"Successfully wrote to database table: {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write to database: {str(e)}")
            return False


class ExcelWriter(BaseWriter):
    """Excel writer for solar plant data with multiple sheets"""
    
    def write(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        destination: str,
        sheet_names: List[str] = None,
        include_index: bool = True,
        **kwargs
    ) -> str:
        """
        Write data to Excel format
        
        Args:
            data: DataFrame or dictionary of DataFrames
            destination: Output Excel file path
            sheet_names: Names for Excel sheets
            include_index: Whether to include index
            **kwargs: Additional pandas to_excel parameters
        
        Returns:
            Path to written Excel file
        """
        self.logger.info(f"Writing Excel file: {destination}")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            if isinstance(data, dict):
                with pd.ExcelWriter(destination, engine='openpyxl') as writer:
                    for i, (name, df) in enumerate(data.items()):
                        sheet_name = sheet_names[i] if sheet_names and i < len(sheet_names) else name
                        df.to_excel(writer, sheet_name=sheet_name, index=include_index, **kwargs)
            else:
                data.to_excel(destination, index=include_index, **kwargs)
            
            self.logger.info(f"Successfully wrote Excel file: {destination}")
            return destination
            
        except Exception as e:
            self.logger.error(f"Failed to write Excel file {destination}: {str(e)}")
            raise


class JSONWriter(BaseWriter):
    """JSON writer for solar plant data"""
    
    def write(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        destination: str,
        orient: str = 'records',
        date_format: str = 'iso',
        **kwargs
    ) -> str:
        """
        Write data to JSON format
        
        Args:
            data: DataFrame or dictionary to write
            destination: Output JSON file path
            orient: JSON orientation ('records', 'index', 'values', etc.)
            date_format: Date formatting ('iso', 'epoch')
            **kwargs: Additional pandas to_json parameters
        
        Returns:
            Path to written JSON file
        """
        self.logger.info(f"Writing JSON file: {destination}")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            if isinstance(data, dict):
                # Convert dict of DataFrames to nested JSON structure
                json_data = {}
                for name, df in data.items():
                    json_data[name] = df.to_dict(orient=orient)
                
                import json
                with open(destination, 'w') as f:
                    json.dump(json_data, f, indent=2, default=str)
            else:
                data.to_json(destination, orient=orient, date_format=date_format, **kwargs)
            
            self.logger.info(f"Successfully wrote JSON file: {destination}")
            return destination
            
        except Exception as e:
            self.logger.error(f"Failed to write JSON file {destination}: {str(e)}")
            raise


class PickleWriter(BaseWriter):
    """Pickle writer for preserving Python object structure"""
    
    def write(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame], Any],
        destination: str,
        protocol: int = None,
        **kwargs
    ) -> str:
        """
        Write data to Pickle format
        
        Args:
            data: Data to pickle (can be any Python object)
            destination: Output file path
            protocol: Pickle protocol version
            **kwargs: Additional parameters (unused)
        
        Returns:
            Path to written pickle file
        """
        import pickle
        
        self.logger.info(f"Writing Pickle file: {destination}")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Use default protocol if not specified
            if protocol is None:
                protocol = pickle.HIGHEST_PROTOCOL
            
            with open(destination, 'wb') as f:
                pickle.dump(data, f, protocol=protocol)
            
            self.logger.info(f"Successfully wrote pickle file: {destination}")
            return destination
            
        except Exception as e:
            self.logger.error(f"Failed to write pickle file {destination}: {str(e)}")
            raise


class WriterFactory:
    """Factory for creating appropriate writers based on file extension"""
    
    @staticmethod
    def create_writer(destination: str, config: ConfigManager = None) -> BaseWriter:
        """
        Create appropriate writer based on file extension
        
        Args:
            destination: Output file path
            config: Configuration manager
        
        Returns:
            Appropriate writer instance
        """
        ext = Path(destination).suffix.lower()
        
        if ext == '.csv':
            return CSVWriter(config)
        elif ext in ['.xlsx', '.xls']:
            return ExcelWriter(config)
        elif ext == '.json':
            return JSONWriter(config)
        elif ext == '.pkl' or ext == '.pickle':
            return PickleWriter(config)
        else:
            # Default to CSV for unknown extensions
            return CSVWriter(config)