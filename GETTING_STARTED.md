# 🚀 Getting Started with Solar Analytics ETL ML Workflows

**Welcome!** This guide will get you running solar plant analytics in under 10 minutes. No more copy-paste scripts - just configure and run!

## ⚡ **Super Quick Start**

```bash
# 1. Clone and setup
git clone https://github.com/ayosamuel/solarpv-analytics-etl-pipeline.git
cd solarpv-analytics-etl-pipeline

# 2. Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install everything  
pip install -e ".[dev]"

# 4. Run the complete demo (generates sample data + analysis)
python test_complete_pipeline.py
```

**That's it!** In 2 minutes you'll have:
- ✅ 2.1GB of realistic solar plant data
- ✅ 4 professional visualizations  
- ✅ Interactive HTML dashboard
- ✅ 24 export files (Excel, CSV, JSON)

## 🎯 **What You Just Built**

The demo creates a complete analysis of a simulated 5MW solar plant:
- **Performance analysis** (daily/monthly performance ratios)
- **Fault detection** (equipment problems requiring maintenance)  
- **Statistical analysis** (data availability, capacity utilization)
- **Professional reports** ready for stakeholders

## 📖 **Try Different Examples**

### 1. Complete Pipeline Demo (Recommended First)
```bash
python test_complete_pipeline.py
```
**Creates**: Realistic plant data + comprehensive analysis + visualizations

### 2. Export System Demo
```bash
python demo_integrated_exports.py  
```
**Shows**: Multi-format exports (CSV, Excel, JSON, Pickle)

### 3. Legacy Script Replacement Example
```bash
python example_usage_replacing_study_files.py
```  
**Demonstrates**: How this replaces copy-paste analysis scripts

## 💡 **How It Works (Simple Version)**

**The Problem**: Solar analysts copy/paste 500+ line scripts for each plant
**The Solution**: One configurable workflow for any plant

```
Your Solar Data  →  Simple Config  →  Complete Analysis
   (CSV files)       (Python dict)     (Reports + Charts)
```

**3-Step Process:**
1. **📁 Extract**: Read your CSV/Excel files  
2. **⚙️ Transform**: Clean data + calculate performance metrics
3. **📊 Load**: Generate reports, charts, and export files

**Key Benefit**: Change config = analyze different plant. No code changes needed.

## 🛠️ **Analyze Your Own Data**

### Method 1: Quick Analysis (Start Here!)

```python
from etl.workflow_orchestrator import SolarPlantWorkflowOrchestrator, PlantAnalysisConfig

# Simple configuration for your plant
config = PlantAnalysisConfig(
    project_name="My_Solar_Plant_2023",
    country="USA",
    analysis_period=("2023-01-01", "2023-12-31"),
    
    # Point to YOUR data files  
    data_sources={
        'meter': 'my_data/energy_meter.csv',        # Energy production
        'irradiance': 'my_data/weather_station.csv'  # Solar irradiance  
    },
    
    # Your plant specs
    plant_parameters={
        'capacity_kw': 5000,    # 5MW plant
        'expected_pr': 0.85     # Expected performance ratio
    },
    
    # What analysis to run
    analysis_types=['pr_analysis', 'fault_detection']
)

# Run the analysis
orchestrator = SolarPlantWorkflowOrchestrator()
results = orchestrator.run_comprehensive_plant_analysis(config)

print(f"Analysis complete! Average PR: {results.pr_analysis['statistics']['daily_mean_pr']:.2%}")
```

### Method 2: With Visualizations + Reports

```python
# Same config as above, plus:
config.generate_plots = True
config.output_directory = "my_plant_reports/"

# Run analysis  
results = orchestrator.run_comprehensive_plant_analysis(config)

# Export everything
from etl.load import export_complete_analysis
files = export_complete_analysis(
    analysis_results=results,
    output_directory="exports/", 
    formats=['excel', 'csv'],
    create_reports=True
)

print(f"Generated {len(files)} report files!")
```

### Generate Visualizations Too

```python
# Add visualization generation to your analysis
from etl.visualization import QuickVisualizer

# Generate charts
visualizer = QuickVisualizer(interactive=False)  # Creates PNG files
plots = visualizer.quick_overview({
    'pr_results': results.pr_analysis,
    'fault_results': results.string_analysis,
    'availability_stats': results.statistical_summary
})

# Save all plots
saved_plots = visualizer.show_all_plots(plots)
print(f"Created {len(saved_plots)} visualization charts!")

# Charts created: pr_timeseries.png, fault_timeline.png, etc.
```

---

## 📁 **Data Format Requirements**

### Expected Data Structure

Your CSV files should have these columns:

**Energy Meter Data** (`meter.csv`):
```csv
Timestamp,E_Meter
2023-01-01 00:00:00,1250.5
2023-01-01 00:15:00,1251.2
...
```

