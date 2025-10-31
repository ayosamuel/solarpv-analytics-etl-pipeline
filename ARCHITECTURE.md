# Architecture Overview

## 🏗️ System Design Philosophy

The **Utility-scale solar analytics ETL and ML workflow** platform follows a clean, modular ETL architecture designed for production-grade solar plant analytics with integrated visualization and machine learning capabilities.

## 📐 Core Design Patterns

### 1. **ETL Architecture Pattern**

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   EXTRACT   │───▶│  TRANSFORM   │───▶│    LOAD     │
│             │    │              │    │             │
│ Data Sources│    │ Processing   │    │ Outputs &   │
│ Validation  │    │ Analytics    │    │ Reports     │
│ File Reading│    │ Cleaning     │    │ Exports     │
└─────────────┘    └──────────────┘    └─────────────┘
```

**Why ETL Separation?**
- **Single Responsibility**: Each module has one clear purpose
- **Testability**: Components can be tested in isolation
- **Scalability**: Can scale Extract/Transform/Load independently
- **Maintainability**: Changes in one stage don't affect others

### 2. **Factory Pattern for Data Writers**

```python
# Extensible writer creation without tight coupling
writer = WriterFactory.create_writer('output.xlsx', config)
writer.write(data, metadata)

# Supports: CSV, Excel, JSON, Pickle, Database
# Easy to add new formats without changing client code
```

**Benefits:**
- **Open/Closed Principle**: Open for extension, closed for modification
- **Polymorphism**: All writers implement same interface
- **Configuration-driven**: Format selection via file extension

### 3. **Workflow Orchestrator Pattern**

```python
# Replaces hardcoded Study files with configurable workflows
config = PlantAnalysisConfig(
    project_name="Plant_XYZ",
    analysis_types=['pr_analysis', 'fault_detection'],
    # ... configuration parameters
)
results = orchestrator.run_comprehensive_analysis(config)
```

**Key Benefits:**
- **Configuration over Code**: No more copy-paste Study files
- **Standardization**: Same analysis methodology across all plants
- **Flexibility**: Mix and match analysis types as needed

---

## 🔧 Module Breakdown

### **Extract Module** (`etl/extract/`)

**Purpose**: Data ingestion with validation and error handling

```python
etl/extract/
├── readers.py          # Multi-format data readers (CSV, Excel, databases)
├── file_handlers.py    # File system operations with error handling
└── __init__.py         # Clean public API
```

**Key Components:**

**SolarPlantDataReader**
```python
class SolarPlantDataReader:
    """Handles multi-format solar plant data ingestion"""
    
    def read_files_by_period(self, source_dir: str, data_types: List[str]) -> Dict[str, pd.DataFrame]:
        """Read multiple data types for a time period with validation"""
```

**Design Decisions:**
- **Lazy Loading**: Only load data when needed (memory efficiency)
- **Format Agnostic**: Auto-detect CSV/Excel/database sources  
- **Error Recovery**: Continue processing even if some files are corrupt
- **Metadata Preservation**: Track source files, timestamps, data quality

---

### **Transform Module** (`etl/transform/`)

**Purpose**: Data cleaning, processing, and analytics calculations

```python
etl/transform/
├── cleaners.py      # Data quality & validation (outlier detection, gap filling)
├── processors.py    # Performance calculations (PR, energy yield, fault detection)
├── aggregators.py   # Time-series aggregation (daily/monthly summaries)
└── __init__.py      # Unified transform interface
```

**Key Components:**

**DataCleaner**
```python
class DataCleaner:
    """Advanced data cleaning for solar plant sensor data"""
    
    def clean_series(self, data: pd.Series, data_type: str) -> Tuple[pd.Series, CleaningReport]:
        """Clean sensor data with detailed reporting"""
        # - Outlier detection using IQR and statistical methods
        # - Gap filling with interpolation and seasonal patterns  
        # - Sensor fault identification
        # - Data quality scoring
```

**PerformanceProcessor**  
```python
class PerformanceProcessor:
    """Solar plant performance calculations"""
    
    def calculate_performance_ratio(self, energy_data: pd.DataFrame, irradiance_data: pd.DataFrame) -> PRResults:
        """Calculate PR with temperature corrections and uncertainty analysis"""
```

**Design Decisions:**
- **Immutable Operations**: Original data never modified (creates new cleaned versions)
- **Detailed Reporting**: Every transformation provides quality metrics
- **Domain-Specific Logic**: Solar industry best practices for PR calculations
- **Statistical Rigor**: Uncertainty propagation and confidence intervals

---

### **Load Module** (`etl/load/`)

**Purpose**: Export management and report generation

```python
etl/load/
├── writers.py            # Low-level file writers (Factory pattern)
├── exporters.py          # Business logic for standardized reports  
├── analytics_exporter.py # Specialized handling of complex analytics results
├── export_manager.py     # Integrated export coordination
└── __init__.py           # Simple public interface
```

**Architecture:**

```
┌─────────────────┐
│ Client Request  │
│ export_analysis │
└─────────┬───────┘
          │
