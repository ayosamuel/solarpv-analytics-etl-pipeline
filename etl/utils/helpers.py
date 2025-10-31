"""
Helper functions for common ETL operations
"""

import pandas as pd
import numpy as np
from typing import Union, List, Optional
import datetime


def column_filter(df: pd.DataFrame, col_string: str) -> pd.DataFrame:
    """
    Filter DataFrame columns by string pattern
    
    Args:
        df: Input DataFrame
        col_string: String pattern to filter columns
    
    Returns:
        Filtered DataFrame with matching columns
    """
    if col_string == 'None' or col_string is None:
        return df
    
    filtered_df = df[df.columns[df.columns.str.contains(col_string, case=False, na=False)]]
    return filtered_df.sort_index(axis=1)


def column_delete(df: pd.DataFrame, del_string: str) -> pd.DataFrame:
    """
    Delete DataFrame columns matching pattern
    
    Args:
        df: Input DataFrame
        del_string: String pattern to delete columns
    
    Returns:
        DataFrame with matching columns removed
    """
    return df[df.columns.drop(list(df.filter(regex=del_string)))]


def aggregate_dataframe(df: pd.DataFrame, resolution: str) -> pd.DataFrame:
    """
    Aggregate DataFrame by time resolution
    
    Args:
        df: Input DataFrame with datetime index
        resolution: 'd' for daily, 'm' for monthly
    
    Returns:
        Aggregated DataFrame
    """
    if resolution == 'd':
        return df.groupby(df.index.date).sum()
    elif resolution == 'm':
        grouped = df.groupby([df.index.year, df.index.month]).sum()
        grouped.index.set_names(['year', 'month'], inplace=True)
        return grouped
    else:
        raise ValueError(f"Unsupported resolution: {resolution}")


def get_date_range(df: pd.DataFrame) -> pd.DatetimeIndex:
    """
    Get date range from DataFrame index
    
    Args:
        df: DataFrame with datetime index
    
    Returns:
        DatetimeIndex covering the full range
    """
    date_01 = df.index[0]
    date_02 = df.index[-1]
    return pd.date_range(date_01, date_02, freq='D')


def calculate_data_availability(
    df: pd.DataFrame, 
    resolution: str = 'd', 
    data_resolution: int = 5
) -> pd.DataFrame:
    """
    Calculate data availability for each series
    
    Args:
        df: Input DataFrame
        resolution: Aggregation resolution ('d' for daily)
        data_resolution: Original data resolution in minutes
    
    Returns:
        DataFrame with availability percentages
    """
    if resolution == 'd':
        daily_points = (24 * 60) // data_resolution  # Expected points per day
        grouped = df.groupby(df.index.date)
        
        availability = {}
        for col in df.columns:
            daily_counts = grouped[col].count()
            availability[col] = (daily_counts / daily_points * 100).fillna(0)
        
        return pd.DataFrame(availability)
    
    raise ValueError(f"Unsupported resolution: {resolution}")


def list_dates(first: datetime.datetime, last: datetime.datetime) -> List[datetime.datetime]:
    """
    Generate list of dates between two dates
    
    Args:
        first: Start date
        last: End date
    
    Returns:
        List of datetime objects
    """
    return pd.date_range(first, last, freq='D').tolist()


def convert_wh_to_kwh(series: pd.Series) -> pd.Series:
    """
    Convert Wh values to kWh
    
    Args:
        series: Series with Wh values
    
    Returns:
        Series with kWh values
    """
    return series / 1000


def apply_irradiance_conversion(series: pd.Series, factor: float = 12) -> pd.Series:
    """
    Apply standard irradiance conversion factor
    
    Args:
        series: Irradiance series
        factor: Conversion factor (default 12 for Wh conversion)
    
    Returns:
        Converted series
    """
    return series / factor