**Irradiance Data** (`irradiance.csv`):
```csv
Timestamp,GTI,GHI,DHI
2023-01-01 00:00:00,0,0,0
2023-01-01 06:00:00,450.2,420.1,180.5
...
```

**Temperature Data** (`temperature.csv`):  
```csv
Timestamp,Tamb,Tmod
2023-01-01 00:00:00,15.2,15.5
...
```

### Data Quality Tips
- ✅ **Consistent timestamps**: Use ISO format (YYYY-MM-DD HH:MM:SS)
- ✅ **Regular intervals**: 15-minute intervals typical for solar plants
- ✅ **Missing data handling**: Use NaN for missing values, not 0
- ✅ **Column naming**: Standard names (E_Meter, GTI, GHI, etc.)

---

## 🔧 **Customization Examples**

### Adding New Analysis Types
```python
# Custom fault detection threshold
config.plant_parameters['fault_threshold'] = 0.10  # 10% deviation

# Multi-azimuth plant setup
config.plant_parameters.update({
    'multi_azimuth': True,
    'azimuth_capacities': {
        '180': 2500000,  # South-facing: 2.5 MW
        '270': 1500000   # West-facing: 1.5 MW  
    }
})
```

### Custom Export Options
```python
# Export only specific analysis results
from etl.load.analytics_exporter import AnalyticsResultsExporter

exporter = AnalyticsResultsExporter()
files = exporter.export_specific_results(
    pr_results=results.pr_analysis,
    output_dir="custom_export/",
    formats=['csv'],
    compress_output=True
)
```

---

## 📊 **Understanding Your Results**

### Key Metrics Explained

**Performance Ratio (PR)**
- **What**: Ratio of actual vs. theoretical energy production
- **Good Range**: 80-90% for most solar plants
- **Formula**: PR = (Actual Energy / Reference Energy) × 100

**Data Availability**
- **What**: Percentage of expected data points received
- **Target**: >95% for reliable analysis
- **Impact**: Low availability affects analysis reliability

**String Fault Detection**
- **What**: Identifies underperforming string circuits
- **Method**: Statistical comparison of string currents
- **Action**: Flagged strings need maintenance inspection

### Sample Output Interpretation
```python
# Typical analysis results
Plant Performance Ratio: 85.6% (Target: 87%)     # Slightly below target
String Faults Detected: 3 periods               # Needs investigation
Data Availability: 99.1% (irradiance)          # Excellent
                   98.7% (power)                # Good
Clipping Losses: 2.3%                          # Within acceptable range
```

---

## 🚨 **Troubleshooting**

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'etl'`
```bash
# Solution: Install in development mode
pip install -e .
```

**Problem**: `FileNotFoundError` when running examples
```bash
# Solution: Create sample data or use demo mode
python demo_integrated_exports.py  # Uses mock data
```

**Problem**: Out of memory for large datasets
```python
# Solution: Use chunked processing
config.processing_options = {
    'chunk_size': 10000,  # Process in smaller chunks
    'parallel_processing': True
}
```

**Problem**: Analysis results seem wrong
```python
# Check data quality first
from etl.utils.validators import DataQualityChecker

checker = DataQualityChecker()
quality_report = checker.assess_data_quality(your_data)
print(quality_report.summary)
```

### Getting Help

1. **Check the logs**: All operations log to console with detailed error messages
2. **Validate your data**: Use the built-in data quality checker
3. **Start simple**: Use `run_quick_performance_assessment()` first
4. **Check examples**: Study `demo_integrated_exports.py` for patterns

---

## 🎓 **Next Steps**

### Learn More
1. **Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
2. **Portfolio Context**: See [PORTFOLIO.md](PORTFOLIO.md) for project background  
3. **Code Examples**: Study the `demo_` and `example_` files

### Advanced Usage
1. **Custom Analytics**: Extend the `etl.analytics` module with your algorithms
2. **New Data Sources**: Add readers in `etl.extract.readers`  
3. **Export Formats**: Create new writers in `etl.load.writers`

### Production Deployment
1. **Scheduling**: Set up cron jobs for automated analysis
2. **Monitoring**: Use the logging module for production monitoring
3. **Scaling**: Deploy across multiple servers for large plant portfolios

---

## 💼 **Professional Use Cases**

This platform is production-ready and suitable for:

- **O&M Companies**: Automated performance monitoring
- **Asset Managers**: Portfolio-wide analytics and reporting
- **Engineering Teams**: Detailed fault investigation and root cause analysis
- **Consultants**: Standardized performance assessments across projects
- **Developers**: Foundation for custom solar analytics applications

---

**🎯 You're now ready to analyze solar plant data like a pro!** Start with the quick demo and work your way up to comprehensive analyses.