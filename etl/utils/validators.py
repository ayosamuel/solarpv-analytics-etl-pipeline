"""
Data validation utilities for ETL operations
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any


def validate_irradiance_data(
    data: pd.Series, 
    min_value: float = 0, 
    max_value: float = 1500
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Validate and clean irradiance data
    
    Args:
        data: Irradiance data series
        min_value: Minimum valid irradiance value
        max_value: Maximum valid irradiance value
    
    Returns:
        Tuple of (cleaned_data, validation_report)
    """
    original_count = len(data)
    
    # Remove negative values
    data = data.copy()
    negative_count = (data < min_value).sum()
    data[data < min_value] = min_value
    
    # Remove unrealistic high values
    high_count = (data > max_value).sum()
    data[data > max_value] = np.nan
    
    # Count null values
    null_count = data.isna().sum()
    
    validation_report = {
        'original_count': original_count,
        'negative_values_corrected': negative_count,
        'high_values_removed': high_count,
        'null_values': null_count,
        'valid_percentage': ((original_count - null_count) / original_count * 100) if original_count > 0 else 0
    }
    
    return data, validation_report


def validate_temperature_data(
    data: pd.Series, 
    min_value: float = -20, 
    max_value: float = 70
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Validate and clean temperature data
    
    Args:
        data: Temperature data series
        min_value: Minimum valid temperature
        max_value: Maximum valid temperature
    
    Returns:
        Tuple of (cleaned_data, validation_report)
    """
    original_count = len(data)
    
    data = data.copy()
    
    # Remove unrealistic values
    low_count = (data < min_value).sum()
    high_count = (data > max_value).sum()
    
    data[(data < min_value) | (data > max_value)] = np.nan
    
    null_count = data.isna().sum()
    
    validation_report = {
        'original_count': original_count,
        'low_values_removed': low_count,
        'high_values_removed': high_count,
        'null_values': null_count,
        'valid_percentage': ((original_count - null_count) / original_count * 100) if original_count > 0 else 0
    }
    
    return data, validation_report


def validate_power_data(
    data: pd.Series, 
    min_value: float = 0
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Validate and clean power data
    
    Args:
        data: Power data series
        min_value: Minimum valid power value
    
    Returns:
        Tuple of (cleaned_data, validation_report)
    """
    original_count = len(data)
    
    data = data.copy()
    
    # Remove negative values
    negative_count = (data < min_value).sum()
    data[data < min_value] = 0
    
    null_count = data.isna().sum()
    
    validation_report = {
        'original_count': original_count,
        'negative_values_corrected': negative_count,
        'null_values': null_count,
        'valid_percentage': ((original_count - null_count) / original_count * 100) if original_count > 0 else 0
    }
    
    return data, validation_report


def detect_frozen_values(
    data: pd.Series, 
    threshold: int = 4
) -> pd.Series:
    """
    Detect frozen (stuck) values in time series data
    
    Args:
        data: Time series data
        threshold: Minimum consecutive identical values to consider frozen
    
    Returns:
        Boolean series indicating frozen values
    """
    # Find consecutive identical values
    diff = data.diff()
    is_same = (diff == 0)
    
    # Group consecutive same values
    groups = (is_same != is_same.shift()).cumsum()
    group_sizes = is_same.groupby(groups).transform('sum')
    
    # Mark as frozen if consecutive identical values exceed threshold
    return (is_same & (group_sizes >= threshold))


def validate_datetime_index(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate DataFrame has proper datetime index
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Tuple of (is_valid, message)
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return False, "Index is not a DatetimeIndex"
    
    if df.index.has_duplicates:
        return False, "Index has duplicate values"
    
    if not df.index.is_monotonic_increasing:
        return False, "Index is not sorted"
    
    return True, "Valid datetime index"