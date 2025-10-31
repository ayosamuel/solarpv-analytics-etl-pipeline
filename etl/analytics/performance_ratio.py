"""
Performance Ratio Analytics Module

Consolidates all PR calculation workflows found across Study files:
- Study043_Gorontalo_v03.py: Multi-azimuth PR calculations
- Study037_FortDePol_PR_v05.py: Plant-level PR analysis
- Study040_Vloeivelden_Performance_Check_v05.py: Performance validation
- Study047_Noordscheschut_InvPower_AmbTemp_v01.py: Inverter-level PR
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging

from ..utils.logging import setup_logger
from ..utils.config import ConfigManager


@dataclass
class PRResults:
    """Standardized PR calculation results"""
    pr_5min: pd.DataFrame
    pr_daily: pd.DataFrame  
    pr_monthly: pd.DataFrame
    pr_temp_corrected: pd.DataFrame
    reference_energy: pd.DataFrame
    actual_energy: pd.DataFrame
    data_availability: Dict[str, float]
    statistics: Dict[str, Any]


class PerformanceRatioCalculator:
    """
    Standardized Performance Ratio calculations for solar plants
    
    Consolidates PR calculation patterns from:
    - Standard PR: E_meter / E_reference
    - Temperature-corrected PR using module temperature data
    - Multi-azimuth PR for complex plant layouts
    - Plant, inverter, and string-level PR calculations
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def calculate_plant_pr(
        self,
        meter_data: pd.DataFrame,
        irradiance_data: pd.DataFrame,
        dc_capacity: float,
        module_temp: pd.DataFrame = None,
        temp_coefficient: float = -0.004,
        reference_temp: float = 25.0,
        aggregation_levels: List[str] = ['5min', 'daily', 'monthly']
    ) -> PRResults:
        """
        Calculate plant-level Performance Ratio
        
        Replaces redundant PR calculations across multiple Study files
        """
        self.logger.info("Starting plant-level PR calculation")
        
        # Prepare main dataframe
        main_df = self._prepare_pr_dataframe(
            meter_data, irradiance_data, module_temp
        )
        
        # Calculate reference energy
        main_df['E_Ref'] = (main_df['GTI'] * dc_capacity / 1000)
        
        # Temperature correction if module temp available
        if module_temp is not None:
            temp_factor = 1 + temp_coefficient * (main_df['ModTemp'] - reference_temp)
            main_df['E_Ref_TempCorr'] = main_df['E_Ref'] * temp_factor
        
        # Calculate PR at different resolutions
        pr_results = {}
        for level in aggregation_levels:
            pr_results[level] = self._calculate_pr_at_resolution(main_df, level)
        
        # Generate statistics
        statistics = self._generate_pr_statistics(pr_results)
        
        return PRResults(
            pr_5min=pr_results.get('5min'),
            pr_daily=pr_results.get('daily'),
            pr_monthly=pr_results.get('monthly'),
            pr_temp_corrected=main_df.get('TempCorr PR') if module_temp else None,
            reference_energy=main_df[['E_Ref']],
            actual_energy=main_df[['E_Meter']],
            data_availability=self._calculate_data_availability(main_df),
            statistics=statistics
        )
    
    def calculate_multi_azimuth_pr(
        self,
        power_data: pd.DataFrame,
        irradiance_by_azimuth: Dict[str, pd.DataFrame],
        capacity_mapping: pd.DataFrame,
        string_map: pd.DataFrame,
        equipment_level: str = 'inverter',
        aggregation: str = 'monthly'
    ) -> pd.DataFrame:
        """
        Calculate PR for multi-azimuth plants with different tilt/orientation zones
        
        Consolidates multi-azimuth logic from Gorontalo study
        """
        self.logger.info(f"Calculating multi-azimuth PR at {equipment_level} level")
        
        pr_results = {}
        
        for equipment in power_data.columns:
            # Get azimuth/tilt for this equipment from string mapping
            equipment_strings = self._get_equipment_strings(equipment, string_map, equipment_level)
            
            if equipment_strings.empty:
                continue
                
            # Calculate weighted irradiance for this equipment
            weighted_irradiance = self._calculate_weighted_irradiance(
                equipment_strings, irradiance_by_azimuth
            )
            
            # Get capacity for this equipment
            equipment_capacity = capacity_mapping.loc[equipment] if equipment in capacity_mapping.index else 0
            
            # Calculate PR
            equipment_power = power_data[equipment]
            reference_power = weighted_irradiance * equipment_capacity / 1000
            
            pr_series = np.where(reference_power > 0, 
                               equipment_power / reference_power, 0)
            
            pr_results[equipment] = pd.Series(pr_series, index=power_data.index)
        
        pr_df = pd.DataFrame(pr_results)
        
        # Aggregate if requested
        if aggregation == 'daily':
            pr_df = pr_df.groupby(pr_df.index.date).mean()
        elif aggregation == 'monthly':
            pr_df = pr_df.groupby([pr_df.index.year, pr_df.index.month]).mean()
        
        return pr_df
    
    def calculate_inverter_level_pr(
        self,
        inverter_power: pd.DataFrame,
        irradiance_data: pd.DataFrame,
        inverter_capacity_map: pd.DataFrame,
        string_map: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Calculate PR at inverter level
        
        Handles both string inverters and central inverters
        """
        self.logger.info("Calculating inverter-level PR")
        
        pr_results = {}
        
        for inverter in inverter_power.columns:
            # Get capacity for this inverter
            if inverter in inverter_capacity_map.index:
                inv_capacity = inverter_capacity_map.loc[inverter]
            else:
                self.logger.warning(f"Capacity not found for inverter {inverter}")
                continue
            
            # Calculate reference energy
            if string_map is not None:
                # Multi-azimuth case
                weighted_irr = self._get_inverter_weighted_irradiance(
                    inverter, irradiance_data, string_map
                )
            else:
                # Single azimuth case
                weighted_irr = irradiance_data.mean(axis=1)
            
            reference_energy = weighted_irr * inv_capacity / 1000
            actual_energy = inverter_power[inverter]
            
            pr_series = np.where(reference_energy > 0,
                               actual_energy / reference_energy, 0)
            
            pr_results[inverter] = pr_series
        
        return pd.DataFrame(pr_results, index=inverter_power.index)
    
    def _prepare_pr_dataframe(
        self, 
        meter_data: pd.DataFrame, 
        irradiance_data: pd.DataFrame,
        module_temp: pd.DataFrame = None
    ) -> pd.DataFrame:
        """Prepare main dataframe for PR calculations"""
        
        # Combine meter and irradiance data
        gti_avg = irradiance_data.mean(axis=1) if isinstance(irradiance_data, pd.DataFrame) else irradiance_data
        meter_avg = meter_data.sum(axis=1) if isinstance(meter_data, pd.DataFrame) else meter_data
        
        main_df = pd.concat([meter_avg, gti_avg], axis=1)
        main_df.columns = ['E_Meter', 'GTI']
        
        # Add module temperature if available
        if module_temp is not None:
            modtemp_avg = module_temp.mean(axis=1) if isinstance(module_temp, pd.DataFrame) else module_temp
            main_df['ModTemp'] = modtemp_avg
        
        # Remove missing data
        main_df = main_df.dropna()
        
        return main_df
    
    def _calculate_pr_at_resolution(self, main_df: pd.DataFrame, resolution: str) -> pd.DataFrame:
        """Calculate PR at specified time resolution"""
        
        if resolution == '5min':
            result_df = main_df.copy()
        elif resolution == 'daily':
            result_df = main_df.groupby(main_df.index.date).sum() / 12000  # Convert to kWh
        elif resolution == 'monthly':
            result_df = main_df.groupby([main_df.index.year, main_df.index.month]).sum() / 12000
        else:
            raise ValueError(f"Unsupported resolution: {resolution}")
        
        # Calculate PR
        result_df['Actual PR'] = np.where(
            result_df['E_Ref'] > 0, 
            result_df['E_Meter'] / result_df['E_Ref'], 
            0
        )
        
        if 'E_Ref_TempCorr' in result_df.columns:
            result_df['TempCorr PR'] = np.where(
                result_df['E_Ref_TempCorr'] > 0,
                result_df['E_Meter'] / result_df['E_Ref_TempCorr'],
                0
            )
        
        return result_df
    
    def _calculate_weighted_irradiance(
        self, 
        equipment_strings: pd.DataFrame, 
        irradiance_by_azimuth: Dict[str, pd.DataFrame]
    ) -> pd.Series:
        """Calculate capacity-weighted irradiance for equipment"""
        
        total_weighted_irr = 0
        total_capacity = 0
        
        for _, string_info in equipment_strings.iterrows():
            azimuth_key = f"{string_info['tilt']}_{string_info['azimuth']}"
            
            if azimuth_key in irradiance_by_azimuth:
                string_capacity = string_info.get('capacity', 1)  # Default to 1 if not specified
                irradiance = irradiance_by_azimuth[azimuth_key].mean(axis=1)
                
                total_weighted_irr += irradiance * string_capacity
                total_capacity += string_capacity
        
        return total_weighted_irr / total_capacity if total_capacity > 0 else pd.Series(0, index=irradiance.index)
    
    def _get_equipment_strings(
        self, 
        equipment: str, 
        string_map: pd.DataFrame, 
        equipment_level: str
    ) -> pd.DataFrame:
        """Get strings associated with specific equipment"""
        
        if equipment_level == 'inverter':
            return string_map[string_map['inverter'].str.contains(equipment, na=False)]
        elif equipment_level == 'transformer':
            return string_map[string_map['transformer'].str.contains(equipment, na=False)]
        elif equipment_level == 'string':
            return string_map[string_map.index == equipment]
        else:
            return pd.DataFrame()
    
    def _get_inverter_weighted_irradiance(
        self, 
        inverter: str, 
        irradiance_data: Dict[str, pd.DataFrame], 
        string_map: pd.DataFrame
    ) -> pd.Series:
        """Get weighted irradiance for a specific inverter"""
        
        inverter_strings = self._get_equipment_strings(inverter, string_map, 'inverter')
        return self._calculate_weighted_irradiance(inverter_strings, irradiance_data)
    
    def _calculate_data_availability(self, main_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate data availability statistics"""
        
        total_points = len(main_df.index)
        
        availability = {
            'meter_availability': (main_df['E_Meter'].notna().sum() / total_points) * 100,
            'irradiance_availability': (main_df['GTI'].notna().sum() / total_points) * 100,
            'combined_availability': (main_df.notna().all(axis=1).sum() / total_points) * 100
        }
        
        if 'ModTemp' in main_df.columns:
            availability['temperature_availability'] = (main_df['ModTemp'].notna().sum() / total_points) * 100
        
        return availability
    
    def _generate_pr_statistics(self, pr_results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate comprehensive PR statistics"""
        
        statistics = {}
        
        for resolution, pr_df in pr_results.items():
            if pr_df is not None and 'Actual PR' in pr_df.columns:
                pr_values = pr_df['Actual PR'][pr_df['Actual PR'] > 0]  # Exclude zero values
                
                statistics[resolution] = {
                    'mean_pr': pr_values.mean(),
                    'median_pr': pr_values.median(),
                    'std_pr': pr_values.std(),
                    'min_pr': pr_values.min(),
                    'max_pr': pr_values.max(),
                    'count': len(pr_values),
                    'p25': pr_values.quantile(0.25),
                    'p75': pr_values.quantile(0.75),
                    'p90': pr_values.quantile(0.90),
                    'p95': pr_values.quantile(0.95)
                }
        
        return statistics


class StringLevelAnalyzer:
    """
    String-level performance and fault analysis
    
    Consolidates string analysis patterns from multiple studies
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def calculate_string_pr(
        self,
        string_power: pd.DataFrame,
        string_current: pd.DataFrame,
        string_voltage: pd.DataFrame,
        irradiance_data: pd.DataFrame,
        string_capacity_map: pd.DataFrame,
        aggregation: str = 'monthly'
    ) -> pd.DataFrame:
        """Calculate PR at string level with validation"""
        
        self.logger.info("Calculating string-level PR")
        
        # Validate string power calculation
        calculated_power = string_current * string_voltage / 1000  # Convert to kW
        calculated_power[calculated_power < 0] = 0
        
        # Use calculated power if string_power not provided or inconsistent
        if string_power is None or len(string_power.columns) != len(calculated_power.columns):
            string_power = calculated_power
        
        # Calculate PR for each string
        pr_results = {}
        irr_avg = irradiance_data.mean(axis=1)
        
        for string in string_power.columns:
            if string in string_capacity_map.index:
                string_cap = string_capacity_map.loc[string]
                reference_power = irr_avg * string_cap / 1000
                
                pr_series = np.where(reference_power > 0,
                                   string_power[string] / reference_power, 0)
                pr_results[string] = pr_series
        
        pr_df = pd.DataFrame(pr_results, index=string_power.index)
        
        # Aggregate if requested
        if aggregation == 'daily':
            pr_df = pr_df.groupby(pr_df.index.date).mean()
        elif aggregation == 'monthly':
            pr_df = pr_df.groupby([pr_df.index.year, pr_df.index.month]).mean()
        
        return pr_df
    
    def detect_string_underperformance(
        self,
        string_current: pd.DataFrame,
        working_strings_map: pd.DataFrame,
        deviation_threshold: float = 0.15,
        fault_duration_threshold: int = 42  # datapoints
    ) -> pd.DataFrame:
        """
        Detect underperforming strings using current deviation analysis
        
        Consolidates string fault detection from Gorontalo study
        """
        self.logger.info("Detecting string underperformance")
        
        string_faults = pd.DataFrame(index=string_current.index, columns=string_current.columns)
        string_faults = string_faults.fillna(0)
        
        # Group strings by combiner box for relative comparison
        cb_groups = self._group_strings_by_combiner_box(string_current.columns)
        
        for cb_name, cb_strings in cb_groups.items():
            cb_currents = string_current[cb_strings]
            
            # Calculate reference current (median of working strings)
            working_mask = working_strings_map.loc[cb_strings] > 0
            working_currents = cb_currents.loc[:, working_mask[working_mask].index]
            
            if len(working_currents.columns) < 2:
                continue  # Need at least 2 working strings for comparison
            
            reference_current = working_currents.median(axis=1)
            
            # Calculate deviations
            for string in cb_strings:
                if string in working_currents.columns:
                    deviation = np.abs(cb_currents[string] - reference_current) / (reference_current + 1e-6)
                    fault_mask = deviation > deviation_threshold
                    string_faults[string] = fault_mask.astype(int)
        
        # Apply fault duration threshold
        string_faults_daily = string_faults.groupby(string_faults.index.date).sum()
        persistent_faults = string_faults_daily > fault_duration_threshold
        
        return persistent_faults.astype(int)
    
    def _group_strings_by_combiner_box(self, string_names: List[str]) -> Dict[str, List[str]]:
        """Group strings by combiner box based on naming convention"""
        
        cb_groups = {}
        
        for string in string_names:
            # Extract combiner box name (typically first 10 characters)
            cb_name = string[:10]
            
            if cb_name not in cb_groups:
                cb_groups[cb_name] = []
            
            cb_groups[cb_name].append(string)
        
        return cb_groups


class ClippingAnalyzer:
    """
    Inverter and string clipping analysis
    
    Consolidates clipping detection patterns from multiple studies
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def detect_inverter_clipping(
        self,
        inverter_power: pd.DataFrame,
        irradiance_data: pd.DataFrame,
        power_limits: pd.Series,
        clipping_threshold_ratio: float = 0.98
    ) -> Dict[str, Dict[str, Any]]:
        """
        Detect inverter clipping and estimate minimum clipping irradiance
        
        Consolidates clipping analysis from Noordscheschut study
        """
        self.logger.info("Analyzing inverter clipping")
        
        clipping_results = {}
        irr_avg = irradiance_data.mean(axis=1)
        
        for inverter in inverter_power.columns:
            if inverter not in power_limits.index:
                continue
            
            inv_power = inverter_power[inverter].dropna()
            power_limit = power_limits[inverter]
            
            # Find clipping events (power close to maximum)
            clipping_threshold = power_limit * clipping_threshold_ratio
            clipping_events = inv_power[inv_power >= clipping_threshold]
            
            if len(clipping_events) == 0:
                continue
            
            # Get corresponding irradiance values
            clipping_irradiance = irr_avg.loc[clipping_events.index]
            
            # Estimate minimum clipping irradiance
            min_clipping_irr = clipping_irradiance.quantile(0.1)  # Bottom 10% of clipping events
            
            # Calculate overloading ratio (OLR) if string info available
            # This would need additional string mapping information
            
            clipping_results[inverter] = {
                'clipping_events_count': len(clipping_events),
                'min_clipping_irradiance': min_clipping_irr,
                'avg_clipping_irradiance': clipping_irradiance.mean(),
                'clipping_power_threshold': clipping_threshold,
                'max_recorded_power': inv_power.max(),
                'clipping_frequency_pct': (len(clipping_events) / len(inv_power)) * 100
            }
        
        return clipping_results
    
    def detect_mppt_clipping(
        self,
        string_current: pd.DataFrame,
        current_limit: float = 25.8,
        min_clipping_events: int = 10
    ) -> Dict[str, pd.DataFrame]:
        """
        Detect MPPT-level current clipping
        
        Consolidates MPPT clipping analysis patterns
        """
        self.logger.info("Analyzing MPPT clipping")
        
        # Group strings by MPPT (modify naming logic as needed)
        mppt_currents = self._group_strings_by_mppt(string_current)
        
        mppt_clipping_results = {}
        
        for mppt, mppt_current_data in mppt_currents.items():
            # Detect clipping events
            clipping_mask = mppt_current_data > current_limit
            clipping_events = mppt_current_data[clipping_mask]
            
            if len(clipping_events) >= min_clipping_events:
                mppt_clipping_results[mppt] = {
                    'clipping_events': clipping_events,
                    'clipping_frequency': (len(clipping_events) / len(mppt_current_data)) * 100,
                    'max_current': mppt_current_data.max(),
                    'avg_clipping_current': clipping_events.mean()
                }
        
        return mppt_clipping_results
    
    def _group_strings_by_mppt(self, string_current: pd.DataFrame) -> Dict[str, pd.Series]:
        """Group string currents by MPPT channel"""
        
        mppt_groups = {}
        
        for string in string_current.columns:
            # Extract MPPT identifier (modify based on naming convention)
            # Assuming format like "SCB A.1.01.current_string_1" -> MPPT = "SCB A.1.01"
            mppt_id = string[:14] if len(string) > 14 else string[:11]
            
            if mppt_id not in mppt_groups:
                mppt_groups[mppt_id] = []
            
            mppt_groups[mppt_id].append(string)
        
        # Sum currents for each MPPT
        mppt_currents = {}
        for mppt_id, string_list in mppt_groups.items():
            mppt_currents[mppt_id] = string_current[string_list].sum(axis=1)
        
        return mppt_currents
