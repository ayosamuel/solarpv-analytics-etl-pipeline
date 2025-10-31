"""
High-level data exporters for reports and analysis outputs

This module focuses on business logic for creating standardized reports 
and exports. It uses the writers module for actual file output operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import os

from ..utils.config import ConfigManager
from ..utils.logging import setup_logger
from .writers import WriterFactory, ExcelWriter


class ReportExporter:
    """Export solar plant performance reports with standardized structure"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def export_performance_report(
        self,
        data: Dict[str, pd.DataFrame],
        output_path: str,
        report_type: str = 'monthly',
        include_charts: bool = False
    ) -> str:
        """
        Export comprehensive performance report
        
        Args:
            data: Dictionary containing performance data
            output_path: Output file path
            report_type: Type of report ('daily', 'monthly', 'annual')
            include_charts: Whether to include charts (requires additional libraries)
        
        Returns:
            Path to exported report
        """
        self.logger.info(f"Exporting {report_type} performance report to {output_path}")
        
        # Prepare report data with business logic
        report_data = self._prepare_report_data(data, report_type)
        
        # Add summary statistics
        report_data['Summary'] = self._calculate_summary_statistics(data)
        
        # Add metadata
        report_data['Metadata'] = self._create_metadata(report_type)
        
        # Use writer for actual export
        writer = WriterFactory.create_writer(output_path, self.config)
        
        if isinstance(writer, ExcelWriter):
            # For Excel, use multiple sheets with proper naming
            sheet_names = list(report_data.keys())
            return writer.write(report_data, output_path, sheet_names=sheet_names)
        else:
            # For other formats, create a combined report
            combined_data = self._combine_report_data(report_data)
            return writer.write(combined_data, output_path)
    
    def export_monthly_summary_report(
        self,
        monthly_data: Dict[str, pd.DataFrame],
        output_path: str
    ) -> str:
        """Export standardized monthly summary report"""
        
        self.logger.info(f"Exporting monthly summary report to {output_path}")
        
        # Structure data for monthly reporting
        report_data = {}
        
        for month, data in monthly_data.items():
            # Add month identifier to data
            data_with_month = data.copy()
            data_with_month['Month'] = month
            report_data[f"Month_{month}"] = data_with_month
        
        # Add cross-month summary
        if monthly_data:
            report_data['Annual_Summary'] = self._create_annual_summary(monthly_data)
        
        # Export using appropriate writer
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(report_data, output_path)
    
    def _prepare_report_data(
        self, 
        data: Dict[str, pd.DataFrame], 
        report_type: str
    ) -> Dict[str, pd.DataFrame]:
        """Prepare data for report export with standardized naming"""
        
        report_data = {}
        
        # Map data to standardized report sections
        section_mapping = {
            'performance_ratio': 'Performance_Ratio',
            'energy_yield': 'Energy_Yield', 
            'availability': 'Availability',
            'irradiance': 'Irradiance_Data',
            'temperature': 'Temperature_Data',
            'faults': 'Fault_Analysis',
            'string_analysis': 'String_Analysis',
            'inverter_analysis': 'Inverter_Analysis'
        }
        
        for key, df in data.items():
            if key in section_mapping and not df.empty:
                report_data[section_mapping[key]] = df
            elif not df.empty:
                # Use original key if no mapping found
                report_data[key] = df
        
        return report_data
    
    def _calculate_summary_statistics(
        self, 
        data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Calculate summary statistics for the report"""
        
        summary_stats = {}
        
        for metric_name, df in data.items():
            if df.empty:
                continue
                
            # Calculate statistics for each numeric column
            for col in df.select_dtypes(include=[np.number]).columns:
                series = df[col].dropna()
                if len(series) > 0:
                    summary_stats[f"{metric_name}_{col}"] = {
                        'Mean': series.mean(),
                        'Median': series.median(),
                        'Std': series.std(),
                        'Min': series.min(),
                        'Max': series.max(),
                        'Count': len(series),
                        'Data_Quality_%': (len(series) / len(df)) * 100
                    }
        
        return pd.DataFrame(summary_stats).T
    
    def _create_metadata(self, report_type: str) -> pd.DataFrame:
        """Create metadata for the report"""
        
        metadata = {
            'Report_Type': [report_type],
            'Generated_Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'ETL_Version': ['2.0.0'],
            'Data_Source': ['Utility-scale Solar Plant Monitoring System'],
            'Processing_Software': ['Utility-scale Solar Analytics ETL Pipeline']
        }
        
        return pd.DataFrame(metadata)
    
    def _combine_report_data(
        self, 
        report_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Combine report data into single DataFrame for non-Excel formats"""
        
        combined_dfs = []
        
        for sheet_name, df in report_data.items():
            if not df.empty:
                # Add section identifier
                df_copy = df.copy()
                df_copy['Report_Section'] = sheet_name
                df_copy['Export_Timestamp'] = datetime.now().isoformat()
                combined_dfs.append(df_copy)
        
        if combined_dfs:
            return pd.concat(combined_dfs, ignore_index=True, sort=False)
        else:
            return pd.DataFrame({'Message': ['No data available for export']})
    
    def _create_annual_summary(
        self, 
        monthly_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Create annual summary from monthly data"""
        
        annual_summary = {}
        
        for month, data in monthly_data.items():
            # Extract key metrics for annual rollup
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                if col not in annual_summary:
                    annual_summary[col] = []
                annual_summary[col].append(data[col].mean())
        
        # Calculate annual statistics
        annual_stats = {}
        for metric, values in annual_summary.items():
            annual_stats[metric] = {
                'Annual_Mean': np.mean(values),
                'Annual_Min': np.min(values),
                'Annual_Max': np.max(values),
                'Annual_Std': np.std(values),
                'Months_Available': len(values)
            }
        
        return pd.DataFrame(annual_stats).T


class DataExporter:
    """Export processed data with business logic for standardization"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def export_cleaned_datasets(
        self,
        datasets: Dict[str, pd.DataFrame],
        output_directory: str,
        file_format: str = 'csv',
        add_metadata: bool = True
    ) -> List[str]:
        """
        Export cleaned datasets with standardized naming and metadata
        
        Args:
            datasets: Dictionary of cleaned DataFrames
            output_directory: Output directory
            file_format: Output format ('csv', 'excel', 'json')
            add_metadata: Whether to add processing metadata to files
        
        Returns:
            List of exported file paths
        """
        self.logger.info(f"Exporting {len(datasets)} cleaned datasets to {output_directory}")
        
        os.makedirs(output_directory, exist_ok=True)
        exported_files = []
        
        for dataset_name, df in datasets.items():
            if df.empty:
                self.logger.warning(f"Skipping empty dataset: {dataset_name}")
                continue
            
            # Add metadata if requested
            if add_metadata:
                df = self._add_processing_metadata(df, dataset_name)
            
            # Create standardized filename
            filename = f"{dataset_name}_cleaned.{file_format}"
            file_path = os.path.join(output_directory, filename)
            
            # Use appropriate writer
            writer = WriterFactory.create_writer(file_path, self.config)
            exported_path = writer.write(df, file_path)
            exported_files.append(exported_path)
            
            self.logger.info(f"Exported {dataset_name}: {len(df)} rows to {exported_path}")
        
        return exported_files
    
    def export_analysis_results(
        self,
        results: Dict[str, Any],
        output_path: str,
        flatten_nested: bool = True
    ) -> str:
        """
        Export analysis results with intelligent data type handling
        
        Args:
            results: Dictionary containing analysis results
            output_path: Output file path
            flatten_nested: Whether to flatten nested dictionaries
        
        Returns:
            Path to exported file
        """
        self.logger.info(f"Exporting analysis results to {output_path}")
        
        # Convert results to exportable format
        export_data = self._prepare_analysis_results(results, flatten_nested)
        
        # Use appropriate writer
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(export_data, output_path)
    
    def _add_processing_metadata(
        self, 
        df: pd.DataFrame, 
        dataset_name: str
    ) -> pd.DataFrame:
        """Add processing metadata to DataFrame"""
        
        df_with_metadata = df.copy()
        
        # Add metadata as DataFrame attributes (preserved in some formats)
        df_with_metadata.attrs = {
            'dataset_name': dataset_name,
            'export_timestamp': datetime.now().isoformat(),
            'etl_version': '1.0.0',
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict()
        }
        
        return df_with_metadata
    
    def _prepare_analysis_results(
        self, 
        results: Dict[str, Any], 
        flatten_nested: bool
    ) -> Dict[str, pd.DataFrame]:
        """Convert analysis results to DataFrame format for export"""
        
        export_data = {}
        
        for analysis_name, result in results.items():
            try:
                if isinstance(result, pd.DataFrame):
                    export_data[analysis_name] = result
                elif isinstance(result, pd.Series):
                    export_data[analysis_name] = result.to_frame()
                elif isinstance(result, dict):
                    if flatten_nested:
                        # Flatten nested dictionaries
                        flattened = self._flatten_dict(result)
                        df = pd.DataFrame([flattened])
                    else:
                        df = pd.DataFrame([result])
                    export_data[analysis_name] = df
                elif isinstance(result, (list, tuple)):
                    # Convert list/tuple to DataFrame
                    df = pd.DataFrame({'values': result})
                    export_data[analysis_name] = df
                else:
                    # Convert single values to DataFrame
                    df = pd.DataFrame({'value': [result]})
                    export_data[analysis_name] = df
                    
            except Exception as e:
                self.logger.warning(f"Could not convert {analysis_name} to DataFrame: {e}")
                # Create a simple info DataFrame
                export_data[f"{analysis_name}_info"] = pd.DataFrame({
                    'type': [type(result).__name__],
                    'value': [str(result)[:100]]  # Truncate long values
                })
        
        return export_data
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class ConfigurationExporter:
    """Export ETL configuration and processing metadata"""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def export_processing_log(
        self,
        operations: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Export processing log with all operations performed
        
        Args:
            operations: List of operation metadata
            output_path: Output file path
        
        Returns:
            Path to exported log file
        """
        self.logger.info(f"Exporting processing log to {output_path}")
        
        log_data = pd.DataFrame(operations)
        log_data['export_timestamp'] = datetime.now().isoformat()
        
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(log_data, output_path)
    
    def export_configuration(
        self,
        output_path: str
    ) -> str:
        """
        Export current configuration settings
        
        Args:
            output_path: Output file path
        
        Returns:
            Path to exported configuration file
        """
        self.logger.info(f"Exporting configuration to {output_path}")
        
        config_data = pd.DataFrame([{
            'setting': key,
            'value': str(value),
            'type': type(value).__name__
        } for key, value in self.config._config.items()])
        
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(config_data, output_path)
    
    def export_data_quality_summary(
        self,
        quality_metrics: Dict[str, Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Export data quality summary report
        
        Args:
            quality_metrics: Dictionary of quality metrics by dataset
            output_path: Output file path
        
        Returns:
            Path to exported quality report
        """
        self.logger.info(f"Exporting data quality summary to {output_path}")
        
        # Convert quality metrics to DataFrame
        quality_rows = []
        for dataset_name, metrics in quality_metrics.items():
            row = {'Dataset': dataset_name}
            row.update(metrics)
            quality_rows.append(row)
        
        quality_df = pd.DataFrame(quality_rows)
        
        writer = WriterFactory.create_writer(output_path, self.config)
        return writer.write(quality_df, output_path)


# Legacy compatibility aliases
ChartExporter = ConfigurationExporter  # Placeholder for future chart functionality