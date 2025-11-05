"""
Unit Tests for the Logging Service (src/services/logger.py)
"""

import pytest
import logging
from src.services.logger import get_logger
from src.services.config_loader import config

def test_get_logger_returns_instance():
    """Tests that get_logger returns a valid logger instance."""
    logger = get_logger("test_logger_instance")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_instance"

def test_logger_respects_config_level():
    """Tests that the logger's level is set from the mock config."""
    # From conftest.py, [LOGGING].log_level = DEBUG
    logger = get_logger("test_logger_level")
    assert logger.level == logging.DEBUG

def test_logger_has_handlers():
    """Tests that the root logger has handlers attached."""
    # get_logger() configures the root logger
    root_logger = logging.getLogger()
    assert root_logger.hasHandlers()

def test_logger_has_rich_handler():
    """Tests that a console handler (Rich or fallback) is attached."""
    root_logger = logging.getLogger()
    handler_types = [type(h).__name__ for h in root_logger.handlers]
    assert any(t in handler_types for t in ["RichHandler", "StreamHandler"])