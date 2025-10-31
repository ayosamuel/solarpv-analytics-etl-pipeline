"""
Machine Learning Models for Solar Plant Analytics

Consolidates all ML workflows found across Performance_Estimation_*.py files
"""

import pandas as pd
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging

from ..utils.logging import setup_logger
from ..utils.config import ConfigManager


@dataclass
class ModelResults:
    """Standardized results structure for ML models"""
    model: Any
    score: float
    mse: float
    rms: float
    intercept: float
    coefficients: np.ndarray
    features: pd.DataFrame
    target: pd.Series
    predictions: pd.Series
    min_irradiance: float
    

class LinearRegressionEngine:
    """
    Consolidates linear regression workflows from:
    - Performance_Estimation_Infinity50_V01-V04.py
    - Performance_Estimation_MMID*.py
    - Study003_Marum_PlantPerformance.py
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def perform_linear_regression(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        min_irradiance: float,
        test_size: float = 0.33,
        random_state: int = 42,
        normalize: bool = False
    ) -> ModelResults:
        """
        Standardized linear regression workflow
        
        Replaces redundant functions:
        - perform_Linear_Regression()
        - perform_Linear_Regression_Power()
        - perform_Linear_Regression_Voltage()
        - perform_Linear_Regression_Current()
        - perform_Linear_Regression_MPM()
        """
        self.logger.info(f"Starting linear regression with {len(features)} features")
        
        X = features.copy()
        y = target.copy()
        
        # Optional scaling
        if normalize:
            scaler = StandardScaler()
            X = pd.DataFrame(
                scaler.fit_transform(X),
                index=X.index,
                columns=X.columns
            )
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Fit model
        model = linear_model.LinearRegression()
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred_test = model.predict(X_test)
        y_pred_full = pd.Series(model.predict(X), index=y.index)
        
        # Metrics
        score = model.score(X_test, y_test)
        mse = mean_squared_error(y_test, y_pred_test)
        rms = np.sqrt(mse)
        
        self.logger.info(f"Model score: {score:.4f}, MSE: {mse:.4f}, RMS: {rms:.4f}")
        
        return ModelResults(
            model=model,
            score=score,
            mse=mse,
            rms=rms,
            intercept=model.intercept_,
            coefficients=model.coef_,
            features=X,
            target=y,
            predictions=y_pred_full,
            min_irradiance=min_irradiance
        )


class FeatureTransformer:
    """
    Consolidates feature transformation workflows
    
    Replaces functions:
    - transform_LR_Data_Power()
    - transform_LR_Data_Voltage()
    - transform_LR_Data_Current()
    - transform_LR_Data_MPM_PR()
    - transform_LR_Data_MPM_LFM()
    - transform_LR_Data_Test()
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def transform_power_features(
        self,
        df: pd.DataFrame,
        power_col: str,
        min_irradiance: float
    ) -> pd.DataFrame:
        """Transform data for power prediction"""
        
        result = df[df['GTI'] >= min_irradiance].copy()
        
        # Standard power model features
        result['X0'] = result['GTI']  # Irradiance
        result['X1'] = np.log10(result['GTI'])  # Log irradiance
        result['X2'] = result['GTI']  # Irradiance (duplicate for compatibility)
        result['X3'] = result['GTI'] * (result['modTemp'] - 25)  # Temperature effect
        result['X4'] = result['GTI'] * result['windSpeed']  # Wind effect
        result['X5'] = result['GTI'] ** 2  # Irradiance squared
        
        return result[['X0', 'X1', 'X2', 'X3', 'X4', 'X5']]
    
    def transform_voltage_features(
        self,
        df: pd.DataFrame,
        voltage_col: str
    ) -> pd.DataFrame:
        """Transform data for voltage prediction"""
        
        result = df.copy()
        
        # Voltage model features
        result['X0'] = result['modTemp'] - 25  # Temperature difference
        result['X1'] = np.log10(result['GTI'])  # Log irradiance
        result['X2'] = result['GTI']  # Irradiance
        
        return result[['X0', 'X1', 'X2']]
    
    def transform_current_features(
        self,
        df: pd.DataFrame,
        current_col: str
    ) -> pd.DataFrame:
        """Transform data for current prediction"""
        
        result = df.copy()
        
        # Current model features
        result['X0'] = result['GTI']  # Irradiance
        result['X1'] = result['GTI'] * (result['modTemp'] - 25)  # Temperature effect
        
        return result[['X0', 'X1']]
    
    def transform_pr_features(
        self,
        df: pd.DataFrame,
        pr_col: str
    ) -> pd.DataFrame:
        """Transform data for Performance Ratio prediction"""
        
        result = df.copy()
        
        # PR model features (MPM - Multi-Parameter Model)
        result['X0'] = result['modTemp'] - 25  # Temperature difference
        result['X1'] = result['windSpeed']  # Wind speed
        result['X2'] = result['GTI']  # Irradiance
        result['X3'] = result['GTI'] * (result['modTemp'] - 25)  # Combined effect
        result['X4'] = result['ambTemp']  # Ambient temperature
        
        return result[['X0', 'X1', 'X2', 'X3', 'X4']]


