"""
Core consolidated functions for solar plant data analytics

This module contains consolidated versions of commonly used functions,
replacing redundant implementations across the codebase.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
import datetime
import glob
import os

from .utils.config import ConfigManager
from .utils.logging import setup_logger
from .utils.helpers import column_filter, column_delete, aggregate_dataframe
from .extract.readers import CSVReader, WebPortalReader
from .transform.cleaners import DataCleaner, IrradianceCleaner, WorkingChannelDetector
from .transform.processors import DataProcessor, MultiAzimuthProcessor, FaultDetector
from .transform.aggregators import DataAggregator, PlantLevelAggregator
from .load.writers import WriterFactory
from .load.exporters import ReportExporter, DataExporter


class SolarPlantDataProcessor:
    """
    Main class for processing solar plant data using ETL pipeline
    
    Consolidates functionality from multiple legacy classes:
    - report_Initial_Data_Clean
    - readFiles
    - update_DB
    - local_DB
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
        
        # Initialize ETL components
        self.reader = CSVReader(self.config)
        self.web_reader = WebPortalReader(self.config)
        self.cleaner = DataCleaner(self.config)
        self.irr_cleaner = IrradianceCleaner(self.config)
        self.processor = DataProcessor(self.config)
        self.aggregator = DataAggregator(self.config)
        self.exporter = DataExporter(self.config)
        
        # Data storage
        self.raw_data = {}
        self.cleaned_data = {}
        self.processed_data = {}
        
    def load_project_parameters(self, project: str) -> Dict[str, Any]:
        """
        Load project-specific parameters
        
        Args:
            project: Project name
        
        Returns:
            Dictionary of project parameters
        """
        self.logger.info(f"Loading parameters for project: {project}")
        
        # This would load from configuration files
        # For now, return basic structure
        default_params = {
            'project': project,
            'min_irradiance': 50,
            'module_capacity': 400,  # Watts
            'modules_per_string': 20,
            'string_dc_capacity': 8.0  # kW
        }
        
        return default_params
    
    def read_files_by_period(
        self,
        source_dir: str,
        project: str,
        year: int,
        month: int,
        data_types: List[str],
        keywords: Dict[str, str],
        partial_month: bool = False,
        first_day: int = 1,
        last_day: int = 31
    ) -> Dict[str, pd.DataFrame]:
        """
        Read and consolidate files for a specific time period
        
        Replaces the legacy readFiles class functionality
        
        Args:
            source_dir: Source directory containing data files
            project: Project name
            year: Target year
            month: Target month
            data_types: List of data types to read
            keywords: Keywords for filtering columns
            partial_month: Whether to read partial month
            first_day: First day if partial month
            last_day: Last day if partial month
        
        Returns:
            Dictionary of consolidated DataFrames by data type
        """
        self.logger.info(f"Reading files for {project} {year}/{month:02d}")
        
        consolidated_data = {}
        
        for data_type in data_types:
            try:
                # Find files for this data type
                file_pattern = f"*{data_type}*.csv"
                files = self._find_files_by_date(
                    source_dir, year, month, data_type, partial_month, first_day, last_day
                )
                
                if not files:
                    self.logger.warning(f"No files found for {data_type}")
                    continue
                
                # Read and concatenate files
                dataframes = []
                for file_path in files:
                    try:
                        df = self.reader.read(file_path)
                        dataframes.append(df)
                    except Exception as e:
                        self.logger.warning(f"Failed to read {file_path}: {str(e)}")
                
                if dataframes:
                    # Concatenate all files for this data type
                    combined_df = pd.concat(dataframes, ignore_index=False, sort=True)
                    combined_df = combined_df.sort_index()
                    
                    # Apply keyword filtering
                    if data_type in keywords and keywords[data_type] != 'None':
                        combined_df = column_filter(combined_df, keywords[data_type])
                    
                    # Apply data-specific column filtering
                    combined_df = self._apply_data_type_filters(combined_df, data_type)
                    
                    consolidated_data[data_type] = combined_df
                    
            except Exception as e:
                self.logger.error(f"Error processing {data_type}: {str(e)}")
        
        self.raw_data.update(consolidated_data)
        return consolidated_data
    
    def _find_files_by_date(
        self,
        source_dir: str,
        year: int,
        month: int,
        container: str,
        partial_month: bool,
        first_day: int,
        last_day: int
    ) -> List[str]:
        """Find files matching date criteria"""
        
        all_files = glob.glob(os.path.join(source_dir, "*.csv"))
        valid_files = []
        
        for file_path in all_files:
            if container in file_path and 'change' not in file_path:
                try:
                    # Extract date from filename
                    file_date = self._extract_date_from_filename(file_path)
                    if file_date and file_date.year == year and file_date.month == month:
                        if partial_month:
                            if first_day <= file_date.day <= last_day:
                                valid_files.append(file_path)
                        else:
                            valid_files.append(file_path)
                except Exception:
                    continue
        
        return valid_files
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime.datetime]:
        """Extract date from filename"""
        import re
        
        # Pattern for YYYYMMDD
        pattern = r'(\d{8})'
        match = re.search(pattern, filename)
        
        if match:
            try:
                return datetime.datetime.strptime(match.group(1), '%Y%m%d')
            except ValueError:
                pass
        
        return None
    
    def _apply_data_type_filters(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Apply data-type specific column filters"""
        
        if data_type == 'pyran':
            # Remove unwanted columns for pyranometer data
            exclude_patterns = ['AC', 'CEWE', 'Meter', 'Station', 'WR', 'nION', 'oION']
            for pattern in exclude_patterns:
                df = column_delete(df, pattern)
        
        elif data_type == 'cbCurr':
            # Remove unwanted columns for combiner box current
            exclude_patterns = ['total', 'IV', 'DC', 're', 'Capacity']
            for pattern in exclude_patterns:
                df = column_delete(df, pattern)
        
        elif data_type == 'cbVolt':
            # Remove unwanted columns for combiner box voltage
            exclude_patterns = ['Meter', 'WR']
            for pattern in exclude_patterns:
                df = column_delete(df, pattern)
        
        return df
    
    def perform_initial_data_cleaning(
        self,
        data: Dict[str, pd.DataFrame],
        params: Dict[str, Any],
        keywords: Dict[str, str],
        apply_temp_correction: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Perform initial data cleaning on raw data
        
        Replaces the legacy report_Initial_Data_Clean class functionality
        
        Args:
            data: Dictionary of raw DataFrames
            params: Project parameters
            keywords: Column keywords
            apply_temp_correction: Whether to apply temperature correction
        
        Returns:
            Dictionary of cleaned data
        """
        self.logger.info("Performing initial data cleaning")
        
        cleaned_data = {}
        
        # Process irradiance data (GTI and GHI)
        if 'pyran' in data:
            gti_raw = column_filter(data['pyran'], keywords.get('gti', 'gti'))
            ghi_raw = column_filter(data['pyran'], keywords.get('ghi', 'ghi'))
            
            # Clean irradiance data
            if params.get('project') == 'Scaldia':
                # Special processing for Scaldia project
                ibv_gti = self._clean_irradiance_scaldia(gti_raw)
            else:
                # Standard irradiance cleaning
                ibv_gti = self.irr_cleaner.clean_irradiance_advanced(gti_raw)
                if isinstance(ibv_gti, tuple):
                    ibv_gti = ibv_gti[0]  # Extract series from tuple
            
            # Apply conversion factor
            ibv_gti = ibv_gti / 12  # Convert to Wh
            
            # Process GHI similarly
            ibv_ghi = self.irr_cleaner.clean_irradiance_advanced(ghi_raw)
            if isinstance(ibv_ghi, tuple):
                ibv_ghi = ibv_ghi[0]
            ibv_ghi = ibv_ghi / 12
            
            cleaned_data['gti'] = ibv_gti
            cleaned_data['ghi'] = ibv_ghi
        
        # Process meter data
        if 'meter' in data:
            meter_data = data['meter']
            if not meter_data.empty:
                meter_cleaned, _ = self.cleaner.clean_series(meter_data, data_type='meter')
                cleaned_data['meter'] = meter_cleaned.sum(axis=1)  # Sum all meter channels
            else:
                cleaned_data['meter'] = pd.Series(0, index=data['pyran'].index if 'pyran' in data else [])
        
        # Process inverter power data
        if 'invPower' in data:
            inv_data = data['invPower']
            inv_cleaned, _ = self.cleaner.clean_series(inv_data, data_type='inv')
            cleaned_data['invPower'] = inv_cleaned
        
        # Process temperature data if correction is enabled
        if apply_temp_correction and 'meteo' in data:
            temp_raw = column_filter(data['meteo'], keywords.get('modTemp', 'temp'))
            temp_cleaned, _ = self.cleaner.clean_series(temp_raw, data_type='temp')
            cleaned_data['modTemp'] = temp_cleaned
        
        self.cleaned_data.update(cleaned_data)
        return cleaned_data
    
    def _clean_irradiance_scaldia(self, gti_data: pd.DataFrame) -> pd.Series:
        """Special irradiance cleaning for Scaldia project"""
        # Apply Scaldia-specific cleaning logic
        # This would contain the specific logic from irradiance_Clean_Scaldia function
        
        gti_clean = gti_data.copy()
        gti_clean[gti_clean < 0] = 0
        
        # Calculate mean, but handle special cases
        ibv_gti = gti_clean.mean(axis=1)
        
        return ibv_gti
    
    def calculate_performance_metrics(
        self,
        cleaned_data: Dict[str, pd.DataFrame],
        params: Dict[str, Any]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate standard performance metrics
        
        Args:
            cleaned_data: Dictionary of cleaned data
            params: Project parameters
        
        Returns:
            Dictionary of performance metrics
        """
        self.logger.info("Calculating performance metrics")
        
        metrics = {}
        
        if 'gti' in cleaned_data and 'invPower' in cleaned_data:
            gti = cleaned_data['gti']
            power = cleaned_data['invPower']
            
            # Calculate Performance Ratio
            if isinstance(power, pd.DataFrame):
                total_power = power.sum(axis=1)
            else:
                total_power = power
            
            installed_capacity = params.get('installed_capacity', 1000)  # kW
            
            pr = total_power / (gti * installed_capacity / 1000)
            pr = pr.clip(0, 2)  # Limit to realistic values
            
            metrics['performance_ratio'] = pr.to_frame('PR')
        
        # Calculate availability if meter data exists
        if 'meter' in cleaned_data:
            availability = self.aggregator.calculate_availability(
                cleaned_data['meter'].to_frame() if isinstance(cleaned_data['meter'], pd.Series) else cleaned_data['meter']
            )
            metrics['availability'] = availability
        
        return metrics
    
    def export_results(
        self,
        data: Dict[str, pd.DataFrame],
        output_path: str,
        report_type: str = 'monthly'
    ) -> str:
        """
        Export processing results
        
        Args:
            data: Processed data to export
            output_path: Output file path
            report_type: Type of report
        
        Returns:
            Path to exported file
        """
        return self.exporter.export_aggregated_data(data, output_path, report_type)


class ProjectParameterManager:
    """
    Consolidated project parameter management
    
    Replaces project_parameters class functionality
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def load_parameters(self, project: str) -> Dict[str, Any]:
        """
        Load project-specific parameters from configuration
        
        Args:
            project: Project name
        
        Returns:
            Dictionary of project parameters
        """
        # This would load from actual parameter files
        # For now, return structured defaults
        
        default_params = {
            'project': project,
            'country': 'Unknown',
            'min_irradiance': 50,
            'module_capacity': 400,  # Watts
            'modules_per_string': 20,
            'strings_per_inverter': 10,
            'inverter_capacity': 100,  # kW
            'installed_capacity': 1000,  # kW
            'reference_irradiance': 1000  # W/m²
        }
        
        # Calculate derived parameters
        default_params['string_dc_capacity'] = (
            default_params['module_capacity'] * default_params['modules_per_string'] / 1000
        )
        
        return default_params


class DataPackageManager:
    """
    Manage data packages for different report types
    
    Replaces get_data_package class functionality
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        
        # Define data packages for different report types
        self.data_packages = {
            0: [],
            1: ['meteo', 'pyran', 'tracker', 'invPOut', 'invPIn', 'meter', 
                'cbCurr', 'cbVolt', 'cbTotCurr', 'dustIQ', 'referenceCell'],
            2: ['meteo', 'pyran', 'meter'],
            3: ['meteo', 'pyran', 'invPOut', 'invPIn', 'meter', 
                'cbCurr', 'cbVolt', 'cbTotCurr'],
            4: ['meteo', 'pyran', 'tracker', 'invPOut', 'invPIn', 'meter',
                'cbCurr', 'cbVolt', 'cbTotCurr', 'eventCode', 'heatSinkTemp', 
                'dustIQ', 'referenceCell'],
            5: ['pyran', 'meter'],
            6: ['pyran', 'meter', 'meteo', 'cbVolt', 'cbTotCurr', 'invPOut', 'invPIn'],
            7: ['meteo', 'pyran', 'meter', 'invPOut', 'invPIn'],
            8: ['meteo', 'pyran', 'meter', 'gridVoltage', 'gridCurrent', 
                'gridPower', 'invPOut', 'invACVoltage', 'invACCurrent'],
            9: ['meter'],
            10: ['meteo', 'pyran', 'meter', 'invPOut'],
            11: ['meteo', 'pyran', 'meter', 'invPOut'],
            12: ['meteo', 'pyran', 'meter', 'invPOut', 'invInCurr', 'invInVolt'],
            13: ['meteo', 'pyran', 'meter']
        }
    
    def get_data_requirements(self, report_type: int) -> List[str]:
        """
        Get data requirements for specific report type
        
        Args:
            report_type: Type of report (0-13)
        
        Returns:
            List of required data types
        """
        return self.data_packages.get(report_type, [])