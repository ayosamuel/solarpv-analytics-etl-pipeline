"""
Integrated Export Manager for Utility-scale Solar Analytics ETL
Coordinates complex multi-format exports with metadata management
"""

from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import os

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger
from .writers import WriterFactory
from .exporters import ReportExporter, DataExporter, ConfigurationExporter
from .analytics_exporter import AnalyticsResultsExporter


class IntegratedExportManager:
    """
    Unified export manager that coordinates all export functionality
    
    This class provides a single entry point for all export operations,
    automatically routing to the appropriate specialized exporter based
    on the data type and user requirements.
    """
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
        
        # Initialize specialized exporters
        self.report_exporter = ReportExporter(config)
        self.data_exporter = DataExporter(config)
        self.analytics_exporter = AnalyticsResultsExporter(config)
        self.config_exporter = ConfigurationExporter(config)
    
    def export_workflow_results(
        self,
        analysis_results,  # AnalysisResults from SolarPlantWorkflowOrchestrator
        output_directory: str,
        export_config: Dict[str, Any] = None
    ) -> Dict[str, List[str]]:
        """
        Export complete workflow analysis results using the best exporters for each data type
        
        Args:
            analysis_results: AnalysisResults object from workflow orchestrator
            output_directory: Base output directory
            export_config: Configuration for export options
            
        Returns:
            Dictionary mapping export type to list of created files
        """
        self.logger.info(f"Starting integrated export of workflow results to {output_directory}")
        
        # Set default export configuration
        if export_config is None:
            export_config = {
                'formats': ['excel', 'csv'],
                'include_raw_data': False,
                'create_reports': True,
                'compress_output': False,
                'export_configuration': True
            }
        
        exported_files = {}
        
        # 1. Export complete analytics results using specialized analytics exporter
        if analysis_results:
            analytics_files = self.analytics_exporter.export_complete_analysis(
                analysis_results=analysis_results,
                output_directory=os.path.join(output_directory, 'analytics'),
                formats=export_config.get('formats', ['excel', 'csv']),
                include_raw_data=export_config.get('include_raw_data', False),
                compress_output=export_config.get('compress_output', False)
            )
            exported_files.update(analytics_files)
            
            # 2. Create standardized reports using report exporter
            if export_config.get('create_reports', True):
                report_files = self._create_standardized_reports(
                    analysis_results, 
                    os.path.join(output_directory, 'reports')
                )
                exported_files.setdefault('reports', []).extend(report_files)
            
            # 3. Export cleaned datasets if available
            if analysis_results.consolidated_datasets:
                cleaned_files = self.data_exporter.export_cleaned_datasets(
                    datasets=analysis_results.consolidated_datasets,
                    output_directory=os.path.join(output_directory, 'cleaned_data'),
                    file_format=export_config.get('formats', ['csv'])[0],
                    add_metadata=True
                )
                exported_files.setdefault('cleaned_data', []).extend(cleaned_files)
        
        # 4. Export configuration and processing log
        if export_config.get('export_configuration', True):
            config_files = self._export_processing_metadata(
                output_directory=os.path.join(output_directory, 'metadata')
            )
            exported_files.setdefault('metadata', []).extend(config_files)
        
        total_files = sum(len(files) for files in exported_files.values())
        self.logger.info(f"Integrated export completed. Total files created: {total_files}")
        
        return exported_files
    
    def export_data_by_type(
        self,
        data: Dict[str, Any],
        output_path: str,
        data_type: str = 'auto'
    ) -> str:
        """
        Export data using the most appropriate exporter based on data type
        
        Args:
            data: Data to export
            output_path: Output file path
            data_type: Type of data ('analytics', 'report', 'cleaned', 'raw', 'auto')
            
        Returns:
            Path to exported file
        """
        self.logger.info(f"Exporting data of type '{data_type}' to {output_path}")
        
        # Auto-detect data type if not specified
        if data_type == 'auto':
            data_type = self._detect_data_type(data)
        
        # Route to appropriate exporter
        if data_type == 'analytics':
            return self.analytics_exporter.export_analysis_results(data, output_path)
        elif data_type == 'report':
            return self.report_exporter.export_performance_report(data, output_path)
        elif data_type in ['cleaned', 'raw']:
            return self.data_exporter.export_analysis_results(data, output_path)
        else:
            # Default to basic writer
            writer = WriterFactory.create_writer(output_path, self.config)
            return writer.write(data, output_path)
    
    def export_monthly_summary(
        self,
        monthly_data: Dict[str, Any],
        output_directory: str,
        formats: List[str] = ['excel', 'csv']
    ) -> List[str]:
        """
        Export monthly summary using both report and analytics exporters
        
        Args:
            monthly_data: Monthly analysis data
            output_directory: Output directory
            formats: Export formats
            
        Returns:
            List of exported file paths
        """
        exported_files = []
        
        for format_type in formats:
            output_path = os.path.join(output_directory, f"monthly_summary.{format_type}")
            
            # Use report exporter for standardized monthly reports
            if hasattr(self.report_exporter, 'export_monthly_summary_report'):
                file_path = self.report_exporter.export_monthly_summary_report(
                    monthly_data, output_path
                )
                exported_files.append(file_path)
        
        return exported_files
    
    def _create_standardized_reports(
        self,
        analysis_results,
        reports_directory: str
    ) -> List[str]:
        """Create standardized reports from analysis results"""
        
        os.makedirs(reports_directory, exist_ok=True)
        report_files = []
        
        # Performance summary report
        if analysis_results.pr_analysis:
            performance_data = {}
            
            # Extract PR data for reporting
            for analysis_type, pr_data in analysis_results.pr_analysis.items():
                if hasattr(pr_data, 'pr_monthly') and pr_data.pr_monthly is not None:
                    performance_data[f'{analysis_type}_monthly'] = pr_data.pr_monthly
                if hasattr(pr_data, 'pr_daily') and pr_data.pr_daily is not None:
                    performance_data[f'{analysis_type}_daily'] = pr_data.pr_daily
            
            if performance_data:
                report_path = os.path.join(reports_directory, "Performance_Report.xlsx")
                file_path = self.report_exporter.export_performance_report(
                    data=performance_data,
                    output_path=report_path,
                    report_type='comprehensive'
                )
                report_files.append(file_path)
        
        # Data quality report
        if analysis_results.data_quality_report:
            quality_path = os.path.join(reports_directory, "Data_Quality_Report.xlsx")
            file_path = self.config_exporter.export_data_quality_summary(
                quality_metrics=analysis_results.data_quality_report,
                output_path=quality_path
            )
            report_files.append(file_path)
        
        return report_files
    
    def _export_processing_metadata(self, output_directory: str) -> List[str]:
        """Export processing metadata and configuration"""
        
        os.makedirs(output_directory, exist_ok=True)
        metadata_files = []
        
        # Export configuration
        config_path = os.path.join(output_directory, "etl_configuration.csv")
        file_path = self.config_exporter.export_configuration(config_path)
        metadata_files.append(file_path)
        
        return metadata_files
    
    def _detect_data_type(self, data: Dict[str, Any]) -> str:
        """Auto-detect the type of data for appropriate export routing"""
        
        # Check for analytics result patterns
        if any(key in data for key in ['pr_analysis', 'string_analysis', 'clipping_analysis']):
            return 'analytics'
        
        # Check for report data patterns
        if any(key in data for key in ['performance_ratio', 'energy_yield', 'availability']):
            return 'report'
        
        # Check for cleaned data patterns
        if any(key.endswith('_cleaned') for key in data.keys()):
            return 'cleaned'
        
        # Default to raw data
        return 'raw'


# Convenience function for easy integration
def export_complete_analysis(
    analysis_results,
    output_directory: str,
    config: ConfigManager = None,
    **export_options
) -> Dict[str, List[str]]:
    """
    Convenience function to export complete analysis results
    
    Args:
        analysis_results: AnalysisResults from SolarPlantWorkflowOrchestrator
        output_directory: Output directory
        config: Configuration manager
        **export_options: Additional export options
        
    Returns:
        Dictionary mapping export type to list of created files
    """
    manager = IntegratedExportManager(config)
    return manager.export_workflow_results(
        analysis_results=analysis_results,
        output_directory=output_directory,
        export_config=export_options
    )
