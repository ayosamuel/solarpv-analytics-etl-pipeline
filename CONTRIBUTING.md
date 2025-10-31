# Contributing to Utility-scale Solar Analytics ETL and ML Workflow

Thank you for your interest in this Utility-scale solar analytics ETL and ML workflow! This is a **portfolio project** demonstrating production-quality ETL engineering for solar plant analytics.

## 🎯 **Project Status**

This repository showcases:
- **Production-grade code architecture** and design patterns
- **Real-world problem solving** in renewable energy analytics
- **Software engineering best practices** for data processing pipelines
- **Technical communication** through documentation and examples

## 🤝 **How to Contribute**

While this is primarily a portfolio project, contributions are welcome in these areas:

### 1. **Bug Reports & Issues**
Found a bug or have a suggestion? Please open an issue:
- **Describe the problem** clearly with steps to reproduce
- **Include sample data** or code snippets where possible  
- **Specify your environment** (Python version, OS, data size)

### 2. **Documentation Improvements**
Help make the project more accessible:
- **Fix typos** or improve clarity in README, docs, or code comments
- **Add usage examples** for different solar plant configurations
- **Improve getting started guide** based on your experience

### 3. **Code Enhancements**
Contribute to the codebase:
- **Performance optimizations** for large dataset processing
- **Additional data format support** (new readers/writers)
- **Enhanced analytics algorithms** (fault detection, performance modeling)
- **Better error handling** and user feedback

### 4. **Testing & Validation**
Help improve reliability:
- **Unit tests** for new functionality
- **Integration tests** with real solar plant data
- **Documentation tests** to ensure examples work
- **Performance benchmarks** for different plant sizes

---

## 🛠️ **Development Setup**

### Prerequisites
```bash
# Python 3.8+ required
python --version

# Clone the repository  
git clone https://github.com/ayosamuel/solarpv-analytics-etl-pipeline.git
cd solarpv-analytics-etl-pipeline
```

### Installation
```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -e .[dev]

# Verify installation
python demo_integrated_exports.py
```

### Development Environment
```bash
# Recommended: Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

---

## 📋 **Code Standards**

### **Python Style Guide**
- **Follow PEP 8** for code formatting
- **Use type hints** for function parameters and return values
- **Write docstrings** for all public classes and functions
- **Keep functions focused** - single responsibility principle

### **Example Code Style**
```python
from typing import Dict, List, Optional, Tuple
import pandas as pd

class DataProcessor:
    """Processes solar plant data with validation and error handling.
    
    This class handles the transformation stage of the ETL pipeline,
    providing data cleaning, validation, and performance calculations
    for solar plant analytics.
    """
    
    def __init__(self, config: ConfigManager) -> None:
        """Initialize processor with configuration.
        
        Args:
            config: Configuration manager with processing parameters
        """
        self.config = config
        self.logger = config.get_logger(__name__)
    
    def clean_irradiance_data(
        self, 
        data: pd.DataFrame, 
        quality_threshold: float = 0.95
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """Clean and validate irradiance sensor data.
        
        Removes outliers, fills gaps, and validates sensor readings
        according to solar industry best practices.
        
        Args:
            data: Raw irradiance measurements with timestamp index
            quality_threshold: Minimum data quality score (0-1)
            
        Returns:
            Tuple of (cleaned_data, quality_metrics)
            
        Raises:
            DataQualityError: If data quality below threshold
        """
        # Implementation here...
        pass
```

### **Architecture Principles**
1. **ETL Separation**: Keep Extract/Transform/Load modules independent
2. **Single Responsibility**: Each class should have one clear purpose  
3. **Dependency Inversion**: Depend on interfaces, not concrete implementations
4. **Open/Closed**: Open for extension, closed for modification

### **Error Handling**
```python
# Good: Specific exceptions with helpful messages
try:
    results = processor.analyze_plant_data(config)
except DataQualityError as e:
    logger.error(f"Data quality insufficient for analysis: {e}")
    return generate_partial_results(available_data)
except ConfigurationError as e:
    logger.error(f"Invalid plant configuration: {e}")
    return suggest_configuration_fix(config)
```

---

## 🧪 **Testing Guidelines**

### **Test Structure**
```bash
tests/
├── unit/           # Unit tests for individual functions
├── integration/    # End-to-end pipeline tests  
├── data/          # Sample test data
└── conftest.py    # Pytest configuration
```

### **Writing Tests**
```python
import pytest
import pandas as pd
from etl.transform.cleaners import DataCleaner

class TestDataCleaner:
    """Test suite for DataCleaner functionality."""
    
    @pytest.fixture
    def sample_irradiance_data(self):
        """Create sample irradiance data for testing."""
        return pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=100, freq='15min'),
            'GTI': [500 + 100 * np.random.randn() for _ in range(100)]
        })
    
    def test_clean_series_removes_outliers(self, sample_irradiance_data):
        """Test that outlier removal works correctly."""
        cleaner = DataCleaner()
        cleaned_data, report = cleaner.clean_series(sample_irradiance_data['GTI'], 'irradiance')
        
        assert len(cleaned_data) <= len(sample_irradiance_data)
        assert report['outliers_removed'] >= 0
        assert report['quality_score'] > 0.8
