"""
Example Usage: Replacing Legacy Study Files with ETL Workflows

This example demonstrates how to replace the repetitive Study*.py files 
with standardized ETL workflows.

Instead of copying and modifying Study files, use the workflow orchestrator
to configure and run standardized analyses.
"""

import pandas as pd
from pathlib import Path

# Import the new ETL workflow orchestrator
from etl.workflow_orchestrator import (
    SolarPlantWorkflowOrchestrator,
    PlantAnalysisConfig
)

def main():
    """
    Example: Replace Study043_Gorontalo_v03.py with standardized workflow
    """
    
    # Initialize the workflow orchestrator
    orchestrator = SolarPlantWorkflowOrchestrator()
    
    # Configure the analysis (replaces hardcoded parameters in Study files)
    analysis_config = PlantAnalysisConfig(
        project_name="Gorontalo",
        country="IDN",
        analysis_period=("2020-04-01", "2021-12-31"),
        data_sources={
            'meter': r'C:\...\gorontalo\{year}\meter\*.csv',
            'inverter_power': r'S:\...\IDN\Gorontalo\InvPowerDF_*.csv',
            'irradiance': r'S:\...\IDN\Gorontalo\PyranomDF_*.csv', 
            'string_current': r'S:\...\IDN\Gorontalo\StringCurrentDF_*.csv',
            'string_voltage': r'S:\...\IDN\Gorontalo\CBVoltageDF_*.csv',
            'temperature': r'S:\...\IDN\Gorontalo\MeteoDF_*.csv'
        },
        plant_parameters={
            'dc_capacity': 2500000,  # 2.5 MW
            'string_dc_capacity': 400,  # 400W per string
            'temp_coefficient': -0.004,
            'inverter_power_limits': pd.Series({
                'Inv_01': 500000,
                'Inv_02': 500000,
                # ... etc
            }),
            'multi_azimuth': True,
            'azimuth_irradiance': {
                '15_180': pd.DataFrame(),  # Would be loaded separately
                '15_270': pd.DataFrame()
            }
        },
        analysis_types=[
            'pr_analysis',
            'string_analysis', 
            'clipping_analysis',
            'downtime_analysis'
        ],
        output_directory=r'C:\Reports\Gorontalo\Analysis_Results',
        generate_plots=True
    )
    
    # Run the comprehensive analysis
    results = orchestrator.run_comprehensive_plant_analysis(analysis_config)
    
    # Access results (replaces manual calculations in Study files)
    print("=== GORONTALO ANALYSIS RESULTS ===")
    
    # Plant-level PR (replaces mainPRDF calculations)
    if results.pr_analysis and 'plant_pr' in results.pr_analysis:
        plant_pr = results.pr_analysis['plant_pr']
        print(f"Plant PR Statistics:")
        print(f"  Monthly Average: {plant_pr.statistics['monthly']['mean_pr']:.3f}")
        print(f"  Annual Energy: {results.monthly_summaries['meter_monthly_kwh'].sum().sum()/1000:.0f} MWh")
    
    # String fault analysis (replaces string fault detection code)
    if results.string_analysis and 'fault_detection' in results.string_analysis:
        string_faults = results.string_analysis['fault_detection']
        faulty_strings = string_faults[string_faults.sum(axis=1) > 0]
        print(f"String Faults Detected: {len(faulty_strings)} periods")
    
    # Clipping analysis (replaces manual clipping detection)
    if results.clipping_analysis and 'inverter_clipping' in results.clipping_analysis:
        clipping_results = results.clipping_analysis['inverter_clipping']
        print(f"Inverters with Clipping: {len(clipping_results)}")
    
    # Data quality report (replaces availability calculations)
    if results.data_quality_report:
        for dataset, quality in results.data_quality_report.items():
            print(f"{dataset} Data Availability: {quality['clean_availability']:.1f}%")
    
    print("\nAnalysis complete! Results saved to output directory.")
    
    return results


def example_quick_assessment():
    """
    Example: Quick performance assessment
    
    Replaces simple Study files that just need basic performance metrics
    """
    
    orchestrator = SolarPlantWorkflowOrchestrator()
    
    # Quick assessment with minimal configuration
    key_metrics = orchestrator.run_quick_performance_assessment(
        data_sources={
            'meter': r'S:\...\NL\Scaldia\MeterDF.csv',
            'irradiance': r'S:\...\NL\Scaldia\PyranomDF.csv'
        },
        plant_parameters={
            'dc_capacity': 1500000  # 1.5 MW
        },
        analysis_period=("2023-01-01", "2023-12-31")
    )
    
    print("=== QUICK ASSESSMENT RESULTS ===")
    print(f"Overall PR: {key_metrics['overall_pr']['mean_pr']:.3f}")
    print(f"Data Availability: {key_metrics['data_availability']['overall_availability']['meter']:.1f}%")
    print(f"Plant Health Score: {key_metrics['plant_health_score']:.1f}/100")
    
    return key_metrics


