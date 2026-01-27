# Solar PV Analytics ETL Pipeline

A production-ready ETL pipeline for solar photovoltaic system analytics with integrated fault detection, supervised machine learning for energy loss prediction, and automated report generation.

## Overview

This project provides a comprehensive platform for analyzing solar PV plant performance through automated data processing, advanced analytics, and intelligent fault detection. The system transforms raw sensor data into actionable insights through configurable workflows, enabling drill-down performance evaluation and root cause assessment at scale.

## Key Features

### 🔍 Advanced Fault Detection
- **Rule-based fault detection engine**: Identifies equipment failures, sensor anomalies, and performance degradation
- **Multi-stage validation**: Catches data quality issues before they propagate through the analysis pipeline
- **Anomaly detection algorithms**: Automatic identification of unusual patterns in solar energy production

### 🤖 Machine Learning for Energy Loss Prediction
- **Supervised learning models**: Predict energy losses using scikit-learn algorithms
- **Feature engineering**: Temperature corrections, irradiance normalization, and seasonal adjustments
- **Performance forecasting**: Identify underperforming equipment before failures occur

### 📊 Statistical Analysis & Performance Evaluation
- **Performance Ratio (PR) calculations**: IEC 61724 standard compliant with temperature corrections and uncertainty analysis
- **Statistical confidence intervals**: Rigorous uncertainty quantification for all metrics
- **Time series analytics**: Handle gaps, seasonality, and long-term trends in solar sensor data
- **Capacity analysis**: Detailed drill-down evaluation of individual system components

### 📋 Root Cause Assessment
- **Systematic diagnostic workflows**: Trace performance issues to specific equipment or environmental factors
- **Correlation analysis**: Identify relationships between environmental conditions and energy output
- **Component-level diagnostics**: Isolate issues in inverters, panels, or monitoring systems

### 🎯 Automated Report Generation
- **Interactive HTML dashboards**: Professional visualizations with embedded analytics
- **Multi-format exports**: Excel workbooks, CSV files, and JSON for API integration
- **One-command automation**: From raw data to complete analysis reports in minutes
- **Customizable templates**: Configure report structure and content through simple parameters

### ⚙️ Production-Ready Architecture
- **ETL Pipeline Design**: Clean separation with Extract → Transform → Load stages
- **Configuration-driven workflows**: No code changes needed for new plant analysis
- **Type-safe implementation**: 100% type hints throughout for maintainability
- **Memory-efficient processing**: Handle 50GB+ datasets through streaming and chunked operations
- **Extensible export system**: Factory pattern supporting CSV, Excel, JSON, and database formats

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from source

```bash
git clone https://github.com/ayosamuel/solarpv-analytics-etl-pipeline.git
cd solarpv-analytics-etl-pipeline
pip install -e .
```

### Install dependencies

```bash
pip install -r requirements.txt
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Running the Complete Demo Pipeline

```bash
python test_complete_pipeline.py
```

This generates a complete analysis including:
- 📊 2.1GB of realistic solar plant data
- 📈 4 professional visualizations (PR trends, fault detection, statistical summaries)
- 📋 Interactive HTML dashboard with embedded analytics
- 💾 24 export files (2 Excel workbooks, 16 CSV files, JSON exports)
- ⚡ All generated in under 2 minutes

### Configuration-Based Analysis

```python
from etl.orchestration import PlantAnalysisConfig, AnalysisOrchestrator

# Configure analysis for any solar plant
config = PlantAnalysisConfig(
    project_name="SolarPlant_001",
    analysis_types=['pr_analysis', 'fault_detection', 'ml_prediction', 'visualization'],
    data_sources={
        'meter': 'data/energy/*.csv',
        'weather': 'data/irradiance/*.csv',
        'temperature': 'data/temperature/*.csv'
    },
    plant_parameters={
        'capacity_kw': 5000,
        'location': 'Site_A'
    }
)

