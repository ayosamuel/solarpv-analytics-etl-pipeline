"""
Data aggregation functions for solar plant analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger
from ..utils.helpers import aggregate_dataframe


class DataAggregator:
    """Main data aggregation class for solar plant data"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def aggregate_time_series(
        self,
        data: Union[pd.DataFrame, pd.Series],
        resolution: str = 'd',
        method: str = 'sum',
        min_periods: int = 1
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        Aggregate time series data by specified resolution
        
        Args:
            data: Input time series data
            resolution: Time resolution ('d' for daily, 'm' for monthly, 'h' for hourly)
            method: Aggregation method ('sum', 'mean', 'max', 'min')
            min_periods: Minimum number of periods required for aggregation
        
        Returns:
            Aggregated data
        """
        self.logger.info(f"Aggregating data to {resolution} resolution using {method}")
        
        if resolution == 'd':
            grouper = data.groupby(data.index.date)
        elif resolution == 'm':
            grouper = data.groupby([data.index.year, data.index.month])
        elif resolution == 'h':
            grouper = data.groupby([data.index.date, data.index.hour])
        elif resolution == 'w':
            grouper = data.groupby(pd.Grouper(freq='W'))
        else:
            raise ValueError(f"Unsupported resolution: {resolution}")
        
        # Apply aggregation method
        if method == 'sum':
            result = grouper.sum(min_count=min_periods)
        elif method == 'mean':
            result = grouper.mean()
        elif method == 'max':
            result = grouper.max()
        elif method == 'min':
            result = grouper.min()
        elif method == 'count':
            result = grouper.count()
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")
        
        # Handle monthly aggregation index naming
        if resolution == 'm' and hasattr(result.index, 'set_names'):
            result.index.set_names(['year', 'month'], inplace=True)
        
        return result
    
    def aggregate_multiple_series(
        self,
        data_dict: Dict[str, pd.DataFrame],
        resolution: str = 'd',
        methods: Dict[str, str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Aggregate multiple data series with different methods
        
        Args:
            data_dict: Dictionary of DataFrames to aggregate
            resolution: Time resolution
            methods: Dictionary mapping data types to aggregation methods
        
        Returns:
            Dictionary of aggregated DataFrames
        """
        if methods is None:
            methods = {
                'power': 'sum',
                'energy': 'sum',
                'irradiance': 'mean',
                'temperature': 'mean',
                'voltage': 'mean',
                'current': 'mean'
            }
        
        aggregated_data = {}
        
        for key, df in data_dict.items():
            method = methods.get(key, 'mean')
            aggregated_data[key] = self.aggregate_time_series(df, resolution, method)
            
        return aggregated_data
    
    def calculate_availability(
        self,
        data: pd.DataFrame,
        resolution: str = 'd',
        data_resolution: int = 5
    ) -> pd.DataFrame:
        """
        Calculate data availability percentages
        
        Args:
            data: Input DataFrame
            resolution: Aggregation resolution
            data_resolution: Original data resolution in minutes
        
        Returns:
            DataFrame with availability percentages
        """
        self.logger.info(f"Calculating data availability at {resolution} resolution")
        
        if resolution == 'd':
            expected_points = (24 * 60) // data_resolution
            grouped = data.groupby(data.index.date)
        elif resolution == 'm':
            # Approximate monthly expected points (varying by month)
            days_in_month = data.index.to_series().dt.days_in_month
            expected_points = (days_in_month * 24 * 60) // data_resolution
            grouped = data.groupby([data.index.year, data.index.month])
        else:
            raise ValueError(f"Unsupported resolution for availability: {resolution}")
        
        # Count non-null values
        counts = grouped.count()
        
        if resolution == 'd':
            availability = (counts / expected_points * 100).fillna(0)
        else:
            # For monthly, calculate average availability
            availability = counts.copy()
            for idx in counts.index:
                year, month = idx
                month_data = data[(data.index.year == year) & (data.index.month == month)]
                days_in_month = pd.Timestamp(year, month, 1).days_in_month
                expected = (days_in_month * 24 * 60) // data_resolution
                availability.loc[idx] = counts.loc[idx] / expected * 100
        
        return availability.clip(0, 100)
    
    def aggregate_performance_metrics(
        self,
        metrics_data: Dict[str, pd.DataFrame],
        resolution: str = 'm'
    ) -> pd.DataFrame:
        """
        Aggregate performance metrics with appropriate methods
        
        Args:
            metrics_data: Dictionary containing performance metrics
            resolution: Time resolution for aggregation
        
        Returns:
            Aggregated performance metrics DataFrame
        """
        self.logger.info("Aggregating performance metrics")
        
        aggregation_methods = {
            'performance_ratio': 'mean',
            'capacity_factor': 'mean',
            'specific_yield': 'sum',
            'total_power': 'sum',
            'total_energy': 'sum',
            'irradiance': 'mean',
            'availability': 'mean'
        }
        
        aggregated_metrics = {}
        
        for metric_name, df in metrics_data.items():
            method = aggregation_methods.get(metric_name, 'mean')
            
            if isinstance(df, pd.Series):
                aggregated_metrics[metric_name] = self.aggregate_time_series(
                    df, resolution, method
                )
            else:
                # For DataFrames, aggregate each column
                metric_agg = {}
                for col in df.columns:
                    metric_agg[col] = self.aggregate_time_series(
                        df[col], resolution, method
                    )
                aggregated_metrics[metric_name] = pd.DataFrame(metric_agg)
        
        return aggregated_metrics


