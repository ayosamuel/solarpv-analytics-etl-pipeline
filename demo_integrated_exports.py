"""
Demo: Integrated Analytics Export System

This script demonstrates how the refactored load submodule works together
to export analytics results from the ETL workflow orchestrator.

Usage example for the new unified export system.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any

# Import the integrated export system
from etl.load import IntegratedExportManager, export_complete_analysis
from etl.load.writers import WriterFactory, CSVWriter, ExcelWriter, JSONWriter, PickleWriter
from etl.load.exporters import ReportExporter, DataExporter, ConfigurationExporter
from etl.load.analytics_exporter import AnalyticsResultsExporter
from etl.utils.config import ConfigManager


# Mock AnalysisResults structure (matching workflow_orchestrator.py)
@dataclass
class MockAnalysisResults:
    """Mock analysis results for demonstration"""
    pr_analysis: Dict[str, Any] = field(default_factory=dict)
    string_analysis: Dict[str, Any] = field(default_factory=dict)
    clipping_analysis: Dict[str, Any] = field(default_factory=dict)
    downtime_analysis: Dict[str, Any] = field(default_factory=dict)
    statistical_summary: Dict[str, Any] = field(default_factory=dict)
    data_quality_report: Dict[str, Any] = field(default_factory=dict)
    consolidated_datasets: Dict[str, pd.DataFrame] = field(default_factory=dict)
    monthly_summaries: Dict[str, pd.DataFrame] = field(default_factory=dict)


def create_mock_analysis_results():
    """Create mock analysis results for demonstration"""
    
    # Create sample date range
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    
    # Mock PR analysis
    pr_analysis = {
        'plant_pr': type('PRResults', (), {
            'pr_monthly': pd.DataFrame({
                'Month': pd.date_range('2023-01-01', '2023-12-01', freq='M'),
                'PR': [0.85, 0.87, 0.84, 0.86, 0.88, 0.85, 0.83, 0.86, 0.87, 0.84, 0.85, 0.86]
            }),
            'pr_daily': pd.DataFrame({
                'Date': dates[:30],  # First 30 days
                'PR': [0.85 + 0.05 * pd.np.random.randn() for _ in range(30)]
            }),
            'statistics': {
                'monthly': {
                    'mean_pr': 0.856,
                    'std_pr': 0.015,
                    'min_pr': 0.83,
                    'max_pr': 0.88
                }
            }
        })()
    }
    
    # Mock string analysis
    string_analysis = {
        'fault_detection': pd.DataFrame({
            'Date': dates[:10],
            'String_01': [0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
            'String_02': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'String_03': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        })
    }
    
    # Mock statistical summary
    statistical_summary = {
        'availability_stats': type('AvailStats', (), {
            'overall_availability': {'Plant': 98.5, 'Inverters': 99.2, 'Strings': 97.8}
        })(),
        'performance_summary': {
            'energy_yield': {'total_kwh': 1250000, 'average_daily_kwh': 3425},
            'plant_health_score': 92.5
        }
    }
    
    # Mock data quality report
    data_quality_report = {
        'irradiance_data': {'clean_availability': 95.2, 'missing_data_%': 4.8},
        'temperature_data': {'clean_availability': 98.1, 'missing_data_%': 1.9},
        'power_data': {'clean_availability': 99.3, 'missing_data_%': 0.7}
    }
    
    # Mock consolidated datasets
    consolidated_datasets = {
        'irradiance': pd.DataFrame({
            'Timestamp': dates[:100],
            'GHI': 800 + 200 * pd.np.random.randn(100),
            'DHI': 100 + 50 * pd.np.random.randn(100),
            'DNI': 700 + 150 * pd.np.random.randn(100)
        }),
        'power': pd.DataFrame({
            'Timestamp': dates[:100],
            'AC_Power': 1000 + 200 * pd.np.random.randn(100),
            'DC_Power': 1050 + 210 * pd.np.random.randn(100)
        })
    }
    
    # Mock monthly summaries
    monthly_summaries = {
        'January': pd.DataFrame({
            'Metric': ['Energy_Yield', 'PR', 'Availability'],
            'Value': [105000, 0.85, 98.5],
            'Target': [110000, 0.87, 99.0]
        }),
        'February': pd.DataFrame({
            'Metric': ['Energy_Yield', 'PR', 'Availability'],
            'Value': [98000, 0.87, 99.1],
            'Target': [100000, 0.87, 99.0]
        })
    }
    
    return MockAnalysisResults(
        pr_analysis=pr_analysis,
        string_analysis=string_analysis,
        statistical_summary=statistical_summary,
        data_quality_report=data_quality_report,
        consolidated_datasets=consolidated_datasets,
        monthly_summaries=monthly_summaries
    )


def demo_individual_exporters():
    """Demonstrate individual exporter functionality"""
    
    print("=== Demo: Individual Exporters ===")
    
    config = ConfigManager()
    
    # Demo 1: Basic Writers
    print("\n1. Testing Basic Writers...")
    
    sample_data = pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=5),
        'Value': [100, 110, 105, 115, 120]
    })
    
    # CSV Writer
    csv_writer = CSVWriter(config)
    csv_file = csv_writer.write(sample_data, "demo_output/sample_data.csv")
    print(f"   ✓ CSV exported: {csv_file}")
    
    # Excel Writer
    excel_writer = ExcelWriter(config)
    excel_file = excel_writer.write(sample_data, "demo_output/sample_data.xlsx")
    print(f"   ✓ Excel exported: {excel_file}")
    
    # JSON Writer
    json_writer = JSONWriter(config)
    json_file = json_writer.write(sample_data, "demo_output/sample_data.json")
    print(f"   ✓ JSON exported: {json_file}")
    
    # Pickle Writer
    pickle_writer = PickleWriter(config)
    pickle_file = pickle_writer.write(sample_data, "demo_output/sample_data.pkl")
    print(f"   ✓ Pickle exported: {pickle_file}")
    
    # Demo 2: Writer Factory
    print("\n2. Testing Writer Factory...")
    
    for ext in ['.csv', '.xlsx', '.json', '.pkl']:
        writer = WriterFactory.create_writer(f"demo_output/test{ext}", config)
        print(f"   ✓ {ext}: {type(writer).__name__}")
    
    # Demo 3: Report Exporter
    print("\n3. Testing Report Exporter...")
    
    report_exporter = ReportExporter(config)
    performance_data = {
        'performance_ratio': sample_data,
        'energy_yield': sample_data.rename(columns={'Value': 'Energy_kWh'})
    }
    
    report_file = report_exporter.export_performance_report(
        data=performance_data,
        output_path="demo_output/performance_report.xlsx",
        report_type="demo"
    )
    print(f"   ✓ Performance report: {report_file}")


def demo_analytics_exporter():
    """Demonstrate analytics results exporter"""
    
    print("\n=== Demo: Analytics Results Exporter ===")
    
    config = ConfigManager()
    analytics_exporter = AnalyticsResultsExporter(config)
    
    # Create mock analysis results
    analysis_results = create_mock_analysis_results()
    
    # Export complete analysis
    exported_files = analytics_exporter.export_complete_analysis(
        analysis_results=analysis_results,
        output_directory="demo_output/analytics_export",
        formats=['excel', 'csv', 'json'],
        include_raw_data=True,
        compress_output=True
    )
    
    print("\nAnalytics Export Results:")
    for format_type, files in exported_files.items():
        print(f"   {format_type}: {len(files)} files")
        for file_path in files[:2]:  # Show first 2 files
            print(f"     - {file_path}")
        if len(files) > 2:
            print(f"     ... and {len(files) - 2} more")


def demo_integrated_export_manager():
    """Demonstrate the integrated export manager"""
    
    print("\n=== Demo: Integrated Export Manager ===")
    
    config = ConfigManager()
    manager = IntegratedExportManager(config)
    
    # Create mock analysis results
    analysis_results = create_mock_analysis_results()
    
    # Export using integrated manager
    exported_files = manager.export_workflow_results(
        analysis_results=analysis_results,
        output_directory="demo_output/integrated_export",
        export_config={
            'formats': ['excel', 'csv'],
            'include_raw_data': True,
            'create_reports': True,
            'compress_output': False,
            'export_configuration': True
        }
    )
    
    print("\nIntegrated Export Results:")
    total_files = 0
    for export_type, files in exported_files.items():
        print(f"   {export_type}: {len(files)} files")
        total_files += len(files)
        for file_path in files[:2]:  # Show first 2 files
            print(f"     - {os.path.basename(file_path)}")
        if len(files) > 2:
            print(f"     ... and {len(files) - 2} more")
    
    print(f"\nTotal files exported: {total_files}")


def demo_convenience_function():
    """Demonstrate the convenience export function"""
    
    print("\n=== Demo: Convenience Export Function ===")
    
    # Create mock analysis results
    analysis_results = create_mock_analysis_results()
    
    # Use convenience function
    exported_files = export_complete_analysis(
        analysis_results=analysis_results,
        output_directory="demo_output/convenience_export",
        formats=['excel'],
        include_raw_data=False,
        create_reports=True
    )
    
    print("Convenience Export Results:")
    for export_type, files in exported_files.items():
        print(f"   {export_type}: {len(files)} files")


if __name__ == "__main__":
    print("Solar Analytics ETL ML Workflows - Load Submodule Demo")
    print("=" * 50)
    
    # Create output directory
    os.makedirs("demo_output", exist_ok=True)
    
    try:
        # Run all demos
        demo_individual_exporters()
        demo_analytics_exporter()
        demo_integrated_export_manager()
        demo_convenience_function()
        
        print("\n" + "=" * 50)
        print("✓ All demos completed successfully!")
        print("\nKey Benefits of the Refactored Load Submodule:")
        print("1. No redundant code between writers, exporters, and analytics_exporter")
        print("2. Clear separation of concerns:")
        print("   - writers: Low-level file operations")
        print("   - exporters: Business logic for reports")
        print("   - analytics_exporter: Specialized for complex analytics")
        print("   - export_manager: Unified interface")
        print("3. All analytics results from workflow orchestrator can be exported")
        print("4. Multiple formats supported (CSV, Excel, JSON, Pickle)")
        print("5. Integrated export manager coordinates all functionality")
        print("6. Convenient single-function export for complete workflows")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
