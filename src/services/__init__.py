"""
Services Sub-package

This package provides core, cross-cutting services like
configuration, logging, and metrics.
"""

# Import key components to make them easily accessible
try:
    from .config_loader import config
    from .logger import get_logger
    from .metrics import metrics_logger
except ImportError:
    # This might happen during initial setup or if files are missing
    print("Warning: Core services (config, logger, metrics) could not be imported.")

# Define what 'from src.services import *' will import
__all__ = [
    "config",
    "get_logger",
    "metrics_logger"
]