# Run complete analysis pipeline
orchestrator = AnalysisOrchestrator()
results = orchestrator.run_analysis(config)
```

## Core Capabilities

### Fault Detection Rules

The system implements comprehensive fault detection covering:
- **Sensor validation**: Missing data, out-of-range values, stuck sensors
- **Performance thresholds**: Equipment operating below expected efficiency
- **Pattern recognition**: Unusual energy production patterns indicating equipment issues
- **Cross-validation**: Verify sensor readings against expected physical relationships

### Supervised Learning Models

Machine learning capabilities include:
- **Energy loss prediction**: Forecast potential energy losses based on historical patterns
- **Performance degradation modeling**: Track and predict long-term efficiency decline
- **Weather impact analysis**: Quantify effects of environmental conditions on output
- **Maintenance optimization**: Predict optimal timing for preventive maintenance

### Statistical Analysis

Rigorous statistical methods throughout:
- **Uncertainty quantification**: Confidence intervals for all calculated metrics
- **Trend analysis**: Long-term performance trends with seasonal decomposition
- **Comparative analytics**: Benchmark plants against expected performance
- **Distribution analysis**: Characterize typical vs. anomalous operating conditions

## Project Structure

```
solarpv-analytics-etl-pipeline/
├── etl/                          # Core ETL pipeline modules
│   ├── extraction/               # Data extraction from various sources
│   ├── transformation/           # Data cleaning, validation, and processing
│   ├── loading/                  # Export to multiple formats (Excel, CSV, JSON)
│   ├── orchestration/            # Workflow coordination and configuration
│   └── visualization/            # Chart generation and dashboard creation
├── test_complete_pipeline.py     # Complete system demonstration
├── demo_integrated_exports.py    # Export functionality examples
├── setup.py                      # Package configuration
└── README.md                     # This file
```

## Technical Highlights

### Performance Ratio Calculation with IEC Standards

```python
def calculate_performance_ratio(energy: pd.DataFrame, 
                               irradiance: pd.DataFrame, 
                               temperature: pd.DataFrame) -> PRResults:
    """IEC 61724 standard PR calculation with temperature correction"""
    
    # Temperature correction (IEC standard coefficient)
    temp_corrected_power = energy * (1 + 0.004 * (25 - temperature))
    
    # Reference energy calculation
    reference_energy = (irradiance / 1000) * plant_capacity
    
    # PR with statistical confidence intervals
    pr = temp_corrected_power / reference_energy
    return PRResults(
        pr_daily=pr.resample('D').mean(),
        confidence_intervals=calculate_uncertainty(pr)
    )
```

### Memory-Efficient Data Processing

```python
def process_large_timeseries(file_path: str) -> pd.DataFrame:
    """Stream processing for multi-GB sensor data files"""
    results = []
    
    # Process in chunks to avoid memory overflow
    for chunk in pd.read_csv(file_path, chunksize=50000):
        cleaned = data_cleaner.clean_chunk(chunk)
        analyzed = analytics.calculate_metrics(cleaned)
        results.append(analyzed)
    
    return pd.concat(results, ignore_index=True)
```

## Use Cases

### Performance Monitoring
- Continuous monitoring of PV system performance metrics
- Automated alerts when performance falls below thresholds
- Historical trend analysis for long-term performance tracking

### Root Cause Analysis
- Drill down from plant-level to component-level diagnostics
- Correlation analysis between environmental factors and performance
- Systematic investigation of performance anomalies

### Predictive Maintenance
- Machine learning models predict equipment failures before they occur
- Optimize maintenance scheduling based on predicted degradation
- Reduce downtime through proactive intervention

### Automated Reporting
- Generate comprehensive analysis reports on-demand
- Export data in multiple formats for integration with other systems
- Create interactive dashboards for stakeholder presentations

## Technologies

**Core Stack:**
- **Python 3.8+**: Modern features including dataclasses, type hints, and context managers
- **Pandas/NumPy**: Optimized data processing and vectorized operations
- **Scikit-learn**: Machine learning algorithms for predictive analytics
- **Matplotlib/Seaborn/Plotly**: Professional visualizations and interactive dashboards

**Architecture Patterns:**
- **ETL Pipeline Design**: Modular extract-transform-load architecture
- **Factory Pattern**: Extensible export system without code modification
- **Configuration Management**: Environment-agnostic, no hardcoded values
- **Type Safety**: Comprehensive type hints for maintainability

## Performance Metrics

| Capability | Performance |
|------------|-------------|
| **Analysis Speed** | Process full year of plant data in 15 minutes |
| **Dataset Size** | Handle 50GB+ datasets on standard hardware |
| **Memory Efficiency** | Streaming processing avoids memory overflow |
| **Report Generation** | From raw data to dashboard in under 2 minutes |
| **Automation** | 100% automated workflow from data to reports |

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

**Ayokunle Samuel Adenigba**  
📧 70694811+ayosamuel@users.noreply.github.com  
🔗 [LinkedIn](https://www.linkedin.com/in/samuel-adenigba-18ab4997/)  
💼 [GitHub Repository](https://github.com/ayosamuel/solarpv-analytics-etl-pipeline)

## Acknowledgments

This project demonstrates production-ready data engineering for solar energy analytics, with emphasis on fault detection, machine learning for energy loss prediction, statistical rigor, and automated reporting capabilities.