```

### **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=etl --cov-report=html

# Run specific test file
pytest tests/unit/test_cleaners.py -v
```

---

## 📝 **Documentation Standards**

### **Docstring Format**
Use **Google-style docstrings** for consistency:

```python
def calculate_performance_ratio(
    energy_actual: pd.Series,
    energy_reference: pd.Series,
    temperature_data: Optional[pd.Series] = None
) -> PRResults:
    """Calculate Performance Ratio with temperature corrections.
    
    Performance Ratio (PR) is the ratio of actual energy output to
    theoretical energy output, accounting for environmental conditions.
    
    Args:
        energy_actual: Measured energy production (kWh)
        energy_reference: Theoretical energy at STC (kWh)  
        temperature_data: Module temperature measurements (°C), optional
        
    Returns:
        PRResults object containing:
            - pr_value: Performance ratio (0-1)
            - temperature_corrected_pr: Temperature-adjusted PR
            - uncertainty: Measurement uncertainty (%)
            
    Raises:
        ValueError: If energy data contains negative values
        DataAlignmentError: If timestamp alignment fails
        
    Example:
        >>> pr_calc = PerformanceRatioCalculator()
        >>> results = pr_calc.calculate_performance_ratio(actual, reference)
        >>> print(f"Plant PR: {results.pr_value:.1%}")
        Plant PR: 85.6%
    """
```

### **README Updates**
When adding features, update relevant documentation:
- **Architecture diagrams** in ARCHITECTURE.md
- **Usage examples** in GETTING_STARTED.md  
- **Feature descriptions** in README.md

---

## 🚀 **Contribution Workflow**

### **1. Fork & Branch**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ibv_datamine.git

# Create feature branch
git checkout -b feature/your-feature-name
```

### **2. Development**
```bash
# Make your changes
# Add tests for new functionality
# Update documentation

# Run tests locally
pytest
python demo_integrated_exports.py
```

### **3. Submit Pull Request**
```bash
# Commit your changes
git add .
git commit -m "feat: Add new solar analytics algorithm

- Implement enhanced string fault detection
- Add temperature correlation analysis  
- Include comprehensive test coverage
- Update documentation with usage examples"

# Push to your fork
git push origin feature/your-feature-name
```

**Pull Request Template:**
```markdown
## Description
Brief description of changes and motivation

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No new warnings introduced
```

---

## 🎓 **Learning & Professional Development**

### **Skills Demonstrated in This Project**
Contributing to this Utility-scale solar analytics ETL and ML workflow helps you learn:

- **ETL Architecture**: Production-scale data pipeline design
- **Software Design Patterns**: Factory, Strategy, Observer patterns in practice
- **Data Engineering**: Time-series processing, data validation, error handling
- **Domain Expertise**: Solar energy analytics and performance modeling
- **Testing**: Unit testing, integration testing, test-driven development
- **Documentation**: Technical writing, API documentation, architecture docs

### **Industry Best Practices**
This project follows renewable energy industry standards:
- **IEC 61724**: Performance monitoring guidelines
- **IEC 61853**: Power rating procedures  
- **ASTM E2848**: Solar irradiance measurement standards

---

## 🌟 **Recognition**

Contributors will be acknowledged in:
- **README.md**: Contributors section
- **Release notes**: Feature attribution  
- **LinkedIn recommendations**: For significant contributions (with permission)

---

## 📞 **Questions & Support**

- **Technical Questions**: Open an issue with the `question` label
- **Architecture Discussions**: Use the `discussion` label
- **Feature Requests**: Use the `enhancement` label

---

## 📄 **License**

By contributing to this Utility-scale solar analytics ETL and ML workflow, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make this Utility-scale solar analytics ETL and ML workflow better! 🚀**

*This project demonstrates production-quality engineering practices in renewable energy analytics - your contributions help showcase best practices in data engineering and software architecture.*