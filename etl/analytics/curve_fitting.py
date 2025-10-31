"""
Curve Fitting and Optimization Module

Consolidates curve fitting workflows from Study008, Study006_Scaldia, etc.
"""

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import logging

from ..utils.logging import setup_logger
from ..utils.config import ConfigManager


class CurveFitter:
    """
    Standardized curve fitting for solar analytics
    
    Consolidates curve fitting patterns found across study files
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def fit_power_curve(
        self,
        irradiance: pd.Series,
        power: pd.Series,
        curve_type: str = 'linear'
    ) -> Dict[str, Any]:
        """
        Fit power vs irradiance curves
        
        Args:
            irradiance: GTI or GHI data
            power: Power output data
            curve_type: 'linear', 'quadratic', 'exponential'
        """
        
        # Clean data
        mask = (irradiance > 0) & (power > 0) & (~np.isnan(irradiance)) & (~np.isnan(power))
        x = irradiance[mask].values
        y = power[mask].values
        
        if len(x) < 10:
            raise ValueError("Insufficient data points for curve fitting")
        
        # Define curve functions
        def linear_func(x, a, b):
            return a * x + b
        
        def quadratic_func(x, a, b, c):
            return a * x**2 + b * x + c
        
        def exponential_func(x, a, b, c):
            return a * np.exp(b * x) + c
        
        # Select function and initial parameters
        if curve_type == 'linear':
            func = linear_func
            p0 = [1, 0]
        elif curve_type == 'quadratic':
            func = quadratic_func
            p0 = [0.001, 1, 0]
        elif curve_type == 'exponential':
            func = exponential_func
            p0 = [1, 0.001, 0]
        else:
            raise ValueError(f"Unknown curve type: {curve_type}")
        
        try:
            # Fit curve
            popt, pcov = curve_fit(func, x, y, p0=p0, maxfev=5000)
            
            # Calculate fitted values
            y_fitted = func(x, *popt)
            
            # Calculate R-squared
            ss_res = np.sum((y - y_fitted) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            # Calculate RMSE
            rmse = np.sqrt(np.mean((y - y_fitted) ** 2))
            
            results = {
                'parameters': popt,
                'covariance': pcov,
                'r_squared': r_squared,
                'rmse': rmse,
                'fitted_values': pd.Series(y_fitted, index=irradiance[mask].index),
                'function': func,
                'curve_type': curve_type,
                'data_points': len(x)
            }
            
            self.logger.info(f"Curve fitting completed: R² = {r_squared:.4f}, RMSE = {rmse:.4f}")
            return results
            
        except Exception as e:
            self.logger.error(f"Curve fitting failed: {e}")
            raise
    
    def fit_temperature_curve(
        self,
        temperature: pd.Series,
        efficiency: pd.Series,
        reference_temp: float = 25.0
    ) -> Dict[str, Any]:
        """
        Fit temperature coefficient curves for solar modules
        
        Common pattern: efficiency = eff_ref * (1 + gamma * (T - T_ref))
        """
        
        # Clean data
        mask = (~np.isnan(temperature)) & (~np.isnan(efficiency)) & (efficiency > 0)
        temp = temperature[mask].values
        eff = efficiency[mask].values
        
        # Temperature difference from reference
        temp_diff = temp - reference_temp
        
        def temp_coeff_func(temp_diff, eff_ref, gamma):
            return eff_ref * (1 + gamma * temp_diff)
        
        try:
            # Initial guess
            p0 = [eff.mean(), -0.004]  # Typical gamma for silicon
            
            popt, pcov = curve_fit(temp_coeff_func, temp_diff, eff, p0=p0)
            
            # Calculate fitted values
            eff_fitted = temp_coeff_func(temp_diff, *popt)
            
            # Statistics
            r_squared = 1 - np.sum((eff - eff_fitted)**2) / np.sum((eff - np.mean(eff))**2)
            rmse = np.sqrt(np.mean((eff - eff_fitted)**2))
            
            results = {
                'reference_efficiency': popt[0],
                'temperature_coefficient': popt[1],  # %/°C
                'covariance': pcov,
                'r_squared': r_squared,
                'rmse': rmse,
                'fitted_values': pd.Series(eff_fitted, index=temperature[mask].index),
                'reference_temperature': reference_temp
            }
            
            self.logger.info(
                f"Temperature curve fit: η_ref = {popt[0]:.4f}, "
                f"γ = {popt[1]:.6f} %/°C, R² = {r_squared:.4f}"
            )
            return results
            
        except Exception as e:
            self.logger.error(f"Temperature curve fitting failed: {e}")
            raise
    
    def fit_soiling_curve(
        self,
        time: pd.Series,
        soiling_ratio: pd.Series,
        curve_type: str = 'exponential_decay'
    ) -> Dict[str, Any]:
        """
        Fit soiling accumulation curves
        
        Used in Study032_Scaldia_Soiling_v01.py patterns
        """
        
        # Convert time to days since start
        time_days = (time - time.min()).dt.total_seconds() / 86400
        
        # Clean data
        mask = (~np.isnan(soiling_ratio)) & (soiling_ratio > 0) & (soiling_ratio <= 1)
        x = time_days[mask].values
        y = soiling_ratio[mask].values
        
        if curve_type == 'exponential_decay':
            def soiling_func(t, s0, k, s_min):
                return s_min + (s0 - s_min) * np.exp(-k * t)
            p0 = [1.0, 0.01, 0.85]
        
        elif curve_type == 'linear_decay':
            def soiling_func(t, s0, k):
                return s0 - k * t
            p0 = [1.0, 0.001]
        
        try:
            popt, pcov = curve_fit(soiling_func, x, y, p0=p0, maxfev=5000)
            
            y_fitted = soiling_func(x, *popt)
            r_squared = 1 - np.sum((y - y_fitted)**2) / np.sum((y - np.mean(y))**2)
            rmse = np.sqrt(np.mean((y - y_fitted)**2))
            
            results = {
                'parameters': popt,
                'covariance': pcov,
                'r_squared': r_squared,
                'rmse': rmse,
                'fitted_values': pd.Series(y_fitted, index=time[mask]),
                'curve_type': curve_type,
                'time_range_days': x.max() - x.min()
            }
            
            if curve_type == 'exponential_decay':
                results['initial_soiling'] = popt[0]
                results['decay_rate'] = popt[1]
                results['minimum_soiling'] = popt[2]
            elif curve_type == 'linear_decay':
                results['initial_soiling'] = popt[0]
                results['decay_rate_per_day'] = popt[1]
            
            self.logger.info(f"Soiling curve fit completed: R² = {r_squared:.4f}")
            return results
            
        except Exception as e:
            self.logger.error(f"Soiling curve fitting failed: {e}")
            raise
