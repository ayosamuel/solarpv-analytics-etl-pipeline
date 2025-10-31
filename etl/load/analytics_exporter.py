"""
Analytics Results Exporter

Specialized exporter for solar plant analytics results from the ETL workflow orchestrator.
Handles the complex nested data structures and provides various export formats.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
from pathlib import Path
import pickle

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger
from .writers import WriterFactory, CSVWriter, ExcelWriter, JSONWriter


class AnalyticsResultsExporter:
    """
    Export analytics results from SolarPlantWorkflowOrchestrator
    
    Handles the AnalysisResults dataclass and all nested analytics components:
    - PR analysis results
    - String analysis results  
    - Clipping analysis results
    - Downtime analysis results
    - Statistical summaries
    - Data quality reports
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def export_complete_analysis(
        self,
        analysis_results,  # AnalysisResults dataclass
        output_directory: str,
        formats: List[str] = ['excel', 'csv'],
        include_raw_data: bool = False,
        compress_output: bool = False
    ) -> Dict[str, List[str]]:
        """
        Export complete analysis results in multiple formats
        
        Args:
            analysis_results: AnalysisResults object from workflow orchestrator
            output_directory: Base directory for all outputs
            formats: Export formats ('excel', 'csv', 'json', 'pickle')
            include_raw_data: Whether to include raw consolidated datasets
            compress_output: Whether to compress output files
            
        Returns:
            Dictionary mapping format -> list of created files
        """
        self.logger.info(f"Exporting complete analysis results to {output_directory}")
        
        # Create output directory structure
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {format_type: [] for format_type in formats}
        
        # Export each analysis component
        for format_type in formats:
            self.logger.info(f"Exporting in {format_type} format")
            
            if format_type == 'excel':
                files = self._export_to_excel(analysis_results, output_path, include_raw_data)
                exported_files['excel'].extend(files)
                
            elif format_type == 'csv':
                files = self._export_to_csv(analysis_results, output_path, include_raw_data)
                exported_files['csv'].extend(files)
                
            elif format_type == 'json':
                files = self._export_to_json(analysis_results, output_path, include_raw_data)
                exported_files['json'].extend(files)
                
            elif format_type == 'pickle':
                files = self._export_to_pickle(analysis_results, output_path)
                exported_files['pickle'].extend(files)
        
        # Create summary report
        summary_file = self._create_summary_report(analysis_results, output_path)
        exported_files.setdefault('summary', []).append(summary_file)
        
        # Compress if requested
        if compress_output:
            compressed_file = self._compress_outputs(output_path)
            exported_files.setdefault('compressed', []).append(compressed_file)
        
        self.logger.info(f"Export completed. Total files created: {sum(len(files) for files in exported_files.values())}")
        return exported_files
    
    def export_pr_analysis(
        self,
        pr_analysis: Dict[str, Any],
        output_path: str,
        format_type: str = 'excel'
    ) -> str:
        """Export PR analysis results specifically"""
        
        self.logger.info(f"Exporting PR analysis to {output_path}")
        
        if not pr_analysis:
            self.logger.warning("No PR analysis data to export")
            return None
        
        # Prepare PR data for export
        pr_data = {}
        
        # Plant-level PR
        if 'plant_pr' in pr_analysis:
            plant_pr = pr_analysis['plant_pr']
            
            if hasattr(plant_pr, 'pr_monthly') and plant_pr.pr_monthly is not None:
                pr_data['Plant_PR_Monthly'] = plant_pr.pr_monthly
            if hasattr(plant_pr, 'pr_daily') and plant_pr.pr_daily is not None:
                pr_data['Plant_PR_Daily'] = plant_pr.pr_daily
            if hasattr(plant_pr, 'reference_energy') and plant_pr.reference_energy is not None:
                pr_data['Reference_Energy'] = plant_pr.reference_energy
            if hasattr(plant_pr, 'actual_energy') and plant_pr.actual_energy is not None:
                pr_data['Actual_Energy'] = plant_pr.actual_energy
            
            # Add statistics
            if hasattr(plant_pr, 'statistics') and plant_pr.statistics:
                stats_df = self._flatten_statistics_to_dataframe(plant_pr.statistics, 'Plant_PR')
                pr_data['Plant_PR_Statistics'] = stats_df
        
        # Inverter-level PR
        if 'inverter_pr' in pr_analysis:
            pr_data['Inverter_PR'] = pr_analysis['inverter_pr']
        
        # Multi-azimuth PR
        if 'multi_azimuth_pr' in pr_analysis:
            pr_data['Multi_Azimuth_PR'] = pr_analysis['multi_azimuth_pr']
        
        # Export using appropriate writer
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(pr_data, output_path)
    
    def export_string_analysis(
        self,
        string_analysis: Dict[str, Any],
        output_path: str,
        format_type: str = 'excel'
    ) -> str:
        """Export string analysis results"""
        
        self.logger.info(f"Exporting string analysis to {output_path}")
        
        if not string_analysis:
            self.logger.warning("No string analysis data to export")
            return None
        
        string_data = {}
        
        # String fault detection
        if 'fault_detection' in string_analysis:
            fault_data = string_analysis['fault_detection']
            if isinstance(fault_data, pd.DataFrame):
                string_data['String_Faults'] = fault_data
                
                # Add fault summary
                fault_summary = fault_data.sum(axis=1).to_frame('Daily_Fault_Count')
                fault_summary['Monthly_Fault_Count'] = fault_summary.groupby([
                    fault_summary.index.year, fault_summary.index.month
                ])['Daily_Fault_Count'].transform('sum')
                string_data['Fault_Summary'] = fault_summary
        
        # String PR
        if 'string_pr' in string_analysis:
            string_data['String_PR'] = string_analysis['string_pr']
        
        # Export
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(string_data, output_path)
    
    def export_statistical_summary(
        self,
        statistical_summary: Dict[str, Any],
        output_path: str,
        format_type: str = 'excel'
    ) -> str:
        """Export statistical summary results"""
        
        self.logger.info(f"Exporting statistical summary to {output_path}")
        
        if not statistical_summary:
            self.logger.warning("No statistical summary data to export")
            return None
        
        stats_data = {}
        
        # Availability statistics
        if 'availability_stats' in statistical_summary:
            avail_stats = statistical_summary['availability_stats']
            
            if hasattr(avail_stats, 'daily_availability'):
                stats_data['Daily_Availability'] = avail_stats.daily_availability
            if hasattr(avail_stats, 'monthly_availability'):
                stats_data['Monthly_Availability'] = avail_stats.monthly_availability
            if hasattr(avail_stats, 'overall_availability'):
                overall_df = pd.DataFrame([avail_stats.overall_availability]).T
                overall_df.columns = ['Availability_Percent']
                stats_data['Overall_Availability'] = overall_df
        
        # Performance summary
        if 'performance_summary' in statistical_summary:
            perf_summary = statistical_summary['performance_summary']
            if isinstance(perf_summary, dict):
                # Convert nested performance summary to DataFrames
                for metric_name, metric_data in perf_summary.items():
                    if isinstance(metric_data, dict):
                        if metric_name != 'plant_health_score':  # Handle separately
                            df = pd.DataFrame([metric_data]).T
                            df.columns = [f'{metric_name}_Value']
                            stats_data[f'Performance_{metric_name}'] = df
                
                # Plant health score
                if 'plant_health_score' in perf_summary:
                    health_df = pd.DataFrame([{'Plant_Health_Score': perf_summary['plant_health_score']}])
                    stats_data['Plant_Health_Score'] = health_df
        
        # Export
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(stats_data, output_path)
    
    def _export_to_excel(
        self,
        analysis_results,
        output_path: Path,
        include_raw_data: bool
    ) -> List[str]:
        """Export to Excel format with multiple sheets"""
        
        excel_files = []
        
        # Main analysis results file
        main_file = output_path / "Complete_Analysis_Results.xlsx"
        main_data = {}
        
        # Add all analysis components
        if analysis_results.pr_analysis:
            pr_data = self._flatten_pr_analysis(analysis_results.pr_analysis)
            main_data.update(pr_data)
        
        if analysis_results.string_analysis:
            string_data = self._flatten_string_analysis(analysis_results.string_analysis)
            main_data.update(string_data)
        
        if analysis_results.clipping_analysis:
            clipping_data = self._flatten_clipping_analysis(analysis_results.clipping_analysis)
            main_data.update(clipping_data)
        
        if analysis_results.downtime_analysis:
            downtime_data = self._flatten_downtime_analysis(analysis_results.downtime_analysis)
            main_data.update(downtime_data)
        
        if analysis_results.statistical_summary:
            stats_data = self._flatten_statistical_summary(analysis_results.statistical_summary)
            main_data.update(stats_data)
        
        if analysis_results.data_quality_report:
            quality_data = self._flatten_data_quality_report(analysis_results.data_quality_report)
            main_data.update(quality_data)
        
        # Monthly summaries
        if analysis_results.monthly_summaries:
            main_data.update(analysis_results.monthly_summaries)
        
        # Export main file
        if main_data:
            writer = ExcelWriter(self.config)
            writer.write(main_data, str(main_file))
            excel_files.append(str(main_file))
        
        # Export raw data if requested
        if include_raw_data and analysis_results.consolidated_datasets:
            raw_data_file = output_path / "Raw_Consolidated_Datasets.xlsx"
            writer = ExcelWriter(self.config)
            writer.write(analysis_results.consolidated_datasets, str(raw_data_file))
            excel_files.append(str(raw_data_file))
        
        return excel_files
    
    def _export_to_csv(
        self,
        analysis_results,
        output_path: Path,
        include_raw_data: bool
    ) -> List[str]:
        """Export to CSV format with separate files"""
        
        csv_files = []
        csv_dir = output_path / "csv_exports"
        csv_dir.mkdir(exist_ok=True)
        
        writer = CSVWriter(self.config)
        
        # Export each analysis component separately
        if analysis_results.pr_analysis:
            pr_data = self._flatten_pr_analysis(analysis_results.pr_analysis)
            files = writer.write(pr_data, str(csv_dir / "pr_analysis"))
            csv_files.extend(files if isinstance(files, list) else [files])
        
        if analysis_results.string_analysis:
            string_data = self._flatten_string_analysis(analysis_results.string_analysis)
            files = writer.write(string_data, str(csv_dir / "string_analysis"))
            csv_files.extend(files if isinstance(files, list) else [files])
        
        if analysis_results.monthly_summaries:
            files = writer.write(analysis_results.monthly_summaries, str(csv_dir / "monthly_summaries"))
            csv_files.extend(files if isinstance(files, list) else [files])
        
        # Raw data
        if include_raw_data and analysis_results.consolidated_datasets:
            files = writer.write(analysis_results.consolidated_datasets, str(csv_dir / "raw_data"))
            csv_files.extend(files if isinstance(files, list) else [files])
        
        return csv_files
    
    def _export_to_json(
        self,
        analysis_results,
        output_path: Path,
        include_raw_data: bool
    ) -> List[str]:
        """Export to JSON format"""
        
        json_files = []
        
        # Create serializable version of results
        serializable_results = self._make_serializable(analysis_results, include_raw_data)
        
        # Export complete results
        main_json_file = output_path / "Complete_Analysis_Results.json"
        writer = JSONWriter(self.config)
        writer.write(serializable_results, str(main_json_file))
        json_files.append(str(main_json_file))
        
        return json_files
    
    def _export_to_pickle(
        self,
        analysis_results,
        output_path: Path
    ) -> List[str]:
        """Export to pickle format (preserves all Python objects)"""
        
        pickle_file = output_path / "Complete_Analysis_Results.pkl"
        
        with open(pickle_file, 'wb') as f:
            pickle.dump(analysis_results, f)
        
        self.logger.info(f"Exported complete analysis results to pickle: {pickle_file}")
        return [str(pickle_file)]
    
    def _flatten_pr_analysis(self, pr_analysis: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Flatten PR analysis results into DataFrames"""
        
        flattened = {}
        
        for analysis_type, analysis_data in pr_analysis.items():
            if hasattr(analysis_data, '__dict__'):  # Handle dataclass objects
                for attr_name, attr_value in analysis_data.__dict__.items():
                    if isinstance(attr_value, pd.DataFrame):
                        flattened[f"{analysis_type}_{attr_name}"] = attr_value
                    elif isinstance(attr_value, dict) and attr_name == 'statistics':
                        stats_df = self._flatten_statistics_to_dataframe(attr_value, analysis_type)
                        flattened[f"{analysis_type}_statistics"] = stats_df
            elif isinstance(analysis_data, pd.DataFrame):
                flattened[analysis_type] = analysis_data
        
        return flattened
    
    def _flatten_string_analysis(self, string_analysis: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Flatten string analysis results"""
        
        flattened = {}
        
        for key, value in string_analysis.items():
            if isinstance(value, pd.DataFrame):
                flattened[f"string_{key}"] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, pd.DataFrame):
                        flattened[f"string_{key}_{sub_key}"] = sub_value
        
        return flattened
    
    def _flatten_clipping_analysis(self, clipping_analysis: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Flatten clipping analysis results"""
        
        flattened = {}
        
        for clipping_type, clipping_data in clipping_analysis.items():
            if isinstance(clipping_data, dict):
                # Convert clipping results to DataFrame
                clipping_df = pd.DataFrame(clipping_data).T
                flattened[f"clipping_{clipping_type}"] = clipping_df
        
        return flattened
    
    def _flatten_downtime_analysis(self, downtime_analysis: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Flatten downtime analysis results"""
        
        flattened = {}
        
        # Downtime periods
        if 'downtime_periods' in downtime_analysis:
            periods = downtime_analysis['downtime_periods']
            if periods:
                downtime_df = pd.DataFrame(periods)
                flattened['downtime_periods'] = downtime_df
        
        # Monthly summary
        if 'monthly_summary' in downtime_analysis:
            monthly = downtime_analysis['monthly_summary']
            if monthly:
                monthly_df = pd.DataFrame(monthly).T
                flattened['downtime_monthly_summary'] = monthly_df
        
        return flattened
    
    def _flatten_statistical_summary(self, statistical_summary: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Flatten statistical summary results"""
        
        flattened = {}
        
        # Handle availability stats
        if 'availability_stats' in statistical_summary:
            avail_stats = statistical_summary['availability_stats']
            
            if hasattr(avail_stats, 'overall_availability'):
                overall_df = pd.DataFrame([avail_stats.overall_availability]).T
                overall_df.columns = ['Availability_Percent']
                flattened['overall_availability'] = overall_df
        
        # Handle performance summary
        if 'performance_summary' in statistical_summary:
            perf_summary = statistical_summary['performance_summary']
            if isinstance(perf_summary, dict):
                for metric, data in perf_summary.items():
                    if isinstance(data, dict) and metric != 'plant_health_score':
                        df = pd.DataFrame([data]).T
                        df.columns = [f'{metric}_value']
                        flattened[f'performance_{metric}'] = df
        
        return flattened
    
    def _flatten_data_quality_report(self, data_quality_report: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Flatten data quality report"""
        
        if not data_quality_report:
            return {}
        
        quality_df = pd.DataFrame(data_quality_report).T
        return {'data_quality_report': quality_df}
    
    def _flatten_statistics_to_dataframe(self, statistics: Dict[str, Any], prefix: str) -> pd.DataFrame:
        """Convert nested statistics dictionary to DataFrame"""
        
        flattened_stats = {}
        
        def _flatten_dict(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(_flatten_dict(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flattened_stats = _flatten_dict(statistics)
        
        # Convert to DataFrame
        stats_df = pd.DataFrame([flattened_stats]).T
        stats_df.columns = [f'{prefix}_Statistics']
        
        return stats_df
    
    def _make_serializable(self, analysis_results, include_raw_data: bool) -> Dict[str, Any]:
        """Convert analysis results to JSON-serializable format"""
        
        def _convert_to_serializable(obj):
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif hasattr(obj, '__dict__'):  # Handle dataclass objects
                return {k: _convert_to_serializable(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: _convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [_convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        serializable = {}
        
        # Convert each component
        if analysis_results.pr_analysis:
            serializable['pr_analysis'] = _convert_to_serializable(analysis_results.pr_analysis)
        
        if analysis_results.string_analysis:
            serializable['string_analysis'] = _convert_to_serializable(analysis_results.string_analysis)
        
        if analysis_results.clipping_analysis:
            serializable['clipping_analysis'] = _convert_to_serializable(analysis_results.clipping_analysis)
        
        if analysis_results.downtime_analysis:
            serializable['downtime_analysis'] = _convert_to_serializable(analysis_results.downtime_analysis)
        
        if analysis_results.statistical_summary:
            serializable['statistical_summary'] = _convert_to_serializable(analysis_results.statistical_summary)
        
        if analysis_results.data_quality_report:
            serializable['data_quality_report'] = _convert_to_serializable(analysis_results.data_quality_report)
        
        if analysis_results.monthly_summaries:
            serializable['monthly_summaries'] = _convert_to_serializable(analysis_results.monthly_summaries)
        
        if include_raw_data and analysis_results.consolidated_datasets:
            serializable['consolidated_datasets'] = _convert_to_serializable(analysis_results.consolidated_datasets)
        
        return serializable
    
    def _create_summary_report(self, analysis_results, output_path: Path) -> str:
        """Create a human-readable summary report"""
        
        summary_file = output_path / "Analysis_Summary_Report.txt"
        
        with open(summary_file, 'w') as f:
            f.write("SOLAR PLANT ANALYSIS SUMMARY REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # PR Analysis Summary
            if analysis_results.pr_analysis:
                f.write("PERFORMANCE RATIO ANALYSIS\n")
                f.write("-" * 30 + "\n")
                
                if 'plant_pr' in analysis_results.pr_analysis:
                    plant_pr = analysis_results.pr_analysis['plant_pr']
                    if hasattr(plant_pr, 'statistics') and plant_pr.statistics:
                        stats = plant_pr.statistics
                        if 'monthly' in stats:
                            f.write(f"Monthly Average PR: {stats['monthly'].get('mean_pr', 'N/A'):.3f}\n")
                            f.write(f"PR Standard Deviation: {stats['monthly'].get('std_pr', 'N/A'):.3f}\n")
                            f.write(f"Minimum PR: {stats['monthly'].get('min_pr', 'N/A'):.3f}\n")
                            f.write(f"Maximum PR: {stats['monthly'].get('max_pr', 'N/A'):.3f}\n")
                
                f.write("\n")
            
            # String Analysis Summary
            if analysis_results.string_analysis:
                f.write("STRING ANALYSIS\n")
                f.write("-" * 15 + "\n")
                
                if 'fault_detection' in analysis_results.string_analysis:
                    fault_data = analysis_results.string_analysis['fault_detection']
                    if isinstance(fault_data, pd.DataFrame):
                        total_faults = fault_data.sum().sum()
                        f.write(f"Total String Fault Events: {total_faults}\n")
                        faulty_strings = (fault_data.sum() > 0).sum()
                        f.write(f"Strings with Faults: {faulty_strings}\n")
                
                f.write("\n")
            
            # Data Quality Summary
            if analysis_results.data_quality_report:
                f.write("DATA QUALITY SUMMARY\n")
                f.write("-" * 20 + "\n")
                
                for dataset, quality in analysis_results.data_quality_report.items():
                    availability = quality.get('clean_availability', 0)
                    f.write(f"{dataset}: {availability:.1f}% availability\n")
                
                f.write("\n")
            
            # Statistical Summary
            if analysis_results.statistical_summary:
                f.write("STATISTICAL SUMMARY\n")
                f.write("-" * 19 + "\n")
                
                if 'performance_summary' in analysis_results.statistical_summary:
                    perf_summary = analysis_results.statistical_summary['performance_summary']
                    if 'plant_health_score' in perf_summary:
                        f.write(f"Plant Health Score: {perf_summary['plant_health_score']:.1f}/100\n")
        
        return str(summary_file)
    
    def _compress_outputs(self, output_path: Path) -> str:
        """Compress all output files into a single archive"""
        
        import zipfile
        
        zip_file = output_path / "Complete_Analysis_Results.zip"
        
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_path.rglob('*'):
                if file_path.is_file() and file_path != zip_file:
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)
        
        self.logger.info(f"Compressed all outputs to: {zip_file}")
        return str(zip_file)
