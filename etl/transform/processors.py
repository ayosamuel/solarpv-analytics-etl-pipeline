"""
Data processing functions for solar plant analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger
from ..utils.helpers import column_filter, column_delete


class DataProcessor:
    """Main data processing class for solar plant data"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def filter_columns(
        self, 
        df: pd.DataFrame, 
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> pd.DataFrame:
        """
        Filter DataFrame columns by patterns
        
        Args:
            df: Input DataFrame
            include_patterns: Patterns to include
            exclude_patterns: Patterns to exclude
        
        Returns:
            Filtered DataFrame
        """
        result_df = df.copy()
        
        # Apply include filters
        if include_patterns:
            for pattern in include_patterns:
                result_df = column_filter(result_df, pattern)
        
        # Apply exclude filters
        if exclude_patterns:
            for pattern in exclude_patterns:
                result_df = column_delete(result_df, pattern)
        
        return result_df
    
    def apply_unit_conversions(
        self,
        data: Dict[str, pd.DataFrame],
        conversions: Dict[str, Dict[str, float]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Apply unit conversions to data
        
        Args:
            data: Dictionary of DataFrames
            conversions: Conversion factors for each data type
        
        Returns:
            Dictionary of converted DataFrames
        """
        if conversions is None:
            conversions = {
                'irradiance': {'factor': 12, 'description': 'Convert to Wh'},
                'power': {'factor': 1000, 'description': 'Convert to kW'},
                'energy': {'factor': 1000, 'description': 'Convert to kWh'}
            }
        
        converted_data = {}
        
        for key, df in data.items():
            if key in conversions:
                factor = conversions[key]['factor']
                converted_data[key] = df / factor
                self.logger.info(f"Applied conversion to {key}: {conversions[key]['description']}")
            else:
                converted_data[key] = df.copy()
        
        return converted_data
    
    def calculate_performance_metrics(
        self,
        power_data: pd.DataFrame,
        irradiance_data: pd.Series,
        installed_capacity: float,
        reference_irradiance: float = 1000
    ) -> pd.DataFrame:
        """
        Calculate performance metrics for solar plant
        
        Args:
            power_data: Power generation data
            irradiance_data: Irradiance measurements
            installed_capacity: Installed capacity in kW
            reference_irradiance: Reference irradiance for PR calculation
        
        Returns:
            DataFrame with performance metrics
        """
        self.logger.info("Calculating performance metrics")
        
        metrics = pd.DataFrame(index=power_data.index)
        
        # Total power
        metrics['total_power'] = power_data.sum(axis=1)
        
        # Performance Ratio (PR)
        metrics['performance_ratio'] = (
            metrics['total_power'] / 
            (installed_capacity * irradiance_data / reference_irradiance)
        )
        
        # Capacity Factor
        metrics['capacity_factor'] = metrics['total_power'] / installed_capacity
        
        # Specific Yield (kWh/kWp)
        metrics['specific_yield'] = metrics['total_power'] / installed_capacity
        
        # Filter unrealistic values
        metrics['performance_ratio'] = metrics['performance_ratio'].clip(0, 2)
        metrics['capacity_factor'] = metrics['capacity_factor'].clip(0, 1)
        
        return metrics


class MultiAzimuthProcessor(DataProcessor):
    """Processor for multi-azimuth solar installations"""
    
    def calculate_multi_azimuth_irradiance(
        self,
        gti_data: pd.DataFrame,
        azimuth_distribution: Dict[str, float],
        string_mapping: Dict[str, str] = None
    ) -> pd.Series:
        """
        Calculate weighted irradiance for multi-azimuth installations
        
        Args:
            gti_data: GTI data for different orientations
            azimuth_distribution: Distribution of capacity by azimuth
            string_mapping: Mapping of strings to azimuth orientations
        
        Returns:
            Weighted average irradiance series
        """
        self.logger.info("Calculating multi-azimuth irradiance")
        
        if string_mapping:
            # Group by azimuth using string mapping
            azimuth_data = {}
            for azimuth in azimuth_distribution.keys():
                matching_strings = [col for col, az in string_mapping.items() if az == azimuth]
                if matching_strings:
                    azimuth_data[azimuth] = gti_data[matching_strings].mean(axis=1)
        else:
            # Assume columns are already azimuth-labeled
            azimuth_data = {col: gti_data[col] for col in gti_data.columns}
        
        # Calculate weighted average
        weighted_irradiance = pd.Series(0, index=gti_data.index)
        total_weight = sum(azimuth_distribution.values())
        
        for azimuth, weight in azimuth_distribution.items():
            if azimuth in azimuth_data:
                weighted_irradiance += azimuth_data[azimuth] * (weight / total_weight)
        
        return weighted_irradiance
    
    def calculate_multi_azimuth_pr(
        self,
        power_data: pd.DataFrame,
        irradiance_data: pd.Series,
        string_count: pd.Series,
        string_mapping: Dict[str, str],
        installed_capacity: float,
        plant_level: bool = True,
        aggregation: str = 'm'
    ) -> pd.DataFrame:
        """
        Calculate Performance Ratio for multi-azimuth installation
        
        Args:
            power_data: Power generation data
            irradiance_data: Weighted irradiance data
            string_count: Number of strings per inverter/section
            string_mapping: Mapping of strings to orientations
            installed_capacity: Total installed capacity
            plant_level: Whether to calculate plant-level or section-level PR
            aggregation: Time aggregation ('d' for daily, 'm' for monthly)
        
        Returns:
            DataFrame with PR calculations
        """
        self.logger.info(f"Calculating multi-azimuth PR with {aggregation} aggregation")
        
        # Filter data by minimum irradiance
        min_irr = self.config.get('processing.min_irradiance', 50)
        power_filtered = power_data[irradiance_data > min_irr]
        irr_filtered = irradiance_data[irradiance_data > min_irr]
        
        if plant_level:
            # Plant-level calculation
            total_power = power_filtered.sum(axis=1)
            total_strings = string_count.sum()
            
            pr_series = total_power / (irr_filtered * total_strings)
            
            # Aggregate by time
            if aggregation == 'd':
                pr_daily = pr_series.groupby(pr_series.index.date).mean()
                return pd.DataFrame({'PR_plant': pr_daily})
            elif aggregation == 'm':
                pr_monthly = pr_series.groupby([
                    pr_series.index.year, 
                    pr_series.index.month
                ]).mean()
                return pd.DataFrame({'PR_plant': pr_monthly})
        
        else:
            # Section-level calculation
            pr_sections = {}
            
            for section in power_filtered.columns:
                if section in string_count.index:
                    section_power = power_filtered[section]
                    section_strings = string_count[section]
                    
                    pr_section = section_power / (irr_filtered * section_strings)
                    
                    if aggregation == 'd':
                        pr_sections[section] = pr_section.groupby(pr_section.index.date).mean()
                    elif aggregation == 'm':
                        pr_sections[section] = pr_section.groupby([
                            pr_section.index.year,
                            pr_section.index.month
                        ]).mean()
            
            return pd.DataFrame(pr_sections)


class FaultDetector(DataProcessor):
    """Detect faults in solar plant equipment"""
    
    def detect_string_faults(
        self,
        string_currents: pd.DataFrame,
        irradiance_data: pd.Series,
        threshold_factor: float = 0.1,
        min_irradiance: float = 50
    ) -> pd.DataFrame:
        """
        Detect string-level faults based on current measurements
        
        Args:
            string_currents: String current measurements
            irradiance_data: Irradiance data for filtering
            threshold_factor: Threshold for fault detection (fraction of max)
            min_irradiance: Minimum irradiance for analysis
        
        Returns:
            DataFrame with fault indicators (1 = fault, 0 = normal)
        """
        self.logger.info("Detecting string faults")
        
        # Filter by irradiance
        filtered_currents = string_currents[irradiance_data > min_irradiance]
        
        # Calculate maximum current per device/inverter
        device_max_currents = []
        device_names = list(set([col.split('_')[0] for col in filtered_currents.columns]))
        
        for device in device_names:
            device_columns = [col for col in filtered_currents.columns if col.startswith(device)]
            device_currents = filtered_currents[device_columns]
            max_current = device_currents.max(axis=1)
            device_max_currents.append(max_current)
        
        # Detect faults
        string_faults = []
        
        for i, device in enumerate(device_names):
            device_columns = [col for col in filtered_currents.columns if col.startswith(device)]
            device_max = device_max_currents[i]
            
            for col in device_columns:
                string_current = filtered_currents[col]
                fault_mask = string_current < (device_max * threshold_factor)
                string_faults.append(pd.Series(fault_mask.astype(int), name=col))
        
        fault_df = pd.concat(string_faults, axis=1)
        
        self.logger.info(f"Detected faults in {fault_df.sum().sum()} measurements")
        
        return fault_df
    
    def detect_inverter_faults(
        self,
        power_data: pd.DataFrame,
        irradiance_data: pd.Series,
        installed_capacity: pd.Series = None,
        threshold_factor: float = 0.1
    ) -> pd.DataFrame:
        """
        Detect inverter-level faults
        
        Args:
            power_data: Inverter power data
            irradiance_data: Irradiance measurements
            installed_capacity: Installed capacity per inverter
            threshold_factor: Threshold for fault detection
        
        Returns:
            DataFrame with inverter fault indicators
        """
        self.logger.info("Detecting inverter faults")
        
        min_irr = self.config.get('processing.min_irradiance', 50)
        filtered_power = power_data[irradiance_data > min_irr]
        
        # Calculate expected power based on irradiance
        if installed_capacity is not None:
            expected_power = irradiance_data / 1000 * installed_capacity
            power_ratio = filtered_power / expected_power
            
            # Detect when actual power is significantly below expected
            fault_mask = power_ratio < threshold_factor
        else:
            # Use relative comparison between inverters
            max_power = filtered_power.max(axis=1)
            fault_mask = filtered_power < (max_power.values[:, np.newaxis] * threshold_factor)
        
        return fault_mask.astype(int)