class PlantLevelAggregator(DataAggregator):
    """Aggregator for plant-level metrics and reports"""
    
    def aggregate_to_plant_level(
        self,
        section_data: Dict[str, pd.DataFrame],
        capacity_weights: Dict[str, float] = None
    ) -> pd.DataFrame:
        """
        Aggregate section-level data to plant level
        
        Args:
            section_data: Dictionary of section-level DataFrames
            capacity_weights: Weights for capacity-weighted averaging
        
        Returns:
            Plant-level aggregated DataFrame
        """
        self.logger.info("Aggregating to plant level")
        
        if not section_data:
            return pd.DataFrame()
        
        # Get common time index
        all_indices = [df.index for df in section_data.values() if not df.empty]
        if not all_indices:
            return pd.DataFrame()
        
        common_index = all_indices[0]
        for idx in all_indices[1:]:
            common_index = common_index.intersection(idx)
        
        plant_metrics = {}
        
        for metric_name, section_df in section_data.items():
            if section_df.empty:
                continue
                
            # Align to common index
            aligned_df = section_df.reindex(common_index)
            
            if capacity_weights:
                # Capacity-weighted average for ratios/efficiencies
                if metric_name in ['performance_ratio', 'efficiency', 'capacity_factor']:
                    weighted_values = pd.Series(0, index=common_index)
                    total_weight = 0
                    
                    for section in aligned_df.columns:
                        if section in capacity_weights:
                            weight = capacity_weights[section]
                            weighted_values += aligned_df[section] * weight
                            total_weight += weight
                    
                    plant_metrics[metric_name] = weighted_values / total_weight if total_weight > 0 else weighted_values
                else:
                    # Sum for absolute values (power, energy)
                    plant_metrics[metric_name] = aligned_df.sum(axis=1)
            else:
                # Simple operations without weights
                if metric_name in ['performance_ratio', 'efficiency', 'capacity_factor']:
                    plant_metrics[metric_name] = aligned_df.mean(axis=1)
                else:
                    plant_metrics[metric_name] = aligned_df.sum(axis=1)
        
        return pd.DataFrame(plant_metrics)
    
    def generate_summary_statistics(
        self,
        data: pd.DataFrame,
        metrics: List[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate summary statistics for plant data
        
        Args:
            data: Plant-level data
            metrics: List of metrics to calculate statistics for
        
        Returns:
            Dictionary of summary statistics
        """
        if metrics is None:
            metrics = data.columns.tolist()
        
        summary = {}
        
        for metric in metrics:
            if metric in data.columns:
                series = data[metric].dropna()
                
                summary[metric] = {
                    'mean': series.mean(),
                    'median': series.median(),
                    'std': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'count': len(series),
                    'p25': series.quantile(0.25),
                    'p75': series.quantile(0.75)
                }
        
        return summary