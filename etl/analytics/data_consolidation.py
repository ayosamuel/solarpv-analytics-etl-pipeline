"""
Data Consolidation and Multi-Source Loading

Consolidates data loading patterns found across Study files:
- Multi-year CSV file loading and concatenation
- Cross-platform file path handling
- Data source validation and consistency checking
"""

import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging

from ..utils.logging import setup_logger
from ..utils.config import ConfigManager


@dataclass
class DataSourceInfo:
    """Information about a data source"""
    file_path: str
    data_type: str  # 'meter', 'inverter', 'irradiance', etc.
    year: int
    month_range: Tuple[int, int] = None
    data_quality: float = None  # Data availability percentage
    row_count: int = None
    date_range: Tuple[pd.Timestamp, pd.Timestamp] = None


@dataclass
class ConsolidationResults:
    """Results from data consolidation process"""
    consolidated_data: pd.DataFrame
    source_info: List[DataSourceInfo]
    data_gaps: pd.DataFrame
    quality_metrics: Dict[str, Any]
    warnings: List[str]


class MultiSourceDataLoader:
    """
    Handles loading and consolidation of data from multiple sources
    
    Consolidates loading patterns from:
    - Study043_Gorontalo_v03.py: Multi-year meter data loading
    - Study049_Isoma_Stefani_Hdown_v02.py: Multi-file status data
    - Study040_Vloeivelden_Performance_Check_v05.py: Additional data sources
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def load_multi_year_data(
        self,
        base_paths: Dict[int, str],  # year -> path mapping
        data_type: str,
        file_pattern: str = "*.csv",
        header: int = 0,
        skiprows: List[int] = None,
        validate_consistency: bool = True
    ) -> ConsolidationResults:
        """
        Load and consolidate data from multiple years
        
        Replaces repetitive multi-year loading patterns found in:
        - Gorontalo meter data loading (2020, 2021, 2022, 2023)
        - Isoma CB status data loading across years
        """
        self.logger.info(f"Loading multi-year {data_type} data from {len(base_paths)} years")
        
        yearly_data = {}
        source_info = []
        warnings = []
        
        for year, base_path in base_paths.items():
            try:
                year_data, year_sources, year_warnings = self._load_year_data(
                    base_path, year, data_type, file_pattern, header, skiprows
                )
                
                if not year_data.empty:
                    yearly_data[year] = year_data
                    source_info.extend(year_sources)
                    warnings.extend(year_warnings)
                else:
                    warnings.append(f"No data loaded for year {year}")
                    
            except Exception as e:
                error_msg = f"Failed to load data for year {year}: {str(e)}"
                self.logger.error(error_msg)
                warnings.append(error_msg)
        
        if not yearly_data:
            raise ValueError("No data could be loaded from any source")
        
        # Consolidate yearly data
        consolidated_data = pd.concat(yearly_data.values(), sort=True)
        consolidated_data = consolidated_data.sort_index()
        
        # Remove duplicates if any
        if consolidated_data.index.duplicated().any():
            duplicates_count = consolidated_data.index.duplicated().sum()
            warnings.append(f"Removed {duplicates_count} duplicate timestamps")
            consolidated_data = consolidated_data[~consolidated_data.index.duplicated(keep='first')]
        
        # Validate consistency across years if requested
        if validate_consistency:
            consistency_warnings = self._validate_data_consistency(yearly_data)
            warnings.extend(consistency_warnings)
        
        # Detect data gaps
        data_gaps = self._detect_data_gaps(consolidated_data)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(consolidated_data, source_info)
        
        return ConsolidationResults(
            consolidated_data=consolidated_data,
            source_info=source_info,
            data_gaps=data_gaps,
            quality_metrics=quality_metrics,
            warnings=warnings
        )
    
    def load_additional_data_sources(
        self,
        additional_sources: Dict[str, str],  # source_name -> file_path
        main_data_index: pd.DatetimeIndex,
        interpolation_method: str = 'linear'
    ) -> Dict[str, pd.DataFrame]:
        """
        Load additional data sources and align with main dataset
        
        Handles cases like:
        - Vloeivelden additional inverter/meteo/setpoint data
        - Gorontalo additional pyranometer data
        """
        self.logger.info(f"Loading {len(additional_sources)} additional data sources")
        
        additional_data = {}
        
        for source_name, file_path in additional_sources.items():
            try:
                # Load data
                if file_path.endswith('.csv'):
                    data = pd.read_csv(file_path, index_col=0, parse_dates=True)
                else:
                    raise ValueError(f"Unsupported file format for {file_path}")
                
                # Align with main dataset index
                aligned_data = self._align_with_main_index(
                    data, main_data_index, interpolation_method
                )
                
                additional_data[source_name] = aligned_data
                
                self.logger.info(f"Loaded {source_name}: {len(aligned_data)} records")
                
            except Exception as e:
                self.logger.error(f"Failed to load {source_name} from {file_path}: {str(e)}")
        
        return additional_data
    
    def consolidate_meter_data(
        self,
        meter_files: Dict[str, str],  # description -> file_path
        energy_columns: List[str] = None,
        power_columns: List[str] = None,
        yield_columns: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Consolidate different types of meter data
        
        Handles patterns from Gorontalo study:
        - Active power (PAC) data
        - Total yield/energy data
        - Different meter measurement types
        """
        self.logger.info(f"Consolidating {len(meter_files)} meter data files")
        
        consolidated_meter_data = {}
        
        for description, file_path in meter_files.items():
            try:
                meter_data = pd.read_csv(file_path, index_col=0, parse_dates=True)
                
                # Extract different types of measurements
                if power_columns:
                    power_data = self._extract_columns_by_pattern(meter_data, power_columns)
                    if not power_data.empty:
                        consolidated_meter_data[f"{description}_power"] = power_data
                
                if energy_columns:
                    energy_data = self._extract_columns_by_pattern(meter_data, energy_columns)
                    if not energy_data.empty:
                        consolidated_meter_data[f"{description}_energy"] = energy_data
                
                if yield_columns:
                    yield_data = self._extract_columns_by_pattern(meter_data, yield_columns)
                    if not yield_data.empty:
                        # Convert to incremental yield if cumulative
                        if self._is_cumulative_data(yield_data):
                            yield_data = yield_data.diff().fillna(0)
                            yield_data[yield_data < 0] = 0  # Handle resets
                        
                        consolidated_meter_data[f"{description}_yield"] = yield_data
                
            except Exception as e:
                self.logger.error(f"Failed to process meter file {description}: {str(e)}")
        
        return consolidated_meter_data
    
    def _load_year_data(
        self,
        base_path: str,
        year: int,
        data_type: str,
        file_pattern: str,
        header: int,
        skiprows: List[int]
    ) -> Tuple[pd.DataFrame, List[DataSourceInfo], List[str]]:
        """Load data for a specific year"""
        
        # Find all files matching pattern
        file_path = Path(base_path)
        if file_path.is_file():
            # Single file provided
            all_files = [str(file_path)]
        else:
            # Directory provided, search for files
            all_files = glob.glob(os.path.join(base_path, file_pattern))
        
        if not all_files:
            return pd.DataFrame(), [], [f"No files found for year {year} in {base_path}"]
        
        year_data_list = []
        source_info = []
        warnings = []
        
        for file_path in all_files:
            try:
                # Load file
                df = pd.read_csv(
                    file_path,
                    header=header,
                    skiprows=skiprows,
                    index_col=0,
                    parse_dates=True
                )
                
                # Clean data
                df = df.astype(float, errors='ignore')
                df = df[:-1] if len(df) > 0 else df  # Remove last row if it's often incomplete
                
                # Validate year
                if not df.empty:
                    file_year = df.index[0].year
                    if file_year != year:
                        warnings.append(f"File {file_path} contains data from year {file_year}, expected {year}")
                
                year_data_list.append(df)
                
                # Create source info
                date_range = (df.index.min(), df.index.max()) if not df.empty else None
                source_info.append(DataSourceInfo(
                    file_path=file_path,
                    data_type=data_type,
                    year=year,
                    row_count=len(df),
                    date_range=date_range,
                    data_quality=self._calculate_file_quality(df)
                ))
                
            except Exception as e:
                warnings.append(f"Failed to load file {file_path}: {str(e)}")
        
        # Combine all files for this year
        if year_data_list:
            year_data = pd.concat(year_data_list, sort=True)
            year_data = year_data.sort_index()
        else:
            year_data = pd.DataFrame()
        
        return year_data, source_info, warnings
    
    def _validate_data_consistency(self, yearly_data: Dict[int, pd.DataFrame]) -> List[str]:
        """Validate consistency across years"""
        
        warnings = []
        
        if len(yearly_data) < 2:
            return warnings
        
        # Check column consistency
        all_columns = [set(df.columns) for df in yearly_data.values()]
        common_columns = set.intersection(*all_columns)
        
        for year, df in yearly_data.items():
            missing_columns = set(df.columns) - common_columns
            if missing_columns:
                warnings.append(f"Year {year} has unique columns: {missing_columns}")
        
        # Check data ranges
        for year, df in yearly_data.items():
            for col in common_columns:
                if df[col].dtype in [np.float64, np.int64]:
                    col_min, col_max = df[col].min(), df[col].max()
                    
                    # Compare with other years
                    for other_year, other_df in yearly_data.items():
                        if other_year != year and col in other_df.columns:
                            other_min, other_max = other_df[col].min(), other_df[col].max()
                            
                            # Check for significant differences (order of magnitude)
                            if abs(col_max - other_max) > max(col_max, other_max) * 0.5:
                                warnings.append(
                                    f"Large difference in {col} max values: {year}={col_max:.2f}, {other_year}={other_max:.2f}"
                                )
        
        return warnings
    
    def _detect_data_gaps(self, data: pd.DataFrame, expected_freq: str = '5min') -> pd.DataFrame:
        """Detect gaps in time series data"""
        
        if data.empty:
            return pd.DataFrame()
        
        # Create expected index
        expected_index = pd.date_range(
            start=data.index.min(),
            end=data.index.max(),
            freq=expected_freq
        )
        
        # Find missing timestamps
        missing_timestamps = expected_index.difference(data.index)
        
        if len(missing_timestamps) == 0:
            return pd.DataFrame()
        
        # Group consecutive missing periods
        gaps = []
        current_gap_start = None
        current_gap_end = None
        
        for timestamp in missing_timestamps:
            if current_gap_start is None:
                current_gap_start = timestamp
                current_gap_end = timestamp
            elif timestamp == current_gap_end + pd.Timedelta(expected_freq):
                current_gap_end = timestamp
            else:
                # Gap in sequence, save current gap
                gaps.append({
                    'start': current_gap_start,
                    'end': current_gap_end,
                    'duration': current_gap_end - current_gap_start + pd.Timedelta(expected_freq),
                    'missing_points': len(pd.date_range(current_gap_start, current_gap_end, freq=expected_freq))
                })
                current_gap_start = timestamp
                current_gap_end = timestamp
        
        # Add the last gap
        if current_gap_start is not None:
            gaps.append({
                'start': current_gap_start,
                'end': current_gap_end,
                'duration': current_gap_end - current_gap_start + pd.Timedelta(expected_freq),
                'missing_points': len(pd.date_range(current_gap_start, current_gap_end, freq=expected_freq))
            })
        
        return pd.DataFrame(gaps)
    
    def _calculate_quality_metrics(
        self, 
        data: pd.DataFrame, 
        source_info: List[DataSourceInfo]
    ) -> Dict[str, Any]:
        """Calculate data quality metrics"""
        
        if data.empty:
            return {'overall_quality': 0}
        
        total_points = len(data)
        missing_points = data.isnull().sum().sum()
        duplicate_points = data.index.duplicated().sum()
        
        # Calculate availability by column
        column_availability = {}
        for col in data.columns:
            available_points = data[col].notna().sum()
            column_availability[col] = (available_points / total_points) * 100
        
        # Calculate temporal coverage
        expected_points = self._calculate_expected_points(data.index)
        temporal_coverage = (total_points / expected_points) * 100 if expected_points > 0 else 0
        
        # Source file statistics
        source_stats = {
            'total_files': len(source_info),
            'years_covered': len(set(info.year for info in source_info)),
            'avg_file_quality': np.mean([info.data_quality for info in source_info if info.data_quality is not None])
        }
        
        return {
            'overall_quality': ((total_points - missing_points) / total_points) * 100,
            'temporal_coverage': temporal_coverage,
            'column_availability': column_availability,
            'missing_points': missing_points,
            'duplicate_points': duplicate_points,
            'total_points': total_points,
            'source_statistics': source_stats
        }
    
    def _calculate_file_quality(self, df: pd.DataFrame) -> float:
        """Calculate quality score for a single file"""
        
        if df.empty:
            return 0.0
        
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        
        return ((total_cells - missing_cells) / total_cells) * 100
    
    def _calculate_expected_points(self, index: pd.DatetimeIndex, freq: str = '5min') -> int:
        """Calculate expected number of data points"""
        
        if len(index) < 2:
            return len(index)
        
        time_span = index.max() - index.min()
        freq_delta = pd.Timedelta(freq)
        
        return int(time_span / freq_delta) + 1
    
    def _align_with_main_index(
        self,
        data: pd.DataFrame,
        main_index: pd.DatetimeIndex,
        method: str = 'linear'
    ) -> pd.DataFrame:
        """Align additional data with main dataset index"""
        
        # Reindex to main index
        aligned_data = data.reindex(main_index)
        
        # Interpolate missing values if requested
        if method and method != 'none':
            aligned_data = aligned_data.interpolate(method=method, limit_direction='both')
        
        return aligned_data
    
    def _extract_columns_by_pattern(self, df: pd.DataFrame, patterns: List[str]) -> pd.DataFrame:
        """Extract columns matching specific patterns"""
        
        selected_columns = []
        
        for pattern in patterns:
            matching_cols = [col for col in df.columns if pattern.lower() in col.lower()]
            selected_columns.extend(matching_cols)
        
        return df[selected_columns] if selected_columns else pd.DataFrame()
    
    def _is_cumulative_data(self, data: pd.DataFrame) -> bool:
        """Check if data appears to be cumulative"""
        
        # Check if values are generally increasing
        for col in data.columns:
            if data[col].dtype in [np.float64, np.int64]:
                # Check if 80% of differences are non-negative
                diffs = data[col].diff().dropna()
                non_negative_ratio = (diffs >= 0).sum() / len(diffs)
                
                if non_negative_ratio < 0.8:
                    return False
        
        return True


