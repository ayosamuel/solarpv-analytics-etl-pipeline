"""
Data cleaning functions for solar plant data
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Union, List, Any

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger
from ..utils.validators import (
    validate_irradiance_data,
    validate_temperature_data, 
    validate_power_data,
    detect_frozen_values
)


class DataCleaner:
    """Main data cleaning class for solar plant data"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def clean_series(
        self,
        data: pd.DataFrame,
        data_type: str = 'general',
        resolution: int = 5,
        apply_smoothing: bool = False,
        sensitivity: float = 1.1
    ) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        Clean time series data with appropriate filters for data type
        
        Args:
            data: Input DataFrame
            data_type: Type of data ('irr', 'temp', 'meter', 'inv', 'general')
            resolution: Data resolution in minutes
            apply_smoothing: Whether to apply smoothing
            sensitivity: Sensitivity for outlier detection
        
        Returns:
            Tuple of (cleaned_data, cleaning_report)
        """
        self.logger.info(f"Cleaning {data_type} data with {len(data.columns)} series")
        
        cleaning_params = self.config.get_cleaning_params()
        cleaned_series = {}
        cleaning_reports = {}
        
        for column in data.columns:
            series = data[column].copy()
            
            if data_type == 'irr':
                cleaned, report = self._clean_irradiance_series(series, cleaning_params)
            elif data_type == 'temp':
                cleaned, report = self._clean_temperature_series(series, cleaning_params)
            elif data_type in ['meter', 'inv']:
                cleaned, report = self._clean_power_series(series, cleaning_params)
            else:
                cleaned, report = self._clean_general_series(series, cleaning_params)
            
            # Remove frozen values
            if data_type != 'general':
                frozen_mask = detect_frozen_values(
                    cleaned, 
                    threshold=cleaning_params.get('frozen_threshold', 4)
                )
                cleaned[frozen_mask] = np.nan
                report['frozen_values_removed'] = frozen_mask.sum()
            
            cleaned_series[column] = cleaned
            cleaning_reports[column] = report
        
        cleaned_df = pd.DataFrame(cleaned_series)
        
        # Generate summary report
        summary_report = self._generate_cleaning_summary(cleaning_reports)
        
        self.logger.info(f"Cleaning completed. Overall data quality: {summary_report['overall_quality']:.1f}%")
        
        return cleaned_df, summary_report
    
    def _clean_irradiance_series(
        self, 
        series: pd.Series, 
        params: Dict[str, any]
    ) -> Tuple[pd.Series, Dict[str, any]]:
        """Clean irradiance data series"""
        return validate_irradiance_data(
            series,
            min_value=params.get('irradiance_min', 0),
            max_value=params.get('irradiance_max', 1500)
        )
    
    def _clean_temperature_series(
        self, 
        series: pd.Series, 
        params: Dict[str, any]
    ) -> Tuple[pd.Series, Dict[str, any]]:
        """Clean temperature data series"""
        return validate_temperature_data(
            series,
            min_value=params.get('temperature_min', -20),
            max_value=params.get('temperature_max', 70)
        )
    
    def _clean_power_series(
        self, 
        series: pd.Series, 
        params: Dict[str, any]
    ) -> Tuple[pd.Series, Dict[str, any]]:
        """Clean power data series"""
        return validate_power_data(series, min_value=0)
    
    def _clean_general_series(
        self, 
        series: pd.Series, 
        params: Dict[str, any]
    ) -> Tuple[pd.Series, Dict[str, any]]:
        """Clean general data series"""
        original_count = len(series)
        cleaned = series.copy()
        null_count = cleaned.isna().sum()
        
        report = {
            'original_count': original_count,
            'null_values': null_count,
            'valid_percentage': ((original_count - null_count) / original_count * 100) if original_count > 0 else 0
        }
        
        return cleaned, report
    
    def _generate_cleaning_summary(self, reports: Dict[str, Dict[str, any]]) -> Dict[str, any]:
        """Generate summary cleaning report"""
        if not reports:
            return {'overall_quality': 0, 'series_count': 0}
        
        total_quality = sum(report.get('valid_percentage', 0) for report in reports.values())
        avg_quality = total_quality / len(reports)
        
        total_original = sum(report.get('original_count', 0) for report in reports.values())
        total_null = sum(report.get('null_values', 0) for report in reports.values())
        
        return {
            'series_count': len(reports),
            'overall_quality': avg_quality,
            'total_records': total_original,
            'total_null_values': total_null,
            'series_reports': reports
        }


class IrradianceCleaner(DataCleaner):
    """Specialized cleaner for irradiance data"""
    
    def clean_irradiance_advanced(
        self,
        gti: pd.DataFrame,
        ghi: pd.DataFrame = None,
        export_levels: bool = False
    ) -> Union[pd.Series, Tuple[pd.Series, Dict[str, any]]]:
        """
        Advanced irradiance cleaning with multiple sensors
        
        Args:
            gti: Global Tilted Irradiance data
            ghi: Global Horizontal Irradiance data (optional)
            export_levels: Whether to export detailed cleaning info
        
        Returns:
            Cleaned irradiance series or tuple with cleaning details
        """
        self.logger.info("Starting advanced irradiance cleaning")
        
        # Clean individual series
        gti_cleaned, gti_report = self.clean_series(gti, data_type='irr')
        
        # Calculate average from multiple sensors
        gti_mean = gti_cleaned.mean(axis=1)
        gti_max = gti_cleaned.max(axis=1)
        gti_min = gti_cleaned.min(axis=1)
        
        # Remove cases where minimum is 0 (indicating sensor issues)
        gti_mean[gti_min == 0] = 0
        
        # Use maximum value when average is significantly reduced by faulty sensor
        sensor_ratio = gti_mean / gti_max
        gti_final = np.where(sensor_ratio < 0.7, gti_max, gti_mean)
        gti_final = pd.Series(gti_final, index=gti_mean.index)
        
        # Final validation
        gti_final[gti_final < 0] = 0
        
        self.logger.info("Advanced irradiance cleaning completed")
        
        if export_levels:
            cleaning_details = {
                'original_report': gti_report,
                'final_mean': gti_mean,
                'final_max': gti_max,
                'final_min': gti_min,
                'sensor_issues_detected': (sensor_ratio < 0.7).sum()
            }
            return gti_final, cleaning_details
        
        return gti_final

    def clean_irradiance_with_frozen_detection(
        self,
        irr: pd.DataFrame,
        export_detailed_levels: bool = False
    ) -> Union[pd.Series, Tuple[pd.Series, Dict[str, Any]]]:
        """
        Advanced irradiance cleaning with frozen sensor detection
        
        Consolidates patterns from:
        - Study015_Irradiation_General_v01.py 
        - Study016_Yield_General_v01.py
        - Multiple irradiance_Clean_final() implementations
        """
        self.logger.info("Starting advanced irradiance cleaning with frozen detection")
        
        # Generate complete time range
        date_range = pd.date_range(irr.index[0], irr.index[-1], freq='5Min')
        complete_points = pd.DataFrame(index=date_range)
        complete_points['data'] = 1
        
        # Calculate data availability
        complete_day = complete_points.groupby(complete_points.index.date).count()
        complete_month = complete_points.groupby([
            complete_points.index.year, 
            complete_points.index.month
        ]).count()
        
        irr_day = irr.groupby(irr.index.date).count()
        irr_month = irr.groupby([irr.index.year, irr.index.month]).count()
        
        # Data availability statistics
        availability_stats = {}
        for sensor in irr.columns:
            availability_stats[sensor] = {
                'daily': irr_day[sensor] / complete_day['data'],
                'monthly': irr_month[sensor] / complete_month['data']
            }
        
        # Level 1: Remove false zeros and calculate deviations
        avg_irr = irr.mean(axis=1)
        irr_clean_l01 = irr.copy()
        
        # Remove false zeros (when sensor shows 0 but others show significant values)
        for sensor in irr.columns:
            zero_indices = irr[sensor][irr[sensor] == 0].index
            false_zero_indices = avg_irr.loc[zero_indices][avg_irr.loc[zero_indices] > 3].index
            irr_clean_l01[sensor].loc[false_zero_indices] = np.nan
        
        # Level 2: Deviation-based filtering
        avg_irr_l01 = irr_clean_l01.mean(axis=1)
        deviation_df = []
        
        for sensor in irr.columns:
            deviation = np.where(
                avg_irr_l01 > 0,
                abs(irr_clean_l01[sensor] - avg_irr_l01) / avg_irr_l01,
                0
            )
            deviation_df.append(pd.Series(deviation, index=irr.index))
        
        deviation_df = pd.concat(deviation_df, axis=1)
        deviation_df.columns = irr.columns
        
        # Create mask for deviations > 10%
        irr_mask = deviation_df.copy()
        irr_mask[abs(irr_mask[irr_mask.count(axis=1) > 2]) > 0.1] = np.nan
        irr_mask[irr_mask.notnull()] = 1
        
        # Apply mask
        irr_clean_l02 = []
        for sensor in irr.columns:
            irr_clean_l02.append(irr_clean_l01[sensor] * irr_mask[sensor])
        irr_clean_l02 = pd.concat(irr_clean_l02, axis=1)
        
        # Level 3: Frozen sensor detection
        frozen_masks = []
        irr_clean_l03 = []
        irr_clean_l04 = []
        
        for sensor in irr.columns:
            self.logger.debug(f"Processing frozen detection for {sensor}")
            
            # Get non-null positive values
            temp_irr = irr_clean_l02[sensor][irr_clean_l02[sensor].notnull()]
            aux_irr = temp_irr[temp_irr > 0]
            
            if len(aux_irr) < 3:
                # Not enough data
                frozen_masks.append(pd.Series(1, index=aux_irr.index))
                irr_clean_l04.append(aux_irr)
                continue
            
            # Detect frozen readings (consecutive identical values)
            frozen_mask = []
            for i in range(len(aux_irr)):
                if i == 0:
                    frozen_mask.append(1)  # First value is always valid
                elif i == len(aux_irr) - 1:
                    frozen_mask.append(1)  # Last value is always valid
                else:
                    # Check if current value differs from both previous and next
                    current = aux_irr.iloc[i]
                    previous = aux_irr.iloc[i-1]
                    next_val = aux_irr.iloc[i+1]
                    
                    if current != previous or current != next_val:
                        frozen_mask.append(1)  # Not frozen
                    else:
                        frozen_mask.append(0)  # Potentially frozen
            
            frozen_mask_series = pd.Series(frozen_mask, index=aux_irr.index)
            frozen_masks.append(frozen_mask_series)
            
            # Apply frozen mask
            irr_clean_l04.append(aux_irr * frozen_mask_series)
            irr_clean_l03.append(temp_irr)
        
        # Combine cleaned data
        irr_clean_final = pd.concat(irr_clean_l04, axis=1)
        irr_clean_final.columns = irr.columns
        
        # Calculate final average
        irr_final = irr_clean_final.mean(axis=1)
        
        # Calculate data loss
        irr_final_dataloss = avg_irr_l01.groupby(avg_irr_l01.index.date).count() / 288
        irr_final_dataloss.index = pd.to_datetime(irr_final_dataloss.index)
        
        self.logger.info(f"Advanced cleaning completed. Final data points: {len(irr_final)}")
        
        if export_detailed_levels:
            cleaning_details = {
                'availability_stats': availability_stats,
                'level1_cleaned': irr_clean_l01,
                'level2_cleaned': irr_clean_l02,
                'level3_cleaned': irr_clean_l03,
                'final_cleaned': irr_clean_final,
                'frozen_masks': pd.concat(frozen_masks, axis=1),
                'deviation_stats': deviation_df,
                'data_loss': irr_final_dataloss
            }
            return irr_final, cleaning_details
        
        return irr_final
    
    def clean_scaldia_irradiance(
        self,
        gti_all: pd.DataFrame,
        azimuth_weights: Optional[Dict[str, float]] = None
    ) -> pd.Series:
        """
        Specialized cleaning for Scaldia-type multi-azimuth installations
        
        Consolidates irradiance_Clean_Scaldia() patterns from specific_functions.py
        """
        
        if azimuth_weights is None:
            # Default weights from Scaldia project
            azimuth_weights = {
                'AH.East': 0.232,
                'AH.West': 0.231, 
                'F.East': 0.153,
                'F.West': 0.152,
                'M.East': 0.0367,
                'M.West': 0.0365,
                'O.East': 0.137,
                'O.West': 0.134
            }
        
        self.logger.info("Applying Scaldia-specific irradiance cleaning")
        
        # Group sensors by azimuth
        irr_dict = {}
        
        # East/West combinations
        if 'A_2.east' in gti_all.columns or 'H.east' in gti_all.columns:
            east_ah = []
            if 'A_2.east' in gti_all.columns:
                east_ah.append(self._filter_columns(gti_all, 'A_2.east'))
            if 'H.east' in gti_all.columns:
                east_ah.append(self._filter_columns(gti_all, 'H.east'))
            if east_ah:
                irr_dict['AH.East'] = pd.concat(east_ah, axis=1).mean(axis=1)
        
        if 'A_2.west' in gti_all.columns or 'H.west' in gti_all.columns:
            west_ah = []
            if 'A_2.west' in gti_all.columns:
                west_ah.append(self._filter_columns(gti_all, 'A_2.west'))
            if 'H.west' in gti_all.columns:
                west_ah.append(self._filter_columns(gti_all, 'H.west'))
            if west_ah:
                irr_dict['AH.West'] = pd.concat(west_ah, axis=1).mean(axis=1)
        
        # Other orientations
        for orientation in ['F.east', 'F.west', 'M.east', 'M.west', 'O_2.east', 'O_2.west']:
            filtered = self._filter_columns(gti_all, orientation)
            if not filtered.empty:
                key = orientation.replace('O_2', 'O').replace('.', '.').title()
                irr_dict[key] = filtered.mean(axis=1)
        
        # Apply weights and combine
        weighted_irr = []
        for azimuth, weight in azimuth_weights.items():
            if azimuth in irr_dict:
                weighted_irr.append(irr_dict[azimuth] * weight)
        
        if not weighted_irr:
            raise ValueError("No matching azimuth data found")
        
        result = pd.concat(weighted_irr, axis=1).sum(axis=1)
        
        self.logger.info(f"Scaldia cleaning completed with {len(weighted_irr)} azimuth groups")
        return result
    
    def _filter_columns(self, df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """Helper method to filter dataframe columns by keyword"""
        matching_cols = [col for col in df.columns if keyword in col]
        return df[matching_cols] if matching_cols else pd.DataFrame()


class WorkingChannelDetector:
    """Detect working channels in solar plant equipment"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def detect_working_channels(
        self,
        current_data: pd.DataFrame,
        sensitivity: float = 1.0,
        module_current: float = 9.0,
        max_current: float = 30.0
    ) -> pd.Series:
        """
        Detect working channels based on current measurements
        
        Args:
            current_data: DataFrame with current measurements
            sensitivity: Detection sensitivity
            module_current: Expected module current
            max_current: Maximum valid current
        
        Returns:
            Series indicating working channels per string
        """
        self.logger.info(f"Detecting working channels from {len(current_data.columns)} channels")
        
        # Filter out unrealistic high values
        filtered_data = current_data[current_data < max_current]
        
        # Get maximum current per channel
        max_string_current = filtered_data.max()
        max_string_current = max_string_current[max_string_current > 1]
        
        # Calculate monthly maxima to detect false positives
        monthly_max = filtered_data.groupby([
            filtered_data.index.year, 
            filtered_data.index.month
        ]).max()
        
        false_positives = monthly_max[monthly_max < 1].count()
        false_positives = false_positives[false_positives > (len(monthly_max) * 0.9)]
        
        total_max_current = filtered_data.max().max()
        
        # Determine strings per channel based on current levels
        limit = 0.6
        
        if (max_string_current.mean() < (total_max_current * limit)) or \
           (max_string_current.mean() > module_current * 1.2):
            # Multi-string configuration
            strings_per_channel = pd.Series(
                np.where(
                    max_string_current > total_max_current * limit, 2,
                    np.where(max_string_current > total_max_current * 0.2, 1, 0)
                )
            )
        else:
            # Single string configuration
            strings_per_channel = pd.Series(
                np.where(max_string_current > total_max_current * 0.4, 1, 0)
            )
        
        strings_per_channel.index = max_string_current.index
        
        # Filter out false positives
        working_channels = strings_per_channel[strings_per_channel > 0]
        working_channels = working_channels.drop(
            false_positives.index.intersection(working_channels.index)
        )
        
        self.logger.info(f"Detected {len(working_channels)} working channels")
        
        return working_channels