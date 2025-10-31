"""
Solar Plant Analytics Workflow Orchestrator

This module provides high-level workflows that consolidate the entire analysis pipeline
found across multiple Study files. Instead of writing repetitive analysis scripts,
users can leverage these standardized workflows.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path

from .analytics import (
    PerformanceRatioCalculator,
    StringLevelAnalyzer, 
    ClippingAnalyzer,
    MultiSourceDataLoader,
    DowntimeAnalyzer,
    StatisticalAnalyzer
)
from .transform.aggregators import DataAggregator
from .transform.cleaners import DataCleaner
from .utils.logging import setup_logger
from .utils.config import ConfigManager


@dataclass
class PlantAnalysisConfig:
    """Configuration for plant analysis workflow"""
    project_name: str
    country: str
    analysis_period: Tuple[str, str]  # start_date, end_date
    data_sources: Dict[str, str]  # data_type -> file_path_pattern
    plant_parameters: Dict[str, Any]
    analysis_types: List[str]  # ['pr_analysis', 'string_analysis', 'clipping_analysis', etc.]
    output_directory: str = None
    generate_plots: bool = True
    

@dataclass 
class AnalysisResults:
    """Complete analysis results"""
    pr_analysis: Dict[str, Any] = None
    string_analysis: Dict[str, Any] = None
    clipping_analysis: Dict[str, Any] = None
    downtime_analysis: Dict[str, Any] = None
    statistical_summary: Dict[str, Any] = None
    data_quality_report: Dict[str, Any] = None
    consolidated_datasets: Dict[str, pd.DataFrame] = None
    monthly_summaries: Dict[str, pd.DataFrame] = None


class SolarPlantWorkflowOrchestrator:
    """
    High-level workflow orchestrator that replaces repetitive Study file patterns
    
    This class consolidates the common analysis patterns found across:
    - Study043_Gorontalo_v03.py
    - Study037_FortDePol_PR_v05.py  
    - Study040_Vloeivelden_Performance_Check_v05.py
    - Study047_Noordscheschut_InvPower_AmbTemp_v01.py
    - And many others
    
    Instead of copying and modifying Study files, users can:
    1. Configure their analysis requirements
    2. Run standardized workflows
    3. Get consistent, comprehensive results
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
        
        # Initialize component analyzers
        self.data_loader = MultiSourceDataLoader(config)
        self.data_cleaner = DataCleaner(config)
        self.data_aggregator = DataAggregator(config)
        self.pr_calculator = PerformanceRatioCalculator(config)
        self.string_analyzer = StringLevelAnalyzer(config)
        self.clipping_analyzer = ClippingAnalyzer(config)
        self.downtime_analyzer = DowntimeAnalyzer(config)
        self.statistical_analyzer = StatisticalAnalyzer(config)
    
    def run_comprehensive_plant_analysis(
        self,
        analysis_config: PlantAnalysisConfig
    ) -> AnalysisResults:
        """
        Run comprehensive plant analysis workflow
        
        This replaces the entire workflow pattern found in most Study files:
        1. Load and consolidate multi-source data
        2. Clean and validate data
        3. Perform requested analyses
        4. Generate summaries and reports
        
        Args:
            analysis_config: Configuration for analysis
            
        Returns:
            Complete analysis results
        """
        self.logger.info(f"Starting comprehensive analysis for {analysis_config.project_name}")
        
        results = AnalysisResults()
        
        try:
            # Step 1: Load and consolidate data
            self.logger.info("Step 1: Loading and consolidating data")
            consolidated_data = self._load_and_consolidate_data(analysis_config)
            results.consolidated_datasets = consolidated_data
            
            # Step 2: Clean and validate data
            self.logger.info("Step 2: Cleaning and validating data")
            cleaned_data = self._clean_and_validate_data(consolidated_data)
            
            # Step 3: Generate monthly summaries
            self.logger.info("Step 3: Generating monthly summaries")
            monthly_summaries = self._generate_monthly_summaries(cleaned_data)
            results.monthly_summaries = monthly_summaries
            
            # Step 4: Run requested analyses
            self.logger.info("Step 4: Running requested analyses")
            
            if 'pr_analysis' in analysis_config.analysis_types:
                results.pr_analysis = self._run_pr_analysis(
                    cleaned_data, analysis_config.plant_parameters
                )
            
            if 'string_analysis' in analysis_config.analysis_types:
                results.string_analysis = self._run_string_analysis(
                    cleaned_data, analysis_config.plant_parameters
                )
            
            if 'clipping_analysis' in analysis_config.analysis_types:
                results.clipping_analysis = self._run_clipping_analysis(
                    cleaned_data, analysis_config.plant_parameters
                )
            
            if 'downtime_analysis' in analysis_config.analysis_types:
                results.downtime_analysis = self._run_downtime_analysis(
                    cleaned_data, analysis_config.plant_parameters
                )
            
            # Step 5: Generate statistical summary
            self.logger.info("Step 5: Generating statistical summary")
            results.statistical_summary = self._generate_statistical_summary(
                cleaned_data, monthly_summaries
            )
            
            # Step 6: Generate data quality report
            self.logger.info("Step 6: Generating data quality report") 
            results.data_quality_report = self._generate_data_quality_report(
                consolidated_data, cleaned_data
            )
            
            # Step 7: Generate output files and plots if requested
            if analysis_config.output_directory and analysis_config.generate_plots:
                self._generate_outputs(results, analysis_config)
            
            self.logger.info("Comprehensive analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def run_quick_performance_assessment(
        self,
        data_sources: Dict[str, str],
        plant_parameters: Dict[str, Any],
        analysis_period: Tuple[str, str] = None
    ) -> Dict[str, Any]:
        """
        Quick performance assessment workflow
        
        Provides rapid plant health check similar to simplified Study files
        """
        self.logger.info("Running quick performance assessment")
        
        # Create minimal config
        config = PlantAnalysisConfig(
            project_name="QuickAssessment",
            country="Unknown",
            analysis_period=analysis_period or ("2023-01-01", "2023-12-31"),
            data_sources=data_sources,
            plant_parameters=plant_parameters,
            analysis_types=['pr_analysis', 'statistical_summary'],
            generate_plots=False
        )
        
        # Run streamlined analysis
        results = self.run_comprehensive_plant_analysis(config)
        
        # Extract key metrics
        key_metrics = {
            'overall_pr': None,
            'monthly_energy_yield': None,
            'data_availability': None,
            'plant_health_score': None
        }
        
        if results.pr_analysis:
            key_metrics['overall_pr'] = results.pr_analysis.get('plant_pr', {}).get('statistics', {})
        
        if results.monthly_summaries:
            key_metrics['monthly_energy_yield'] = results.monthly_summaries.get('energy_monthly', {})
        
        if results.data_quality_report:
            key_metrics['data_availability'] = results.data_quality_report.get('availability_stats', {})
        
        if results.statistical_summary:
            key_metrics['plant_health_score'] = results.statistical_summary.get('plant_health_score', 0)
        
        return key_metrics
    
    def run_fault_investigation_workflow(
        self,
        data_sources: Dict[str, str],
        plant_parameters: Dict[str, Any],
        investigation_period: Tuple[str, str],
        focus_equipment: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fault investigation workflow
        
        Focused analysis for troubleshooting specific issues
        Similar to specialized Study files like Isoma downtime analysis
        """
        self.logger.info("Running fault investigation workflow")
        
        config = PlantAnalysisConfig(
            project_name="FaultInvestigation",
            country="Unknown", 
            analysis_period=investigation_period,
            data_sources=data_sources,
            plant_parameters=plant_parameters,
            analysis_types=['string_analysis', 'clipping_analysis', 'downtime_analysis'],
            generate_plots=True
        )
        
        results = self.run_comprehensive_plant_analysis(config)
        
        # Focus on fault-related results
        fault_analysis = {
            'string_faults': results.string_analysis.get('fault_detection', {}),
            'clipping_events': results.clipping_analysis.get('inverter_clipping', {}), 
            'downtime_periods': results.downtime_analysis.get('downtime_periods', []),
            'performance_deviations': self._identify_performance_deviations(results),
            'recommendations': self._generate_fault_recommendations(results)
        }
        
        return fault_analysis
    
    def _load_and_consolidate_data(
        self, 
        config: PlantAnalysisConfig
    ) -> Dict[str, pd.DataFrame]:
        """Load and consolidate data from multiple sources"""
        
        consolidated_data = {}
        
        for data_type, source_pattern in config.data_sources.items():
            try:
                if '*' in source_pattern or '{year}' in source_pattern:
                    # Multi-file/multi-year case
                    year_paths = self._expand_source_pattern(source_pattern, config.analysis_period)
                    
                    consolidation_result = self.data_loader.load_multi_year_data(
                        base_paths=year_paths,
                        data_type=data_type
                    )
                    
                    consolidated_data[data_type] = consolidation_result.consolidated_data
                    
                else:
                    # Single file case
                    data = pd.read_csv(source_pattern, index_col=0, parse_dates=True)
                    consolidated_data[data_type] = data
                    
            except Exception as e:
                self.logger.warning(f"Failed to load {data_type} data: {str(e)}")
                consolidated_data[data_type] = pd.DataFrame()
        
        return consolidated_data
    
    def _clean_and_validate_data(
        self, 
        raw_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Clean and validate loaded data"""
        
        cleaned_data = {}
        
        for data_type, data in raw_data.items():
            if data.empty:
                cleaned_data[data_type] = data
                continue
            
            try:
                # Apply appropriate cleaning based on data type
                if 'irradiance' in data_type.lower() or 'gti' in data_type.lower():
                    cleaned_data[data_type] = self.data_cleaner.clean_irradiance_data(
                        data, 
                        min_value=0,
                        max_value=1500,
                        remove_frozen_sensors=True
                    )
                elif 'temperature' in data_type.lower():
                    cleaned_data[data_type] = self.data_cleaner.clean_temperature_data(
                        data,
                        min_value=-50,
                        max_value=100
                    )
                elif 'current' in data_type.lower():
                    cleaned_data[data_type] = self.data_cleaner.clean_electrical_data(
                        data,
                        min_value=0,
                        max_value=30,
                        remove_outliers=True
                    )
                elif 'power' in data_type.lower():
                    cleaned_data[data_type] = self.data_cleaner.clean_electrical_data(
                        data,
                        min_value=0,
                        max_value=None,  # No upper limit for power
                        remove_outliers=True
                    )
                else:
                    # Generic cleaning
                    cleaned_data[data_type] = self.data_cleaner.clean_sensor_data(data)
                    
            except Exception as e:
                self.logger.warning(f"Failed to clean {data_type} data: {str(e)}")
                cleaned_data[data_type] = data  # Use raw data if cleaning fails
        
        return cleaned_data
    
    def _generate_monthly_summaries(
        self, 
        cleaned_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Generate monthly summaries for all datasets"""
        
        return self.data_aggregator.create_monthly_energy_summary(cleaned_data)
    
    def _run_pr_analysis(
        self, 
        data: Dict[str, pd.DataFrame], 
        plant_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run comprehensive PR analysis"""
        
        pr_results = {}
        
        # Plant-level PR
        if 'meter' in data and 'irradiance' in data:
            plant_pr = self.pr_calculator.calculate_plant_pr(
                meter_data=data['meter'],
                irradiance_data=data['irradiance'],
                dc_capacity=plant_params.get('dc_capacity', 1000),
                module_temp=data.get('temperature'),
                temp_coefficient=plant_params.get('temp_coefficient', -0.004)
            )
            pr_results['plant_pr'] = plant_pr
        
        # Inverter-level PR
        if 'inverter_power' in data and 'irradiance' in data:
            inv_capacity_map = plant_params.get('inverter_capacity_map', pd.Series())
            
            if not inv_capacity_map.empty:
                inverter_pr = self.pr_calculator.calculate_inverter_level_pr(
                    inverter_power=data['inverter_power'],
                    irradiance_data=data['irradiance'],
                    inverter_capacity_map=inv_capacity_map
                )
                pr_results['inverter_pr'] = inverter_pr
        
        # Multi-azimuth PR if applicable
        if plant_params.get('multi_azimuth', False):
            azimuth_irradiance = plant_params.get('azimuth_irradiance', {})
            string_map = plant_params.get('string_map', pd.DataFrame())
            
            if azimuth_irradiance and not string_map.empty:
                multi_az_pr = self.pr_calculator.calculate_multi_azimuth_pr(
                    power_data=data.get('inverter_power', pd.DataFrame()),
                    irradiance_by_azimuth=azimuth_irradiance,
                    capacity_mapping=plant_params.get('capacity_mapping', pd.DataFrame()),
                    string_map=string_map
                )
                pr_results['multi_azimuth_pr'] = multi_az_pr
        
        return pr_results
    
    def _run_string_analysis(
        self, 
        data: Dict[str, pd.DataFrame], 
        plant_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run string-level analysis"""
        
        string_results = {}
        
        if 'string_current' in data:
            # String fault detection
            working_strings_map = plant_params.get('working_strings_map', pd.DataFrame())
            
            if not working_strings_map.empty:
                fault_detection = self.string_analyzer.detect_string_underperformance(
                    string_current=data['string_current'],
                    working_strings_map=working_strings_map,
                    deviation_threshold=plant_params.get('fault_threshold', 0.15)
                )
                string_results['fault_detection'] = fault_detection
            
            # String PR calculation
            if 'string_voltage' in data and 'irradiance' in data:
                string_capacity_map = plant_params.get('string_capacity_map', pd.DataFrame())
                
                if not string_capacity_map.empty:
                    string_pr = self.string_analyzer.calculate_string_pr(
                        string_power=None,  # Will be calculated from current/voltage
                        string_current=data['string_current'],
                        string_voltage=data['string_voltage'],
                        irradiance_data=data['irradiance'],
                        string_capacity_map=string_capacity_map
                    )
                    string_results['string_pr'] = string_pr
        
        return string_results
    
    def _run_clipping_analysis(
        self, 
        data: Dict[str, pd.DataFrame], 
        plant_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run clipping analysis"""
        
        clipping_results = {}
        
        # Inverter clipping
        if 'inverter_power' in data and 'irradiance' in data:
            power_limits = plant_params.get('inverter_power_limits', pd.Series())
            
            if not power_limits.empty:
                inv_clipping = self.clipping_analyzer.detect_inverter_clipping(
                    inverter_power=data['inverter_power'],
                    irradiance_data=data['irradiance'],
                    power_limits=power_limits
                )
                clipping_results['inverter_clipping'] = inv_clipping
        
        # MPPT clipping
        if 'string_current' in data:
            mppt_clipping = self.clipping_analyzer.detect_mppt_clipping(
                string_current=data['string_current'],
                current_limit=plant_params.get('mppt_current_limit', 25.8)
            )
            clipping_results['mppt_clipping'] = mppt_clipping
        
        return clipping_results
    
    def _run_downtime_analysis(
        self, 
        data: Dict[str, pd.DataFrame], 
        plant_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run downtime analysis"""
        
        downtime_results = {}
        
        # Status-based downtime
        if 'status' in data and 'irradiance' in data:
            status_downtime = self.downtime_analyzer.calculate_downtime_from_status(
                status_data=data['status'],
                irradiance_data=data['irradiance'].mean(axis=1) if isinstance(data['irradiance'], pd.DataFrame) else data['irradiance']
            )
            downtime_results.update(status_downtime)
        
        # Alarm-based downtime
        if 'alarms' in data and 'irradiance' in data:
            alarm_downtime = self.downtime_analyzer.calculate_downtime_from_alarms(
                alarm_data=data['alarms'],
                irradiance_data=data['irradiance'].mean(axis=1) if isinstance(data['irradiance'], pd.DataFrame) else data['irradiance'],
                dc_capacity=plant_params.get('dc_capacity')
            )
            downtime_results.update(alarm_downtime)
        
        return downtime_results
    
    def _generate_statistical_summary(
        self, 
        cleaned_data: Dict[str, pd.DataFrame], 
        monthly_summaries: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Generate statistical summary"""
        
        # Calculate data availability
        availability_stats = self.statistical_analyzer.calculate_data_availability(cleaned_data)
        
        # Generate performance summary
        performance_summary = self.statistical_analyzer.generate_performance_summary(monthly_summaries)
        
        return {
            'availability_stats': availability_stats,
            'performance_summary': performance_summary
        }
    
    def _generate_data_quality_report(
        self, 
        raw_data: Dict[str, pd.DataFrame], 
        cleaned_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Generate data quality report"""
        
        quality_report = {}
        
        for data_type in raw_data.keys():
            raw_df = raw_data[data_type]
            clean_df = cleaned_data[data_type]
            
            if raw_df.empty:
                continue
            
            # Calculate quality metrics
            raw_points = raw_df.size
            raw_missing = raw_df.isnull().sum().sum()
            clean_points = clean_df.size if not clean_df.empty else 0
            clean_missing = clean_df.isnull().sum().sum() if not clean_df.empty else raw_points
            
            quality_report[data_type] = {
                'raw_data_points': raw_points,
                'raw_missing_points': raw_missing,
                'raw_availability': ((raw_points - raw_missing) / raw_points) * 100 if raw_points > 0 else 0,
                'clean_data_points': clean_points,
                'clean_missing_points': clean_missing,
                'clean_availability': ((clean_points - clean_missing) / clean_points) * 100 if clean_points > 0 else 0,
                'data_reduction': ((raw_points - clean_points) / raw_points) * 100 if raw_points > 0 else 0
            }
        
        return quality_report
    
    def _expand_source_pattern(
        self, 
        pattern: str, 
        analysis_period: Tuple[str, str]
    ) -> Dict[int, str]:
        """Expand source pattern to year-specific paths"""
        
        start_date = pd.to_datetime(analysis_period[0])
        end_date = pd.to_datetime(analysis_period[1])
        
        years = range(start_date.year, end_date.year + 1)
        year_paths = {}
        
        for year in years:
            year_path = pattern.replace('{year}', str(year))
            year_paths[year] = year_path
        
        return year_paths
    
    def _identify_performance_deviations(self, results: AnalysisResults) -> Dict[str, Any]:
        """Identify performance deviations from analysis results"""
        
        deviations = {}
        
        # PR deviations
        if results.pr_analysis and 'plant_pr' in results.pr_analysis:
            pr_stats = results.pr_analysis['plant_pr'].statistics
            if pr_stats.get('monthly', {}).get('mean_pr', 0) < 0.75:  # Below 75% PR
                deviations['low_pr'] = {
                    'severity': 'high',
                    'value': pr_stats['monthly']['mean_pr'],
                    'threshold': 0.75
                }
        
        # String fault deviations
        if results.string_analysis and 'fault_detection' in results.string_analysis:
            fault_count = results.string_analysis['fault_detection'].sum().sum()
            if fault_count > 0:
                deviations['string_faults'] = {
                    'severity': 'medium',
                    'fault_count': fault_count,
                    'details': results.string_analysis['fault_detection']
                }
        
        return deviations
    
    def _generate_fault_recommendations(self, results: AnalysisResults) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        
        # Check data quality
        if results.data_quality_report:
            low_quality_datasets = [
                dataset for dataset, metrics in results.data_quality_report.items()
                if metrics.get('clean_availability', 100) < 80
            ]
            
            if low_quality_datasets:
                recommendations.append(
                    f"Improve data quality for: {', '.join(low_quality_datasets)}. "
                    f"Current availability below 80%."
                )
        
        # Check performance
        if results.pr_analysis and 'plant_pr' in results.pr_analysis:
            pr_mean = results.pr_analysis['plant_pr'].statistics.get('monthly', {}).get('mean_pr', 0)
            if pr_mean < 0.75:
                recommendations.append(
                    f"Plant PR ({pr_mean:.2%}) is below expected levels. "
                    f"Investigate soiling, shading, or equipment issues."
                )
        
        # Check string faults
        if results.string_analysis and 'fault_detection' in results.string_analysis:
            fault_summary = results.string_analysis['fault_detection']
            if isinstance(fault_summary, pd.DataFrame) and fault_summary.sum().sum() > 0:
                recommendations.append(
                    "String faults detected. Prioritize inspection and maintenance "
                    "of underperforming strings."
                )
        
        # Check clipping
        if results.clipping_analysis and 'inverter_clipping' in results.clipping_analysis:
            clipping_summary = results.clipping_analysis['inverter_clipping']
            high_clipping_invs = [
                inv for inv, data in clipping_summary.items()
                if data.get('clipping_frequency_pct', 0) > 5
            ]
            
            if high_clipping_invs:
                recommendations.append(
                    f"High clipping detected in inverters: {', '.join(high_clipping_invs)}. "
                    f"Consider DC/AC ratio optimization."
                )
        
        if not recommendations:
            recommendations.append("No critical issues identified. Plant performance within normal parameters.")
        
        return recommendations
    
    def _generate_outputs(self, results: AnalysisResults, config: PlantAnalysisConfig):
        """Generate output files and plots"""
        
        output_dir = Path(config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save monthly summaries
        if results.monthly_summaries:
            for summary_name, summary_data in results.monthly_summaries.items():
                if not summary_data.empty:
                    summary_data.to_csv(output_dir / f"{summary_name}.csv")
        
        # Save analysis results
        analysis_summary = {
            'project': config.project_name,
            'analysis_period': config.analysis_period,
            'pr_analysis': results.pr_analysis,
            'statistical_summary': results.statistical_summary,
            'data_quality_report': results.data_quality_report
        }
        
        # This would be expanded to include plotting functionality
        self.logger.info(f"Analysis outputs saved to {output_dir}")