class DowntimeAnalyzer:
    """
    Analyze plant downtime and availability
    
    Consolidates downtime analysis patterns from:
    - Study049_Isoma_Stefani_Hdown_v02.py: CB status-based downtime
    - Inverter alarm-based downtime analysis
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def calculate_downtime_from_status(
        self,
        status_data: pd.DataFrame,
        irradiance_data: pd.Series,
        status_column: str = None,
        off_value: Union[int, str] = 0,
        min_irradiance: float = 10
    ) -> Dict[str, Any]:
        """
        Calculate downtime periods based on equipment status
        
        Replicates downtime analysis from Isoma Stefani study
        """
        self.logger.info("Calculating downtime from status data")
        
        if status_column is None:
            status_column = status_data.columns[0]
        
        # Align status and irradiance data
        combined_data = pd.concat([
            status_data[status_column], 
            irradiance_data
        ], axis=1)
        combined_data.columns = ['status', 'irradiance']
        combined_data = combined_data.dropna()
        
        # Identify downtime periods (status = off AND irradiance > threshold)
        downtime_mask = (
            (combined_data['status'] == off_value) & 
            (combined_data['irradiance'] > min_irradiance)
        )
        
        downtime_data = combined_data[downtime_mask]
        
        # Calculate monthly downtime impact
        monthly_downtime = downtime_data.groupby(downtime_data.index.month).agg({
            'irradiance': ['sum', 'count'],
            'status': 'count'
        })
        
        # Calculate total monthly irradiance for comparison
        monthly_total_irr = irradiance_data.groupby(irradiance_data.index.month).sum()
        
        # Calculate downtime impact as percentage
        downtime_impact = {}
        for month in monthly_downtime.index:
            if month in monthly_total_irr.index:
                lost_irradiance = monthly_downtime.loc[month, ('irradiance', 'sum')]
                total_irradiance = monthly_total_irr.loc[month]
                
                downtime_impact[month] = {
                    'lost_irradiance_kwh_m2': lost_irradiance / 12,  # Convert to kWh/m²
                    'downtime_hours': monthly_downtime.loc[month, ('irradiance', 'count')] / 12,
                    'impact_percentage': (lost_irradiance / total_irradiance) * 100 if total_irradiance > 0 else 0
                }
        
        return {
            'monthly_impact': downtime_impact,
            'total_downtime_hours': len(downtime_data) / 12,
            'total_lost_irradiance': downtime_data['irradiance'].sum() / 12,
            'downtime_events': self._identify_downtime_events(downtime_data['irradiance'])
        }
    
    def calculate_downtime_from_alarms(
        self,
        alarm_data: pd.DataFrame,
        irradiance_data: pd.Series,
        power_data: pd.DataFrame = None,
        dc_capacity: float = None
    ) -> Dict[str, Any]:
        """
        Calculate downtime impact from alarm/fault data
        
        Handles alarm log analysis similar to Isoma inverter alarms
        """
        self.logger.info("Calculating downtime from alarm data")
        
        # Ensure required columns exist
        required_columns = ['occurred_round', 'cleared_round', 'Duration_check_seconds']
        missing_columns = [col for col in required_columns if col not in alarm_data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        downtime_periods = []
        total_lost_irradiance = 0
        
        for _, alarm in alarm_data.iterrows():
            start_time = alarm['occurred_round']
            end_time = alarm['cleared_round']
            duration_seconds = alarm['Duration_check_seconds']
            
            # Get irradiance during this period
            period_irradiance = irradiance_data[
                (irradiance_data.index >= start_time) & 
                (irradiance_data.index <= end_time)
            ]
            
            if not period_irradiance.empty:
                lost_irradiance = period_irradiance.sum() / 12  # Convert to kWh/m²
                
                # Calculate lost energy if capacity provided
                lost_energy = None
                if dc_capacity is not None:
                    lost_energy = (lost_irradiance * dc_capacity) / 1000  # kWh
                
                downtime_periods.append({
                    'start': start_time,
                    'end': end_time,
                    'duration_hours': duration_seconds / 3600,
                    'lost_irradiance': lost_irradiance,
                    'lost_energy_kwh': lost_energy,
                    'avg_irradiance': period_irradiance.mean()
                })
                
                total_lost_irradiance += lost_irradiance
        
        # Group by month for summary
        monthly_summary = {}
        for period in downtime_periods:
            month = period['start'].month
            if month not in monthly_summary:
                monthly_summary[month] = {
                    'total_hours': 0,
                    'total_lost_irradiance': 0,
                    'total_lost_energy': 0,
                    'event_count': 0
                }
            
            monthly_summary[month]['total_hours'] += period['duration_hours']
            monthly_summary[month]['total_lost_irradiance'] += period['lost_irradiance']
            monthly_summary[month]['event_count'] += 1
            
            if period['lost_energy_kwh']:
                monthly_summary[month]['total_lost_energy'] += period['lost_energy_kwh']
        
        return {
            'downtime_periods': downtime_periods,
            'monthly_summary': monthly_summary,
            'total_lost_irradiance': total_lost_irradiance,
            'total_events': len(downtime_periods)
        }
    
    def _identify_downtime_events(self, downtime_irradiance: pd.Series) -> List[Dict[str, Any]]:
        """Identify discrete downtime events"""
        
        if downtime_irradiance.empty:
            return []
        
        events = []
        current_event_start = None
        current_event_irradiance = 0
        
        # Group consecutive downtime periods
        for i, (timestamp, irradiance) in enumerate(downtime_irradiance.items()):
            if current_event_start is None:
                current_event_start = timestamp
                current_event_irradiance = irradiance
            elif timestamp == downtime_irradiance.index[i-1] + pd.Timedelta('5min'):
                # Consecutive timestamp
                current_event_irradiance += irradiance
            else:
                # Gap in sequence, save current event
                events.append({
                    'start': current_event_start,
                    'end': downtime_irradiance.index[i-1],
                    'duration': downtime_irradiance.index[i-1] - current_event_start + pd.Timedelta('5min'),
                    'lost_irradiance': current_event_irradiance / 12
                })
                
                current_event_start = timestamp
                current_event_irradiance = irradiance
        
        # Add the last event
        if current_event_start is not None:
            events.append({
                'start': current_event_start,
                'end': downtime_irradiance.index[-1],
                'duration': downtime_irradiance.index[-1] - current_event_start + pd.Timedelta('5min'),
                'lost_irradiance': current_event_irradiance / 12
            })
        
        return events