┌─────────▼───────────┐
│ IntegratedExport    │  ◄── Coordination Layer
│ Manager             │
└─────────┬───────────┘
          │
    ┌─────▼──────┐ ┌────▼─────┐ ┌────▼──────┐
    │ Analytics  │ │ Report   │ │ Data      │
    │ Exporter   │ │ Exporter │ │ Exporter  │
    └─────┬──────┘ └────┬─────┘ └────┬──────┘
          │             │            │
    ┌─────▼─────────────▼────────────▼──────┐
    │         WriterFactory                 │  ◄── Implementation Layer
    │  CSV │ Excel │ JSON │ Pickle │ DB     │
    └───────────────────────────────────────┘
```

**Design Benefits:**
- **Separation of Concerns**: Business logic separate from file I/O
- **Single Responsibility**: Each exporter handles one type of output
- **Extensibility**: Easy to add new export formats or report types
- **Consistency**: Standardized metadata and naming conventions

---

### **Analytics Module** (`etl/analytics/`)

**Purpose**: Advanced analytics and machine learning workflows

```python
etl/analytics/
├── performance_ratio.py    # PR calculations with uncertainty analysis
├── fault_detection.py      # Statistical anomaly detection
├── curve_fitting.py        # Power curve modeling
├── ml_models.py           # Predictive modeling (irradiance, performance)
├── statistical_analysis.py # Time-series analysis and trend detection
└── data_consolidation.py  # Multi-source data fusion
```

**Key Algorithms:**

**String Fault Detection**
- **Statistical Approach**: Compare string currents using z-score analysis
- **Temporal Patterns**: Identify persistent vs. transient faults
- **Weather Correlation**: Exclude weather-related variations

**Performance Ratio (PR) Calculation**
- **Temperature Correction**: IEC 61724 standard implementation
- **Uncertainty Analysis**: Monte Carlo error propagation
- **Multi-Azimuth Support**: Complex plant geometries

---

### **Visualization Module** (`etl/visualization/`)

**Purpose**: Quick visualization and dashboard generation for analytics results

```python
etl/visualization/
├── plotters.py          # Core plotting utilities for analytics results
├── dashboards.py        # Interactive dashboards for single/multi-plant analysis  
├── export_plots.py      # Plot export and report generation
└── __init__.py          # Unified visualization interface
```

**Key Components:**

**QuickVisualizer Class**
```python
class QuickVisualizer:
    """Generate professional charts from analytics results"""
    
    def quick_overview(self, analytics_data: Dict) -> Dict[str, Figure]:
        """Create comprehensive visualization suite"""
        # - PR time series with trend lines
        # - Fault detection timelines with severity coding  
        # - Statistical distribution plots
        # - Correlation matrices and heatmaps
```

**Dashboard Generation**
- **Single Plant**: Complete performance analysis dashboards
- **Multi-Plant**: Comparative analytics across plant portfolios
- **Interactive Charts**: Plotly-based interactive visualizations
- **Static Reports**: PNG exports for executive presentations

**Export Capabilities**
- **Multiple Formats**: PNG, HTML (interactive), JSON for web integration
- **Automated Reports**: HTML reports with embedded plots and statistics  
- **Professional Styling**: Consistent branding and color schemes

---

### **Utils Module** (`etl/utils/`)

**Purpose**: Cross-cutting concerns and shared utilities

```python
etl/utils/
├── config.py       # Configuration management with validation
├── logging.py      # Structured logging for production systems
├── validators.py   # Data validation rules and business logic
├── helpers.py      # Common utility functions
└── __init__.py     # Utility consolidation
```

---

## 🔄 Data Flow Architecture

### **High-Level Data Flow**
```
Solar Plant Sensors
        ↓
    File Systems (CSV/Excel)
        ↓
┌──────────────────────────┐
│     ETL Pipeline         │
│                          │
│  Extract → Transform     │
│     ↓        ↓          │
│  Validate   Clean       │
│     ↓        ↓          │
│  Structure  Analyze     │
│     ↓        ↓          │
│     Load  ← Results     │
└──────────────────────────┘
        ↓
    Multi-format Outputs
 (Excel, JSON, Database)
        ↓
    Executive Dashboards
```

### **Detailed Processing Pipeline**

```python
# 1. EXTRACT: Multi-source data ingestion
raw_data = {
    'meter': reader.read_meter_data(),
    'irradiance': reader.read_pyranometer_data(), 
    'weather': reader.read_weather_data(),
    'inverter': reader.read_inverter_data()
}

