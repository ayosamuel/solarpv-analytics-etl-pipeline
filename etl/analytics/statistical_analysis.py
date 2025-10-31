"""
Statistical Analysis and Reporting Module

Consolidates statistical analysis patterns found across Study files:
- Data availability statistics
- Performance statistics and benchmarking  
- Plant capacity and working equipment analysis
- Statistical summaries and reporting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging

from ..utils.logging import setup_logger
from ..utils.config import ConfigManager


@dataclass
class AvailabilityStats:
    """Data availability statistics"""
    daily_availability: pd.DataFrame
    monthly_availability: pd.DataFrame
    overall_availability: Dict[str, float]
    missing_periods: List[Dict[str, Any]]
    quality_score: float


@dataclass
class PlantCapacityAnalysis:
    """Plant capacity and working equipment analysis"""
    working_strings_per_level: Dict[str, pd.DataFrame]
    dc_capacity_per_level: Dict[str, pd.DataFrame]
    equipment_utilization: Dict[str, float]
    capacity_factors: Dict[str, float]
    working_equipment_stats: Dict[str, Any]


class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis for solar plant data
    
    Consolidates statistical analysis patterns from:
    - Data availability calculations across all studies
    - Working string/equipment counting
    - Capacity utilization analysis
    - Performance benchmarking
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def calculate_data_availability(
        self,
        datasets: Dict[str, pd.DataFrame],
        aggregation_levels: List[str] = ['daily', 'monthly'],
        expected_frequency: str = '5min'
    ) -> AvailabilityStats:
        """
        Calculate comprehensive data availability statistics
        
        Consolidates availability calculations from all Study files
        """
        self.logger.info(f"Calculating data availability for {len(datasets)} datasets")
        
        availability_results = {}
        overall_availability = {}
        
        for level in aggregation_levels:
            level_results = {}
            
            for dataset_name, data in datasets.items():
                if data.empty:
                    level_results[dataset_name] = pd.DataFrame()
                    continue
                
                # Calculate availability at requested level
                if level == 'daily':
                    availability = self._calculate_daily_availability(data)
                elif level == 'monthly':
                    availability = self._calculate_monthly_availability(data)
                else:
                    raise ValueError(f"Unsupported aggregation level: {level}")
                
                level_results[dataset_name] = availability
                
                # Calculate overall availability for this dataset
                if dataset_name not in overall_availability:
                    total_possible = self._calculate_expected_points(data, expected_frequency)
                    total_actual = data.notna().sum().sum()
                    overall_availability[dataset_name] = (total_actual / total_possible) * 100 if total_possible > 0 else 0
            
            availability_results[level] = level_results
        
        # Identify missing periods
        missing_periods = self._identify_missing_periods(datasets, expected_frequency)
        
        # Calculate overall quality score
        quality_score = np.mean(list(overall_availability.values())) if overall_availability else 0
        
        return AvailabilityStats(
            daily_availability=availability_results.get('daily', {}),
            monthly_availability=availability_results.get('monthly', {}),
            overall_availability=overall_availability,
            missing_periods=missing_periods,
            quality_score=quality_score
        )
    
    def analyze_plant_capacity(
        self,
        equipment_data: Dict[str, pd.DataFrame],  # 'string_current', 'inverter_power', etc.
        plant_parameters: Dict[str, Any],
        string_dc_capacity: float = None,
        equipment_hierarchy: Dict[str, int] = None  # level_name -> string_count_threshold
    ) -> PlantCapacityAnalysis:
        """
        Analyze plant capacity and working equipment at different levels
        
        Consolidates capacity analysis patterns from Gorontalo and other studies
        """
        self.logger.info("Analyzing plant capacity and working equipment")
        
        working_strings_per_level = {}
        dc_capacity_per_level = {}
        equipment_utilization = {}
        capacity_factors = {}
        
        # Default hierarchy if not provided
        if equipment_hierarchy is None:
            equipment_hierarchy = {
                'channel': 1,      # String level
                'combiner_box': 10,    # CB level (typically 10 strings)
                'inverter': None,      # Will be determined from data
                'transformer': None    # Will be determined from data
            }
        
        # Analyze string-level data if available
        if 'string_current' in equipment_data:
            string_data = equipment_data['string_current']
            
            # Identify working strings (non-zero, realistic current values)
            working_strings = self._identify_working_strings(
                string_data, 
                min_current=0.5, 
                max_current=30.0
            )
            
            working_strings_per_level['channel'] = working_strings
            
            if string_dc_capacity:
                dc_capacity_per_level['channel'] = working_strings * string_dc_capacity
            
            # Calculate higher-level aggregations
            for level_name, string_count in equipment_hierarchy.items():
                if level_name == 'channel':
                    continue
                
                if string_count:
                    level_working = self._aggregate_string_count(working_strings, string_count)
                    working_strings_per_level[level_name] = level_working
                    
                    if string_dc_capacity:
                        dc_capacity_per_level[level_name] = level_working * string_dc_capacity
        
        # Analyze inverter-level data if available
        if 'inverter_power' in equipment_data:
            inv_data = equipment_data['inverter_power']
            
            # Calculate inverter utilization
            inv_max_power = inv_data.max()
            inv_rated_power = plant_parameters.get('inverter_rated_power', inv_max_power)
            
            for inverter in inv_data.columns:
                if isinstance(inv_rated_power, dict):
                    rated = inv_rated_power.get(inverter, inv_max_power[inverter])
                else:
                    rated = inv_rated_power
                
                utilization = (inv_data[inverter].mean() / rated) * 100
                equipment_utilization[inverter] = utilization
        
        # Calculate plant-level capacity factors
        if 'irradiance' in equipment_data and dc_capacity_per_level:
            irradiance = equipment_data['irradiance']
            plant_dc_capacity = sum(dc_capacity_per_level.get('channel', {}).values())
            
            if plant_dc_capacity > 0:
                theoretical_energy = irradiance.mean() * plant_dc_capacity / 1000
                
                if 'meter_energy' in equipment_data:
                    actual_energy = equipment_data['meter_energy'].mean()
                    capacity_factors['plant'] = (actual_energy / theoretical_energy) * 100
        
        # Generate working equipment statistics
        working_equipment_stats = self._generate_equipment_stats(
            working_strings_per_level, 
            dc_capacity_per_level,
            equipment_data
        )
        
        return PlantCapacityAnalysis(
            working_strings_per_level=working_strings_per_level,
            dc_capacity_per_level=dc_capacity_per_level,
            equipment_utilization=equipment_utilization,
            capacity_factors=capacity_factors,
            working_equipment_stats=working_equipment_stats
        )
    
    def generate_performance_summary(
        self,
        performance_data: Dict[str, pd.DataFrame],  # 'pr_monthly', 'energy_monthly', etc.
        benchmark_values: Dict[str, float] = None,
        target_values: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance summary with benchmarking
        
        Consolidates performance reporting patterns from multiple studies
        """
        self.logger.info("Generating performance summary")
        
        summary = {}
        
        for metric_name, data in performance_data.items():
            if data.empty:
                continue
            
            metric_summary = {
                'mean': data.mean(),
                'median': data.median(), 
                'std': data.std(),
                'min': data.min(),
                'max': data.max(),
                'count': data.count(),
                'latest_value': data.iloc[-1] if len(data) > 0 else None,
                'trend': self._calculate_trend(data)
            }
            
            # Add percentiles
            if isinstance(data, pd.DataFrame):
                for col in data.columns:
                    col_data = data[col].dropna()
                    if len(col_data) > 0:
                        metric_summary[f'{col}_p25'] = col_data.quantile(0.25)
                        metric_summary[f'{col}_p75'] = col_data.quantile(0.75)
                        metric_summary[f'{col}_p90'] = col_data.quantile(0.90)
            
            # Compare with benchmarks if available
            if benchmark_values and metric_name in benchmark_values:
                benchmark = benchmark_values[metric_name]
                current_mean = data.mean().mean() if isinstance(data, pd.DataFrame) else data.mean()
                metric_summary['benchmark_comparison'] = {
                    'benchmark_value': benchmark,
                    'current_value': current_mean,
                    'difference': current_mean - benchmark,
                    'difference_percent': ((current_mean - benchmark) / benchmark) * 100 if benchmark != 0 else None
                }
            
            # Compare with targets if available
            if target_values and metric_name in target_values:
                target = target_values[metric_name]
                current_mean = data.mean().mean() if isinstance(data, pd.DataFrame) else data.mean()
                metric_summary['target_comparison'] = {
                    'target_value': target,
                    'current_value': current_mean,
                    'achievement_percent': (current_mean / target) * 100 if target != 0 else None,
                    'gap': target - current_mean
                }
            
            summary[metric_name] = metric_summary
        
        # Add overall plant health score
        summary['plant_health_score'] = self._calculate_plant_health_score(summary)
        
        return summary
    
    def calculate_monthly_aggregations(
        self,
        raw_datasets: Dict[str, pd.DataFrame],
        aggregation_functions: Dict[str, str] = None  # dataset_name -> function ('sum', 'mean', etc.)
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate monthly aggregations for multiple datasets
        
        Consolidates monthly aggregation patterns from all studies
        """
        self.logger.info(f"Calculating monthly aggregations for {len(raw_datasets)} datasets")
        
        if aggregation_functions is None:
            # Default aggregation functions
            aggregation_functions = {
                'energy': 'sum',
                'power': 'mean', 
                'irradiance': 'sum',
                'temperature': 'mean',
                'pr': 'mean',
                'current': 'mean',
                'voltage': 'mean'
            }
        
        monthly_data = {}
        
        for dataset_name, data in raw_datasets.items():
            if data.empty:
                monthly_data[dataset_name] = pd.DataFrame()
                continue
            
            # Determine aggregation function
            agg_func = 'mean'  # Default
            for pattern, func in aggregation_functions.items():
                if pattern.lower() in dataset_name.lower():
                    agg_func = func
                    break
            
            # Perform aggregation
            if agg_func == 'sum':
                monthly = data.groupby([data.index.year, data.index.month]).sum()
                # Convert to appropriate units (e.g., kWh for energy)
                if 'energy' in dataset_name.lower() or 'irradiance' in dataset_name.lower():
                    monthly = monthly / 12000  # Convert from 5-min values to kWh
            elif agg_func == 'mean':
                monthly = data.groupby([data.index.year, data.index.month]).mean()
            elif agg_func == 'max':
                monthly = data.groupby([data.index.year, data.index.month]).max()
            elif agg_func == 'min':
                monthly = data.groupby([data.index.year, data.index.month]).min()
            else:
                monthly = data.groupby([data.index.year, data.index.month]).agg(agg_func)
            
            monthly_data[dataset_name] = monthly
        
        return monthly_data
    
    def _calculate_daily_availability(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily data availability"""
        
        # Expected points per day (288 for 5-minute data)
        expected_daily_points = 288
        
        daily_counts = data.groupby(data.index.date).count()
        daily_availability = (daily_counts / expected_daily_points) * 100
        
        # Clip to 100% in case of more data than expected
        daily_availability = daily_availability.clip(upper=100)
        
        return daily_availability
    
    def _calculate_monthly_availability(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate monthly data availability"""
        
        monthly_availability = {}
        
        for col in data.columns:
            monthly_data = []
            
            for year_month, group in data.groupby([data.index.year, data.index.month]):
                year, month = year_month
                
                # Calculate expected points for this month
                month_start = pd.Timestamp(year, month, 1)
                if month == 12:
                    month_end = pd.Timestamp(year + 1, 1, 1) - pd.Timedelta(seconds=1)
                else:
                    month_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(seconds=1)
                
                expected_points = len(pd.date_range(month_start, month_end, freq='5min'))
                actual_points = group[col].notna().sum()
                
                availability = (actual_points / expected_points) * 100 if expected_points > 0 else 0
                
                monthly_data.append({
                    'year': year,
                    'month': month,
                    'availability': min(availability, 100)  # Cap at 100%
                })
            
            monthly_availability[col] = pd.DataFrame(monthly_data).set_index(['year', 'month'])
        
        return pd.concat(monthly_availability, axis=1)
    
    def _identify_working_strings(
        self, 
        string_data: pd.DataFrame,
        min_current: float = 0.5,
        max_current: float = 30.0,
        min_data_points: int = 100
    ) -> pd.Series:
        """Identify working strings based on current data"""
        
        working_strings = pd.Series(index=string_data.columns, dtype=int)
        
        for string in string_data.columns:
            string_current = string_data[string].dropna()
            
            # Check if string has sufficient data
            if len(string_current) < min_data_points:
                working_strings[string] = 0
                continue
            
            # Check if current values are within realistic range
            valid_currents = string_current[
                (string_current >= min_current) & 
                (string_current <= max_current)
            ]
            
            # String is considered working if >50% of data is valid and non-zero
            if len(valid_currents) > len(string_current) * 0.5:
                working_strings[string] = 1
            else:
                working_strings[string] = 0
        
        return working_strings
    
    def _aggregate_string_count(self, working_strings: pd.Series, strings_per_unit: int) -> pd.Series:
        """Aggregate string counts to higher equipment levels"""
        
        aggregated = {}
        
        for string_name in working_strings.index:
            # Extract unit name (e.g., combiner box name from string name)
            # This logic may need adjustment based on naming convention
            unit_name = string_name[:strings_per_unit] if len(string_name) >= strings_per_unit else string_name
            
            if unit_name not in aggregated:
                aggregated[unit_name] = 0
            
            aggregated[unit_name] += working_strings[string_name]
        
        return pd.Series(aggregated)
    
    def _calculate_expected_points(self, data: pd.DataFrame, frequency: str = '5min') -> int:
        """Calculate expected number of data points"""
        
        if data.empty:
            return 0
        
        time_span = data.index.max() - data.index.min()
        freq_delta = pd.Timedelta(frequency)
        
        expected_points = int(time_span / freq_delta) + 1
        num_columns = len(data.columns)
        
        return expected_points * num_columns
    
    def _identify_missing_periods(
        self, 
        datasets: Dict[str, pd.DataFrame], 
        frequency: str = '5min'
    ) -> List[Dict[str, Any]]:
        """Identify periods with missing data across datasets"""
        
        missing_periods = []
        
        for dataset_name, data in datasets.items():
            if data.empty:
                continue
            
            # Create expected index
            expected_index = pd.date_range(
                start=data.index.min(),
                end=data.index.max(), 
                freq=frequency
            )
            
            # Find missing timestamps
            missing_timestamps = expected_index.difference(data.index)
            
            if len(missing_timestamps) > 0:
                # Group consecutive missing periods
                gaps = self._group_consecutive_timestamps(missing_timestamps, frequency)
                
                for gap in gaps:
                    missing_periods.append({
                        'dataset': dataset_name,
                        'start': gap['start'],
                        'end': gap['end'],
                        'duration': gap['duration'],
                        'missing_points': gap['points']
                    })
        
        return missing_periods
    
    def _group_consecutive_timestamps(
        self, 
        timestamps: pd.DatetimeIndex, 
        frequency: str
    ) -> List[Dict[str, Any]]:
        """Group consecutive timestamps into periods"""
        
        if len(timestamps) == 0:
            return []
        
        gaps = []
        current_start = timestamps[0]
        current_end = timestamps[0]
        freq_delta = pd.Timedelta(frequency)
        
        for i in range(1, len(timestamps)):
            if timestamps[i] == current_end + freq_delta:
                current_end = timestamps[i]
            else:
                # Gap in sequence
                gaps.append({
                    'start': current_start,
                    'end': current_end,
                    'duration': current_end - current_start + freq_delta,
                    'points': len(pd.date_range(current_start, current_end, freq=frequency))
                })
                current_start = timestamps[i]
                current_end = timestamps[i]
        
        # Add the last gap
        gaps.append({
            'start': current_start,
            'end': current_end,
            'duration': current_end - current_start + freq_delta,
            'points': len(pd.date_range(current_start, current_end, freq=frequency))
        })
        
        return gaps
    
    def _calculate_trend(self, data: Union[pd.Series, pd.DataFrame]) -> Dict[str, float]:
        """Calculate trend (slope) in data over time"""
        
        if isinstance(data, pd.DataFrame):
            trends = {}
            for col in data.columns:
                col_data = data[col].dropna()
                if len(col_data) > 1:
                    x = np.arange(len(col_data))
                    slope = np.polyfit(x, col_data.values, 1)[0]
                    trends[col] = slope
                else:
                    trends[col] = 0
            return trends
        else:
            data = data.dropna()
            if len(data) > 1:
                x = np.arange(len(data))
                slope = np.polyfit(x, data.values, 1)[0]
                return {'trend': slope}
            else:
                return {'trend': 0}
    
    def _generate_equipment_stats(
        self,
        working_strings_per_level: Dict[str, pd.DataFrame],
        dc_capacity_per_level: Dict[str, pd.DataFrame], 
        equipment_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Generate equipment statistics summary"""
        
        stats = {}
        
        # String-level statistics
        if 'channel' in working_strings_per_level:
            string_stats = working_strings_per_level['channel']
            stats['string_level'] = {
                'total_strings': len(string_stats),
                'working_strings': string_stats.sum(),
                'working_percentage': (string_stats.sum() / len(string_stats)) * 100,
                'non_working_strings': len(string_stats) - string_stats.sum()
            }
        
        # Combiner box level statistics  
        if 'combiner_box' in working_strings_per_level:
            cb_stats = working_strings_per_level['combiner_box']
            stats['combiner_box_level'] = {
                'total_combiner_boxes': len(cb_stats),
                'avg_strings_per_cb': cb_stats.mean(),
                'min_strings_per_cb': cb_stats.min(),
                'max_strings_per_cb': cb_stats.max()
            }
        
        # Capacity statistics
        if dc_capacity_per_level:
            total_capacity = 0
            working_capacity = 0
            
            for level, capacity_data in dc_capacity_per_level.items():
                if isinstance(capacity_data, pd.Series):
                    working_capacity += capacity_data.sum()
                    # Estimate total capacity (this would need actual installed capacity data)
                    total_capacity += capacity_data.sum()  # Simplified assumption
            
            stats['capacity'] = {
                'total_dc_capacity_kw': total_capacity,
                'working_dc_capacity_kw': working_capacity,
                'capacity_utilization_percent': (working_capacity / total_capacity) * 100 if total_capacity > 0 else 0
            }
        
        return stats
    
    def _calculate_plant_health_score(self, performance_summary: Dict[str, Any]) -> float:
        """Calculate overall plant health score"""
        
        # This is a simplified health score calculation
        # In practice, this would be weighted based on business priorities
        
        health_factors = []
        
        # Data availability factor
        if 'availability' in performance_summary:
            availability = performance_summary['availability'].get('mean', 0)
            health_factors.append(availability)
        
        # Performance ratio factor
        if 'pr_monthly' in performance_summary:
            pr_mean = performance_summary['pr_monthly'].get('mean', 0)
            # Assume good PR is around 0.85, excellent is 0.90+
            pr_score = min(pr_mean / 0.85 * 100, 100) if pr_mean > 0 else 0
            health_factors.append(pr_score)
        
        # Equipment working factor
        if 'working_equipment_stats' in performance_summary:
            working_pct = performance_summary['working_equipment_stats'].get('working_percentage', 0)
            health_factors.append(working_pct)
        
        # Calculate overall score
        if health_factors:
            return np.mean(health_factors)
        else:
            return 0.0
