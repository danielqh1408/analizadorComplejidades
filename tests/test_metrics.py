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
    metrics_logger_instance.start_timer(label)
    time.sleep(0.01) # Sleep for 10ms
    elapsed = metrics_logger_instance.end_timer(label)
    
    # Config time_unit is 'milliseconds', multiplier is 1000
    assert elapsed > 10
    assert elapsed < 50 # Should be fast
    
    # Check that the metric was also logged
    assert len(metrics_logger_instance.metrics) == 1
    assert metrics_logger_instance.metrics[0]['label'] == label
    assert metrics_logger_instance.metrics[0]['value'] == elapsed
    assert metrics_logger_instance.metrics[0]['unit'] == "milliseconds"

def test_metrics_log(metrics_logger_instance):
    """Tests the arbitrary log method."""
    metrics_logger_instance.log("tokens", 120, "count")
    
    assert len(metrics_logger_instance.metrics) == 1
    assert metrics_logger_instance.metrics[0]['label'] == "tokens"
    assert metrics_logger_instance.metrics[0]['value'] == 120
    assert metrics_logger_instance.metrics[0]['unit'] == "count"

def test_metrics_save_to_file(metrics_logger_instance, tmp_path):
    """Tests saving metrics to a JSON file."""
    metrics_logger_instance.log("test_save", "data")
    metrics_logger_instance.save()
    
    # The output path is patched in the fixture to tmp_path
    output_file = tmp_path / "test_metrics.json"
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['label'] == "test_save"
    assert data[0]['value'] == "data"

def test_metrics_disabled(metrics_logger_instance):
    """Tests that methods are no-ops when disabled."""
    metrics_logger_instance.enabled = False
    
    metrics_logger_instance.start_timer("disabled_timer")
    elapsed = metrics_logger_instance.end_timer("disabled_timer")
    metrics_logger_instance.log("disabled_log", 1)
    
    assert elapsed is None
    assert len(metrics_logger_instance.metrics) == 0
    assert len(metrics_logger_instance.timers) == 0

def test_metrics_thread_safety(metrics_logger_instance):
    """A simple test for thread-safe logging."""
    num_threads = 10
    
    def log_metric():
        metrics_logger_instance.log("threaded_metric", 1, "unit")

    threads = [threading.Thread(target=log_metric) for _ in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert len(metrics_logger_instance.metrics) == num_threads
    assert metrics_logger_instance.metrics[0]['value'] == 1