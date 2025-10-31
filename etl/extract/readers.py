"""
File readers for various data sources
"""

import pandas as pd
import glob
import datetime
import shutil
from typing import List, Dict, Union, Optional
from pathlib import Path

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger


class BaseReader:
    """Base class for all data readers"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def read(self, source: str, **kwargs) -> pd.DataFrame:
        """Base read method to be implemented by subclasses"""
        raise NotImplementedError


class CSVReader(BaseReader):
    """Standardized CSV reader for solar plant data"""
    
    def read(
        self, 
        source: str, 
        sep: str = None,
        decimal: str = None,
        header: int = None,
        skiprows: List[int] = None,
        datetime_col: str = 'DateTime',
        parse_dates: bool = True,
        dayfirst: bool = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Read CSV file with solar plant data standards
        
        Args:
            source: Path to CSV file
            sep: Column separator
            decimal: Decimal separator
            header: Header row number
            skiprows: Rows to skip
            datetime_col: Name of datetime column
            parse_dates: Whether to parse dates
            dayfirst: Day first in date parsing
            **kwargs: Additional pandas read_csv parameters
        
        Returns:
            DataFrame with datetime index
        """
        file_settings = self.config.get_file_settings()
        
        # Use config defaults if not specified
        sep = sep or file_settings.get('separator', ';')
        decimal = decimal or file_settings.get('decimal', ',')
        header = header if header is not None else file_settings.get('header_row', 0)
        skiprows = skiprows or file_settings.get('skip_rows', [1])
        dayfirst = dayfirst if dayfirst is not None else file_settings.get('date_first', True)
        
        self.logger.info(f"Reading CSV file: {source}")
        
        try:
            df = pd.read_csv(
                source,
                sep=sep,
                decimal=decimal,
                header=header,
                skiprows=skiprows,
                parse_dates=parse_dates,
                dayfirst=dayfirst,
                **kwargs
            )
            
            # Set datetime index if datetime column exists
            if datetime_col in df.columns:
                df.index = pd.to_datetime(df[datetime_col], dayfirst=dayfirst)
                df = df.drop([datetime_col], axis=1)
            
            self.logger.info(f"Successfully read {len(df)} rows from {source}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to read CSV file {source}: {str(e)}")
            raise


class WebPortalReader(BaseReader):
    """Reader for web portal exported data"""
    
    def read(
        self, 
        source: str, 
        version: int = 2,
        **kwargs
    ) -> pd.DataFrame:
        """
        Read web portal exported data with proper datetime handling
        
        Args:
            source: Path to file
            version: Portal version (affects datetime column name)
            **kwargs: Additional parameters
        
        Returns:
            DataFrame with datetime index
        """
        self.logger.info(f"Reading web portal data: {source}")
        
        try:
            file_settings = self.config.get_file_settings()
            
            df = pd.read_csv(
                source,
                sep=file_settings.get('separator', ';'),
                header=file_settings.get('header_row', 0),
                skiprows=file_settings.get('skip_rows', [1]),
                decimal=file_settings.get('decimal', ','),
                **kwargs
            )
            
            # Handle different portal versions
            if version == 3:
                df = df.set_index(pd.to_datetime(df['Date Time'], dayfirst=True))
                df = df.drop(['Date Time'], axis=1)
            elif version == 2:
                df = df.set_index(pd.to_datetime(df['DateTime'], dayfirst=True))
                df = df.drop(['DateTime'], axis=1)
            elif version == 1:
                df.index = pd.to_datetime(
                    df['Date'] + ' ' + df['Time'], 
                    dayfirst=True
                )
                df = df.drop(['Date', 'Time'], axis=1)
            
            self.logger.info(f"Successfully read web portal data: {len(df)} rows")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to read web portal data {source}: {str(e)}")
            raise


class MultiFileReader(BaseReader):
    """Reader for multiple files in a directory"""
    
    def read_directory(
        self,
        source_dir: str,
        file_pattern: str = "*.csv",
        reader_class: BaseReader = None,
        **reader_kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Read multiple files from a directory
        
        Args:
            source_dir: Source directory path
            file_pattern: File pattern to match
            reader_class: Reader class to use
            **reader_kwargs: Arguments for the reader
        
        Returns:
            Dictionary mapping filenames to DataFrames
        """
        reader = reader_class or CSVReader(self.config)
        source_path = Path(source_dir)
        files = list(source_path.glob(file_pattern))
        
        self.logger.info(f"Found {len(files)} files matching pattern '{file_pattern}'")
        
        dataframes = {}
        for file_path in files:
            try:
                df = reader.read(str(file_path), **reader_kwargs)
                dataframes[file_path.name] = df
            except Exception as e:
                self.logger.warning(f"Failed to read {file_path}: {str(e)}")
        
        return dataframes