def example_fault_investigation():
    """
    Example: Fault investigation workflow
    
    Replaces specialized fault investigation Study files like Isoma downtime analysis
    """
    
    orchestrator = SolarPlantWorkflowOrchestrator()
    
    # Focused fault investigation
    fault_analysis = orchestrator.run_fault_investigation_workflow(
        data_sources={
            'status': r'C:\...\isoma\CB_Status\*.csv',
            'irradiance': r'C:\...\isoma\Pyranometer\*.csv',
            'alarms': r'C:\...\isoma\Inverter_Alarms\alarms.csv',
            'string_current': r'C:\...\isoma\String_Current\*.csv'
        },
        plant_parameters={
            'dc_capacity': 2549830,  # From study
            'fault_threshold': 0.15
        },
        investigation_period=("2022-01-01", "2022-08-31"),
        focus_equipment=['Inv_01', 'Inv_02']  # Focus on specific equipment
    )
    
    print("=== FAULT INVESTIGATION RESULTS ===")
    
    # Downtime analysis
    if 'downtime_periods' in fault_analysis:
        total_downtime = sum(period['duration_hours'] for period in fault_analysis['downtime_periods'])
        total_lost_energy = sum(period['lost_energy_kwh'] or 0 for period in fault_analysis['downtime_periods'])
        print(f"Total Downtime: {total_downtime:.1f} hours")
        print(f"Total Lost Energy: {total_lost_energy:.0f} kWh")
    
    # String faults
    if 'string_faults' in fault_analysis:
        print(f"String Faults Detected: {len(fault_analysis['string_faults'])}")
    
    # Recommendations
    if 'recommendations' in fault_analysis:
        print("Recommendations:")
        for rec in fault_analysis['recommendations']:
            print(f"  - {rec}")
    
    return fault_analysis


def migration_guide():
    """
    Migration guide for converting existing Study files to use ETL workflows
    """
    
    print("""
    MIGRATION GUIDE: Converting Study Files to ETL Workflows
    ========================================================
    
    1. IDENTIFY ANALYSIS PATTERNS:
       - Data loading and consolidation
       - PR calculations  
       - String analysis
       - Statistical summaries
       
    2. REPLACE HARDCODED PARAMETERS:
       OLD: country = 'NL'; project = 'Scaldia'
       NEW: PlantAnalysisConfig(project_name='Scaldia', country='NL', ...)
       
    3. REPLACE REPETITIVE DATA LOADING:
       OLD: Multiple gf_old.webPortal_to_DB() calls
       NEW: data_sources = {'meter': 'path/*.csv', ...}
       
    4. REPLACE MANUAL CALCULATIONS:
       OLD: mainPRDF = pd.concat([meter, gti_average], axis=1)
            mainPRDF['Actual PR'] = mainPRDF['E_Meter'] / mainPRDF['E_Ref']
       NEW: results.pr_analysis['plant_pr']
       
    5. REPLACE CUSTOM AGGREGATIONS:
       OLD: monthly_data = data.groupby([data.index.year, data.index.month]).sum()
       NEW: results.monthly_summaries
       
    6. USE STANDARDIZED OUTPUTS:
       OLD: Custom plotting and file saving
       NEW: Automatic output generation with generate_plots=True
    
    BENEFITS:
    - Eliminates 100+ redundant Study*.py files
    - Consistent analysis methodology
    - Automatic data validation and cleaning
    - Standardized output formats
    - Easy configuration for new projects
    - Built-in error handling and logging
    """)


if __name__ == "__main__":
    # Run examples
    print("Running Gorontalo comprehensive analysis...")
    gorontalo_results = main()
    
    print("\n" + "="*50 + "\n")
    
    print("Running quick assessment...")
    quick_results = example_quick_assessment()
    
    print("\n" + "="*50 + "\n")
    
    print("Running fault investigation...")
    fault_results = example_fault_investigation()
    
    print("\n" + "="*50 + "\n")
    
    # Show migration guide
    migration_guide()
