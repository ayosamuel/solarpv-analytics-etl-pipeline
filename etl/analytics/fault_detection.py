"""
Fault Detection Module for Solar Plant Analytics

Consolidates fault detection patterns from various Study files
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import logging

from ..utils.logging import setup_logger
from ..utils.config import ConfigManager


class FaultDetector:
    """
    Consolidated fault detection for solar plant components
    
    Consolidates patterns from:
    - Study033_Bienvenida_Inverter_Status_*.py
    - Study034_Goor_InvStudy_*.py  
    - Study007_Westfield_StringData.py
    - Various performance analysis files
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def detect_inverter_faults(
        self,
        power_data: pd.DataFrame,
        voltage_data: pd.DataFrame = None,
        current_data: pd.DataFrame = None,
        expected_power: pd.Series = None,
        thresholds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Detect inverter faults using multiple indicators
        
        Args:
            power_data: Inverter power output data
            voltage_data: DC voltage data (optional)
            current_data: DC current data (optional)
            expected_power: Expected power based on irradiance
            thresholds: Detection thresholds
        """
        
        if thresholds is None:
            thresholds = {
                'low_power_ratio': 0.8,  # Power < 80% of expected
                'high_power_ratio': 1.2,  # Power > 120% of expected
                'voltage_low': 400,       # DC voltage too low
                'voltage_high': 1000,     # DC voltage too high
                'current_deviation': 0.15  # Current deviation > 15%
            }
        
        self.logger.info("Starting inverter fault detection")
        
        faults = {}
        
        # Power-based fault detection
        if expected_power is not None:
            power_ratio = power_data.div(expected_power, axis=0)
            
            # Low power faults
            low_power_mask = power_ratio < thresholds['low_power_ratio']
            faults['low_power'] = self._extract_fault_periods(low_power_mask)
            
            # High power faults (overload)
            high_power_mask = power_ratio > thresholds['high_power_ratio']
            faults['high_power'] = self._extract_fault_periods(high_power_mask)
        
        # Voltage-based fault detection
        if voltage_data is not None:
            low_voltage_mask = voltage_data < thresholds['voltage_low']
            high_voltage_mask = voltage_data > thresholds['voltage_high']
            
            faults['low_voltage'] = self._extract_fault_periods(low_voltage_mask)
            faults['high_voltage'] = self._extract_fault_periods(high_voltage_mask)
        
        # Current-based fault detection
        if current_data is not None:
            # Detect string imbalances
            current_mean = current_data.mean(axis=1)
            current_std = current_data.std(axis=1)
            current_cv = current_std / current_mean  # Coefficient of variation
            
            imbalance_mask = current_cv > thresholds['current_deviation']
            faults['current_imbalance'] = self._extract_fault_periods(imbalance_mask)
        
        # Zero output detection
        zero_power_mask = power_data == 0
        faults['zero_output'] = self._extract_fault_periods(zero_power_mask)
        
        # Combine all faults
        faults['summary'] = self._summarize_faults(faults)
        
        self.logger.info(f"Fault detection completed. Found {len(faults['summary'])} fault types")
        return faults
    
    def detect_string_faults(
        self,
        string_current: pd.DataFrame,
        string_voltage: pd.DataFrame = None,
        irradiance: pd.Series = None,
        thresholds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Detect string-level faults
        
        Common patterns from Study007_Westfield_StringData.py
        """
        
        if thresholds is None:
            thresholds = {
                'current_deviation': 0.2,    # 20% deviation from median
                'voltage_deviation': 0.1,    # 10% voltage deviation
                'min_irradiance': 100        # Minimum irradiance for analysis
            }
        
        self.logger.info("Starting string fault detection")
        
        faults = {}
        
        # Filter by irradiance if available
        if irradiance is not None:
            mask = irradiance >= thresholds['min_irradiance']
            current_filtered = string_current[mask]
            voltage_filtered = string_voltage[mask] if string_voltage is not None else None
        else:
            current_filtered = string_current
            voltage_filtered = string_voltage
        
        # Current-based string fault detection
        current_median = current_filtered.median(axis=1)
        
        string_faults = {}
        for string in current_filtered.columns:
            string_current_series = current_filtered[string]
            
            # Calculate deviation from median
            deviation = abs(string_current_series - current_median) / current_median
            fault_mask = deviation > thresholds['current_deviation']
            
            if fault_mask.any():
                string_faults[string] = {
                    'fault_periods': self._extract_fault_periods(fault_mask),
                    'max_deviation': deviation.max(),
                    'fault_percentage': (fault_mask.sum() / len(fault_mask)) * 100
                }
        
        faults['string_current_faults'] = string_faults
        
        # Voltage-based string fault detection
        if voltage_filtered is not None:
            voltage_median = voltage_filtered.median(axis=1)
            
            voltage_faults = {}
            for string in voltage_filtered.columns:
                string_voltage_series = voltage_filtered[string]
                
                deviation = abs(string_voltage_series - voltage_median) / voltage_median
                fault_mask = deviation > thresholds['voltage_deviation']
                
                if fault_mask.any():
                    voltage_faults[string] = {
                        'fault_periods': self._extract_fault_periods(fault_mask),
                        'max_deviation': deviation.max(),
                        'fault_percentage': (fault_mask.sum() / len(fault_mask)) * 100
                    }
            
            faults['string_voltage_faults'] = voltage_faults
        
        # Clustering-based anomaly detection
        faults['anomaly_clusters'] = self._detect_anomalies_clustering(current_filtered)
        
        self.logger.info(f"String fault detection completed")
        return faults
    
    def detect_tracker_faults(
        self,
        tracker_angle: pd.DataFrame,
        expected_angle: pd.Series = None,
        power_data: pd.DataFrame = None,
        thresholds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Detect tracker faults
        
        Patterns from tracker analysis in performance studies
        """
        
        if thresholds is None:
            thresholds = {
                'angle_deviation': 5.0,      # degrees
                'stuck_duration': 30,        # minutes
                'power_loss_threshold': 0.1  # 10% power loss
            }
        
        self.logger.info("Starting tracker fault detection")
        
        faults = {}
        
        # Stuck tracker detection (angle not changing)
        stuck_trackers = {}
        for tracker in tracker_angle.columns:
            angle_diff = tracker_angle[tracker].diff().abs()
            stuck_mask = angle_diff < 0.1  # Minimal movement
            
            # Group consecutive stuck periods
            stuck_periods = self._group_consecutive_periods(
                stuck_mask, 
                min_duration_minutes=thresholds['stuck_duration']
            )
            
            if stuck_periods:
                stuck_trackers[tracker] = stuck_periods
        
        faults['stuck_trackers'] = stuck_trackers
        
        # Angle deviation detection
        if expected_angle is not None:
            angle_faults = {}
            for tracker in tracker_angle.columns:
                deviation = abs(tracker_angle[tracker] - expected_angle)
                fault_mask = deviation > thresholds['angle_deviation']
                
                if fault_mask.any():
                    angle_faults[tracker] = self._extract_fault_periods(fault_mask)
            
            faults['angle_deviations'] = angle_faults
        
        # Power-based tracker fault detection
        if power_data is not None:
            # Compare power between trackers
            power_median = power_data.median(axis=1)
            
            power_faults = {}
            for tracker in power_data.columns:
                power_ratio = power_data[tracker] / power_median
                fault_mask = power_ratio < (1 - thresholds['power_loss_threshold'])
                
                if fault_mask.any():
                    power_faults[tracker] = self._extract_fault_periods(fault_mask)
            
            faults['power_based_faults'] = power_faults
        
        self.logger.info("Tracker fault detection completed")
        return faults
    
    def _extract_fault_periods(
        self, 
        fault_mask: Union[pd.Series, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """Extract continuous fault periods from boolean mask"""
        
        if isinstance(fault_mask, pd.DataFrame):
            # Handle multiple columns
            all_periods = {}
            for col in fault_mask.columns:
                all_periods[col] = self._extract_fault_periods(fault_mask[col])
            return all_periods
        
        # Single series
        periods = []
        in_fault = False
        start_time = None
        
        for timestamp, is_fault in fault_mask.items():
            if is_fault and not in_fault:
                # Start of fault period
                start_time = timestamp
                in_fault = True
            elif not is_fault and in_fault:
                # End of fault period
                periods.append({
                    'start': start_time,
                    'end': timestamp,
                    'duration': timestamp - start_time
                })
                in_fault = False
        
        # Handle case where fault period extends to end of data
        if in_fault and start_time is not None:
            periods.append({
                'start': start_time,
                'end': fault_mask.index[-1],
                'duration': fault_mask.index[-1] - start_time
            })
        
        return periods
    
    def _group_consecutive_periods(
        self,
        mask: pd.Series,
        min_duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Group consecutive True values with minimum duration"""
        
        periods = self._extract_fault_periods(mask)
        
        # Filter by minimum duration
        min_duration = pd.Timedelta(minutes=min_duration_minutes)
        filtered_periods = [
            period for period in periods 
            if period['duration'] >= min_duration
        ]
        
        return filtered_periods
    
    def _detect_anomalies_clustering(
        self,
        data: pd.DataFrame,
        eps: float = 0.5,
        min_samples: int = 5
    ) -> Dict[str, Any]:
        """Use DBSCAN clustering to detect anomalous behavior"""
        
        # Prepare data for clustering
        data_clean = data.dropna()
        if len(data_clean) < min_samples * 2:
            return {'error': 'Insufficient data for clustering'}
        
        # Standardize features
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data_clean.T)  # Transpose for string comparison
        
        # Apply DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = clustering.fit_predict(data_scaled)
        
        # Identify anomalies (label = -1)
        anomaly_strings = [
            data_clean.columns[i] for i, label in enumerate(cluster_labels) 
            if label == -1
        ]
        
        # Group normal strings by cluster
        normal_clusters = {}
        for i, label in enumerate(cluster_labels):
            if label != -1:
                if label not in normal_clusters:
                    normal_clusters[label] = []
                normal_clusters[label].append(data_clean.columns[i])
        
        return {
            'anomaly_strings': anomaly_strings,
            'normal_clusters': normal_clusters,
            'n_clusters': len(normal_clusters),
            'n_anomalies': len(anomaly_strings)
        }
    
    def _summarize_faults(self, faults: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary statistics for all detected faults"""
        
        summary = {
            'total_fault_types': 0,
            'total_fault_instances': 0,
            'fault_type_counts': {}
        }
        
        for fault_type, fault_data in faults.items():
            if fault_type == 'summary':
                continue
                
            if isinstance(fault_data, dict):
                if 'fault_periods' in fault_data:
                    # Single component fault
                    count = len(fault_data['fault_periods'])
                    summary['fault_type_counts'][fault_type] = count
                    summary['total_fault_instances'] += count
                else:
                    # Multiple component faults
                    total_count = 0
                    for component, component_faults in fault_data.items():
                        if isinstance(component_faults, list):
                            total_count += len(component_faults)
                        elif isinstance(component_faults, dict) and 'fault_periods' in component_faults:
                            total_count += len(component_faults['fault_periods'])
                    
                    summary['fault_type_counts'][fault_type] = total_count
                    summary['total_fault_instances'] += total_count
            elif isinstance(fault_data, list):
                # Direct list of fault periods
                count = len(fault_data)
                summary['fault_type_counts'][fault_type] = count
                summary['total_fault_instances'] += count
        
        summary['total_fault_types'] = len(summary['fault_type_counts'])
        
        return summary
