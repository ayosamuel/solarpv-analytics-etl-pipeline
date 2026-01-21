# Solar PV Analytics ETL Pipeline

> **Transform raw solar plant data into actionable insights** — automated performance analysis, fault detection, and professional reports in minutes, not days.

## 🎯 What This Does (In Plain English)

If you're a **data analyst** working with solar power plants, you know the pain:
- Messy CSV files from multiple sensors
- Manual data cleaning taking hours
- Copy-pasting analysis scripts for each plant
- Creating reports manually in Excel

**This pipeline automates all of that.**

You point it at your solar plant data → it cleans, analyzes, and generates professional reports automatically.

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Install
git clone https://github.com/ayosamuel/solarpv-analytics-etl-pipeline.git
cd solarpv-analytics-etl-pipeline
pip install -e .

# 2. Run demo (creates sample data + full analysis)
python test_complete_pipeline.py
# This demo script generates sample solar plant data and runs a complete analysis

# 3. Check the outputs folder - you'll find:
#    ✅ Performance analysis reports
#    ✅ Fault detection results  
#    ✅ Interactive visualizations
#    ✅ Excel/CSV/JSON exports
```

**That's it!** You just ran a complete solar plant analysis.

## 💡 What You Get

### For Your Daily Work:

**📊 Automated Performance Analysis**
- Calculate Performance Ratio (PR) — industry standard metric
- Daily, monthly, and annual summaries
- Identify underperforming periods instantly

**🔍 Fault Detection**
- Find equipment problems before they cost you money
- Statistical anomaly detection on sensor data
- Prioritized alerts for maintenance teams

**📈 Professional Reports**
- Executive-ready dashboards
- Interactive charts (zoom, filter, export)
- Multiple formats: Excel, CSV, JSON, PNG

**⏱️ Time Savings**
- **Before**: Days of manual work per plant
- **After**: Minutes with this pipeline
- Scale from 1 plant to 50+ plants easily

## 🔄 How It Works

```
Your Solar Data → ETL Pipeline → Insights & Reports
   (CSV files)    → (Automated)  → (Ready to use)
```

**Three Simple Steps:**

1. **Extract**: Reads your CSV/Excel files (energy meters, weather stations, inverters)
2. **Transform**: Cleans data, removes outliers, calculates performance metrics
3. **Load**: Generates reports, visualizations, and exports in multiple formats

**The Key Benefit**: Configure once, use everywhere. No code changes needed for different plants.

## 📁 What Data You Need

Minimum requirements (any of these formats: CSV, Excel):

- **Energy Production Data**: From your meter/inverter
- **Solar Irradiance Data**: From weather station or pyranometer

Optional (for deeper analysis):
- Weather data (temperature, wind speed)
- Inverter-level data (for fault detection)
- String-level current (for detailed diagnostics)

## 💼 Real-World Example

```python
from etl.workflow_orchestrator import SolarPlantWorkflowOrchestrator, PlantAnalysisConfig

# Simple configuration
config = PlantAnalysisConfig(
    project_name="My_Solar_Plant_Q1_2024",
    analysis_period=("2024-01-01", "2024-03-31"),
    
    # Point to YOUR data
    data_sources={
        'meter': 'data/energy_production.csv',
        'irradiance': 'data/weather_station.csv'
    },
    
    # Your plant specs  
    plant_parameters={
        'capacity_kw': 5000,      # 5 MW plant
        'expected_pr': 0.85       # Expected performance
    },
    
    # What analysis to run
    analysis_types=['pr_analysis', 'fault_detection', 'visualization']
)

# Run it!
orchestrator = SolarPlantWorkflowOrchestrator()
results = orchestrator.run_comprehensive_plant_analysis(config)

# Results automatically exported to Excel, CSV, JSON + visualizations
```

**Output**: 24 files including performance reports, fault detection alerts, and interactive dashboards.

## 📊 Example Results

After running the pipeline, you get:

**Performance Analysis**
- Daily/Monthly PR trends
- Capacity factor calculations
- Energy yield vs. expected
- Data availability statistics

**Fault Detection** 
- Equipment anomalies with severity scores
- Temporal patterns (persistent vs. transient issues)
- Maintenance priority recommendations

**Visualizations**
- Time-series charts with trend lines
- Heat maps for multi-variable analysis
- Interactive dashboards you can share with stakeholders
- Professional PNG exports for presentations

## 🛠️ Key Features

✅ **Multi-Format Support**: CSV, Excel, JSON input/output  
✅ **Automated Cleaning**: Handles missing data, outliers, sensor errors  
✅ **Industry Standards**: IEC 61724 compliant PR calculations  
✅ **Scalable**: Analyze 1 plant or 100 plants with same code  
✅ **Flexible Exports**: Excel workbooks, CSV files, JSON APIs, PNG charts  
✅ **Production-Ready**: Error handling, logging, validation built-in  

## 📚 Documentation

- **[Getting Started Guide](GETTING_STARTED.md)** - Detailed setup and usage
- **[Architecture Overview](ARCHITECTURE.md)** - Technical design details
- **[Portfolio Examples](PORTFOLIO.md)** - Real-world use cases

## 🎓 Who This Is For

**Data Analysts** working with solar energy:
- Performance monitoring teams
- O&M (Operations & Maintenance) analysts  
- Asset managers needing regular reports
- Engineers doing root cause analysis

**You don't need to be a programmer** — just basic Python knowledge to configure and run.

## 🔧 Requirements

- Python 3.8 or higher
- Basic packages: pandas, numpy, matplotlib (auto-installed)

## 📄 License

MIT License - free to use for commercial and personal projects.

## 🚀 Why Use This?

**Instead of:**
- Writing custom scripts for each plant
- Manual data cleaning in Excel
- Copy-pasting code between projects
- Spending days on each analysis

**You get:**
- One configurable system for all plants
- Automated data quality checks
- Consistent, repeatable analysis
- Professional outputs in minutes

## 🤝 Contributing

Found a bug? Have a feature request? Want to add new analysis types?

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ayosamuel/solarpv-analytics-etl-pipeline/issues)
- **Email**: ayosamuel [via GitHub]

---

**Ready to automate your solar analytics?** Start with `python test_complete_pipeline.py` and see the results in 2 minutes. 🌞
