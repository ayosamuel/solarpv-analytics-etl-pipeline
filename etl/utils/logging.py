"""
Logging utilities for the ETL pipeline
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger for ETL operations
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def log_operation(logger: logging.Logger, operation: str):
    """
    Decorator to log ETL operations
    
    Args:
        logger: Logger instance
        operation: Operation description
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Starting {operation}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed {operation}")
                return result
            except Exception as e:
                logger.error(f"Failed {operation}: {str(e)}")
                raise
        return wrapper
    return decorator