class SolarPlantPredictor:
    """
    High-level predictor class combining all workflows
    
    Consolidates functionality from:
    - All Performance_Estimation_*.py files
    - Plant performance studies
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
        self.regression_engine = LinearRegressionEngine(config)
        self.transformer = FeatureTransformer(config)
    
    def predict_power(
        self,
        df: pd.DataFrame,
        power_col: str,
        level: str = 'Inverter',  # 'Inverter', 'Combiner Box', 'String'
        min_irradiance: float = 200,
        **kwargs
    ) -> ModelResults:
        """Predict power output"""
        
        self.logger.info(f"Predicting power at {level} level")
        
        # Filter and transform features
        features = self.transformer.transform_power_features(
            df, power_col, min_irradiance
        )
        target = df.loc[features.index, power_col]
        
        # Run regression
        return self.regression_engine.perform_linear_regression(
            features, target, min_irradiance, **kwargs
        )
    
    def predict_voltage(
        self,
        df: pd.DataFrame,
        voltage_col: str,
        level: str = 'Inverter',
        **kwargs
    ) -> ModelResults:
        """Predict voltage"""
        
        self.logger.info(f"Predicting voltage at {level} level")
        
        features = self.transformer.transform_voltage_features(df, voltage_col)
        target = df.loc[features.index, voltage_col]
        
        return self.regression_engine.perform_linear_regression(
            features, target, 0, **kwargs
        )
    
    def predict_current(
        self,
        df: pd.DataFrame,
        current_col: str,
        level: str = 'Inverter',
        **kwargs
    ) -> ModelResults:
        """Predict current"""
        
        self.logger.info(f"Predicting current at {level} level")
        
        features = self.transformer.transform_current_features(df, current_col)
        target = df.loc[features.index, current_col]
        
        return self.regression_engine.perform_linear_regression(
            features, target, 0, **kwargs
        )
    
    def predict_performance_ratio(
        self,
        df: pd.DataFrame,
        pr_col: str,
        min_irradiance: float = 400,
        **kwargs
    ) -> ModelResults:
        """Predict Performance Ratio using Multi-Parameter Model"""
        
        self.logger.info("Predicting Performance Ratio")
        
        # Filter data
        filtered_df = df[df['GTI'] >= min_irradiance].copy()
        
        features = self.transformer.transform_pr_features(filtered_df, pr_col)
        target = filtered_df.loc[features.index, pr_col]
        
        return self.regression_engine.perform_linear_regression(
            features, target, min_irradiance, **kwargs
        )


class PerformanceEstimator:
    """
    Consolidates performance estimation workflows
    
    Replaces functions like:
    - build_DF_Reg()
    - run_MPM_PR()
    - deviations_data()
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
        self.predictor = SolarPlantPredictor(config)
    
    def build_regression_dataframe(
        self,
        df: pd.DataFrame,
        month: int,
        min_gti: float = 400,
        pr_min: float = 0.7,
        pr_max: float = 0.93,
        cutoff_power: float = 670
    ) -> pd.DataFrame:
        """Build filtered dataframe for regression analysis"""
        
        # Filter by month and conditions
        result = df[df.index.month == month].copy()
        result = result[result['GTI'] > min_gti]
        result = result[result['PR'] > pr_min]
        result = result[result['PR'] < pr_max]
        
        if cutoff_power > 0:
            power_cols = [col for col in result.columns if 'power' in col.lower()]
            for col in power_cols:
                if col in result.columns:
                    result = result[result[col] < cutoff_power]
        
        self.logger.info(f"Filtered dataframe: {len(result)} records")
        return result
    
    def calculate_deviations(
        self,
        measured: pd.Series,
        predicted: pd.Series,
        threshold: float = 0.07,
        max_threshold: float = 0.15
    ) -> Dict[str, Any]:
        """Calculate deviation statistics between measured and predicted values"""
        
        # Align series
        common_idx = measured.index.intersection(predicted.index)
        measured_aligned = measured.loc[common_idx]
        predicted_aligned = predicted.loc[common_idx]
        
        # Calculate relative deviations
        deviations = abs(measured_aligned - predicted_aligned) / measured_aligned
        
        # Statistics
        stats = {
            'mean_deviation': deviations.mean(),
            'std_deviation': deviations.std(),
            'max_deviation': deviations.max(),
            'threshold_exceeded': (deviations > threshold).sum(),
            'max_threshold_exceeded': (deviations > max_threshold).sum(),
            'total_samples': len(deviations)
        }
        
        stats['threshold_percentage'] = (
            stats['threshold_exceeded'] / stats['total_samples'] * 100
        )
        stats['max_threshold_percentage'] = (
            stats['max_threshold_exceeded'] / stats['total_samples'] * 100
        )
        
        return stats
