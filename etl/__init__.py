"""
ETL Package for Solar Plant Data Analytics

This package provides a clean Extract, Transform, Load (ETL) architecture
for solar plant data processing and analytics.
"""

__version__ = "1.0.0"
__author__ = "Data Analytics Team"

# Import core utilities that don't require external dependencies
from .utils.config import ConfigManager
from .utils.logging import setup_logger

# Lazy imports for modules that require external dependencies
def get_core_processor():
    """Get the core solar plant data processor"""
    from .core import SolarPlantDataProcessor
    return SolarPlantDataProcessor

def get_project_manager():
    """Get the project parameter manager"""
    from .core import ProjectParameterManager
    return ProjectParameterManager

def get_readers():
    """Get data readers"""
    from .extract.readers import CSVReader, WebPortalReader
    return CSVReader, WebPortalReader

def get_cleaners():
    """Get data cleaners"""
    from .transform.cleaners import DataCleaner, IrradianceCleaner
    return DataCleaner, IrradianceCleaner

def get_writers():
    """Get data writers"""
    from .load.writers import CSVWriter, ExcelWriter
    return CSVWriter, ExcelWriter