# 2. TRANSFORM: Cleaning and processing
cleaned_data = {}
for data_type, df in raw_data.items():
    cleaned_data[data_type], report = cleaner.clean_series(df, data_type)
    
# 3. ANALYTICS: Performance calculations  
pr_results = processor.calculate_performance_ratio(cleaned_data['meter'], cleaned_data['irradiance'])
fault_results = processor.detect_string_faults(cleaned_data['inverter'])

# 4. LOAD: Export and reporting
files = exporter.export_complete_analysis(results, formats=['excel', 'json'])
```

---

## 🏛️ **Architectural Principles**

### **1. Separation of Concerns**
Each module has a single, well-defined responsibility:
- **Extract**: Data acquisition and validation
- **Transform**: Processing and analytics  
- **Load**: Export and reporting
- **Utils**: Cross-cutting support functions

### **2. Dependency Inversion**
High-level modules don't depend on low-level modules:
```python
# Analytics depends on abstractions, not concrete implementations
class PerformanceAnalyzer:
    def __init__(self, data_reader: DataReaderProtocol, exporter: ExporterProtocol):
        # Depends on interfaces, not concrete classes
```

### **3. Open/Closed Principle**
System is open for extension, closed for modification:
- New data formats: Add writer to factory
- New analysis types: Add to workflow orchestrator
- New export formats: Implement writer interface

### **4. Single Responsibility**
Each class has one reason to change:
- `DataCleaner`: Only changes if cleaning logic changes
- `WriterFactory`: Only changes if new formats are added
- `PerformanceAnalyzer`: Only changes if PR calculation logic changes

---

## 🚀 **Scalability Considerations**

### **Memory Efficiency**
```python
# Streaming processing for large datasets
for chunk in reader.read_chunks(chunk_size=10000):
    processed_chunk = transformer.process(chunk)
    writer.write_chunk(processed_chunk)
```

### **Parallel Processing**
```python
# Multi-core utilization for plant analysis
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as executor:
    futures = {executor.submit(analyze_plant, config): config 
               for config in plant_configs}
    results = [future.result() for future in futures]
```

### **Caching Strategy**
```python
# Cache expensive calculations
@lru_cache(maxsize=128)
def calculate_reference_irradiance(plant_config: PlantConfig) -> float:
    # Expensive calculation cached for repeated use
```

---

## 🔒 **Error Handling & Reliability**

### **Graceful Degradation**
```python
try:
    full_analysis = orchestrator.run_complete_analysis(config)
except DataQualityError as e:
    # Fall back to partial analysis with available data
    partial_analysis = orchestrator.run_partial_analysis(config, available_data)
    logger.warning(f"Partial analysis due to data quality: {e}")
```

### **Comprehensive Logging**
```python
# Structured logging for production debugging
logger.info("Starting plant analysis", extra={
    'plant_id': config.project_name,
    'analysis_period': config.analysis_period,
    'data_sources': list(config.data_sources.keys())
})
```

---

## 📊 **Performance Characteristics**

### **Benchmarks** (Demo Performance)
- **Sample Data**: 1 year × 15-min intervals × 8 data streams = 280K records
- **Processing Time**: < 2 minutes (full pipeline + 24 export files)
- **Memory Usage**: < 1GB peak (efficient pandas operations)
- **Output Generation**: 24 files (Excel, JSON, PNG) in single run

### **Scalability Design**
- **Single Plant**: Designed for megawatt-scale installations
- **Multi-Plant**: Configurable workflows for plant portfolios  
- **Time Series**: Multi-year analysis with daily/monthly aggregation
- **Export Flexibility**: 10+ format combinations supported

---

## 🎯 **Design Trade-offs & Rationale**

### **ETL vs. Monolithic Processing**

**✅ Chosen: ETL Separation**
- **Pro**: Clear interfaces, testable components, parallel development
- **Pro**: Can optimize each stage independently (memory, CPU, I/O)
- **Con**: More complex for simple use cases
- **Con**: Additional abstraction overhead

### **Factory Pattern vs. If/Else Chain**

**✅ Chosen: Factory Pattern for Writers**
- **Pro**: Easy to add new formats without touching existing code
- **Pro**: Polymorphic behavior through common interface  
- **Con**: Slightly more complex initial setup
- **Rationale**: Solar industry has many export format requirements

### **Configuration vs. Inheritance**

**✅ Chosen: Configuration-driven Workflows**
- **Pro**: No code changes needed for new plants
- **Pro**: Business users can configure analyses  
- **Con**: Runtime validation instead of compile-time
- **Rationale**: 50+ plants with unique requirements need flexibility

---

This architecture provides a **robust foundation** for industrial-scale solar analytics while maintaining **clean code principles** and **production reliability**.