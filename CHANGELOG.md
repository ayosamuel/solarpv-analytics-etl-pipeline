# Utility-scale Solar Analytics ETL Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Development Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)]()

A production-grade ETL pipeline for solar plant performance analytics with integrated machine learning and interactive visualization capabilities.

## ✨ Key Features

- **Complete ETL Pipeline**: Extract, transform, and load solar plant data with configurable workflows
- **Advanced Analytics**: Performance ratio analysis, fault detection, and statistical modeling
- **Interactive Visualizations**: Generate professional charts and dashboards automatically
- **Multiple Export Formats**: Excel, JSON, CSV with customizable templates
- **ML Integration**: Scikit-learn powered fault detection and performance modeling
- **Production Ready**: Comprehensive error handling, logging, and data validation

## 🚀 Quick Demo

```bash
# Clone and setup
git clone https://github.com/ayosamuel/solarpv-analytics-etl-pipeline.git
cd solarpv-analytics-etl-pipeline
python -m venv solar_env
source solar_env/bin/activate  # On Windows: solar_env\Scripts\activate
pip install -e .

# Run the demo (generates sample data and full pipeline)
python test_complete_pipeline.py
```

This creates a complete solar plant analysis with:
- 24 different output files (Excel, JSON, PNG charts)
- Performance ratio calculations
- Fault detection reports  
- Interactive dashboards
- Statistical summaries

## 📊 What Gets Generated

The pipeline automatically creates:

### Analytics Outputs
- **Performance Reports**: Monthly/daily PR analysis with benchmarking
- **Fault Detection**: Equipment issue identification with severity ranking
- **Data Quality**: Availability statistics and gap analysis

### Visualizations
- **Time Series Charts**: PR trends, irradiance correlations, temperature effects
- **Fault Timelines**: Visual fault detection with severity color coding
- **Statistical Dashboards**: Distribution plots, correlation matrices

### Export Formats
- Excel workbooks with multiple tabs
- JSON data for API integration
- Interactive HTML dashboards
- Static PNG charts for reports

## 💻 Usage

### Basic Pipeline

```python
from etl.workflow_orchestrator import SolarPlantWorkflowOrchestrator
from etl.utils.config import PlantAnalysisConfig

# Configure your analysis
config = PlantAnalysisConfig(
    project_name="My_Solar_Plant",
    data_sources={'meter': 'data/*.csv'},
    plant_parameters={'dc_capacity': 5000000},
    analysis_types=['pr_analysis', 'fault_detection']
)

# Run analysis
orchestrator = SolarPlantWorkflowOrchestrator()
results = orchestrator.run_comprehensive_plant_analysis(config)
```

### Add Visualizations

```python
from etl.visualization import QuickVisualizer

visualizer = QuickVisualizer(interactive=True)
plots = visualizer.quick_overview(results.analytics_data)
saved_files = visualizer.show_all_plots(plots)
```

## 🏗️ Architecture

```
etl/
├── extract/        # Data readers (CSV, Excel, API)
├── transform/      # Cleaners, processors, aggregators  
├── load/           # Writers and export managers
├── analytics/      # PR analysis, fault detection, ML models
├── visualization/  # Plotters, dashboards, interactive charts
└── utils/          # Config, logging, validation
```

## 📈 Business Impact

Perfect for:
- **Solar Asset Management**: Automated performance monitoring
- **O&M Optimization**: Early fault detection reduces downtime
- **Regulatory Reporting**: Standardized performance metrics
- **Investment Analysis**: ROI tracking and benchmarking

## 🛠️ Technical Stack

- **Core**: Python 3.8+, Pandas, NumPy
- **Visualization**: Matplotlib, Plotly, Seaborn  
- **ML**: Scikit-learn for fault detection
- **Export**: OpenPyXL for Excel, JSON for APIs
- **Architecture**: Factory patterns, configurable workflows

## 📦 Installation

```bash
pip install solarpv-analytics-etl-pipeline
```

Or for development:
```bash
git clone https://github.com/ayosamuel/solarpv-analytics-etl-pipeline.git
cd solarpv-analytics-etl-pipeline  
pip install -e .[dev]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [Getting Started Guide](GETTING_STARTED.md)
- **Architecture**: [Technical Details](ARCHITECTURE.md)
- **Portfolio**: [Project Showcase](PORTFOLIO.md)

---

**Ready to transform your solar data into actionable insights?** Try the quick demo above!