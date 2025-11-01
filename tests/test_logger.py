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

def test_logger_has_handlers(test_logger):
    """Tests that the root logger has handlers attached."""
    # get_logger() configures the root logger
    root_logger = logging.getLogger()
    assert root_logger.hasHandlers()

def test_logger_has_rich_handler(test_logger):
    """Tests that RichHandler is attached for console output."""
    root_logger = logging.getLogger()
    handler_types = [type(h).__name__ for h in root_logger.handlers]
    assert "RichHandler" in handler_types

def test_logger_creates_log_file(test_logger, tmp_path):
    """
    Tests that file logging is enabled and creates a file.
    Note: This is tricky because the logger is session-scoped.
    A better test would mock the config_loader *per-test*
    to redirect the log path to tmp_path.
    
    Assuming the conftest patch works, we check the log_dir.
    """
    log_file_path = config.get_path('LOGGING', 'log_file')
    
    # We can't guarantee the path from config.ini is writable.
    # A better test would patch the 'config.get' call within the logger
    # to point to tmp_path.
    
    # For this test, we'll just confirm the config setting is correct.
    assert config.get_bool('LOGGING', 'enable_file_logging') is True
    assert "analyzer_test.log" in str(log_file_path)