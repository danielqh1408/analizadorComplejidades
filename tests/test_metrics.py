"""
Unit Tests for the Metrics Service (src/services/metrics.py)
"""

import pytest
import time
import json
import threading
from src.services.metrics import MetricsLogger

def test_metrics_singleton():
    """Tests the singleton pattern."""
    from src.services.metrics import metrics_logger as global_instance
    instance1 = MetricsLogger.get_instance()
    instance2 = MetricsLogger.get_instance()
    assert instance1 is instance2
    assert instance1 is global_instance

def test_metrics_timer(metrics_logger_instance):
    """Tests start_timer and end_timer functionality."""
    label = "test_timer"
    metrics_logger_instance.enabled = True
    metrics_logger_instance.start_timer(label)
    time.sleep(0.01) # Sleep for 10ms
    elapsed = metrics_logger_instance.end_timer(label)
    
    # Config time_unit is 'milliseconds', multiplier is 1000
  # Should be fast
    
    # Check that the metric was also logged
    assert len(metrics_logger_instance.metrics) == 1
    assert metrics_logger_instance.metrics[0]['label'] == label
    assert metrics_logger_instance.metrics[0]['value'] == elapsed
    assert metrics_logger_instance.metrics[0]['unit'] == "milliseconds"

    assert elapsed > 10
    assert elapsed < 50 
