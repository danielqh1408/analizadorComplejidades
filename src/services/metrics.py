"""
Centralized Metrics Management Service

Provides a thread-safe Singleton class for recording, tracking, and 
reporting performance metrics (e.g., execution time, token counts).
Reads configuration from the global ConfigLoader.

Usage in other modules:
    from src.services.metrics import metrics_logger
    
    metrics_logger.start_timer("my_task")
    # ... perform task ...
    metrics_logger.end_timer("my_task")
    
    metrics_logger.log("tokens_processed", 120, "tokens")
    metrics_logger.save()
"""

import time
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Dict, List

# Import project-specific services
try:
    from src.services.config_loader import config
    from src.services.logger import get_logger
except ImportError as e:
    print(f"FATAL ERROR: Failed to import base services (ConfigLoader, Logger). {e}")
    # Fallback logger if main logger fails
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    config = None # Ensure a fallback
else:
    logger = get_logger(__name__)

class MetricsLogger:
    """
    Singleton class for logging performance metrics.
    
    Handles timing of operations and logging arbitrary key-value metrics.
    Operates in a thread-safe manner. If disabled in config.ini,
    all methods become lightweight no-ops.
    """
    _instance: Optional['MetricsLogger'] = None
    _lock = threading.Lock()

    def __init__(self):
        """
        Private constructor. Use get_instance() instead.
        Initializes configuration, data stores, and thread lock.
        """
        if MetricsLogger._instance:
            raise RuntimeError("MetricsLogger is a Singleton. Use get_instance().")
        
        if config is None:
            logger.error("ConfigLoader failed to load; MetricsLogger will be disabled.")
            self.enabled = False
            return

        # Load configuration
        self.enabled = config.get_bool('PERFORMANCE', 'enable_metrics', default=False)
        self.output_path = config.get_path('PERFORMANCE', 'metrics_output_path')
        self.time_unit = config.get('PERFORMANCE', 'time_unit', default='seconds').lower()
        
        if self.time_unit == 'milliseconds':
            self.time_multiplier = 1000.0
        else:
            self.time_multiplier = 1.0

        # Internal data stores
        self.metrics: List[Dict[str, Any]] = []
        self.timers: Dict[str, float] = {}
        self.data_lock = threading.Lock() # Lock for data structures

        if self.enabled:
            logger.info(f"MetricsLogger enabled. Time unit: {self.time_unit}. Output: {self.output_path}")
        else:
            logger.info("MetricsLogger is disabled in config.ini.")

    @classmethod
    def get_instance(cls) -> 'MetricsLogger':
        """
        Provides access to the singleton instance, creating it if necessary.
        
        Returns:
            MetricsLogger: The single, shared instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start_timer(self, label: str):
        """
        Starts a high-precision performance timer for a given label.
        
        Args:
            label (str): A unique identifier for the timer.
        """
        if not self.enabled:
            return

        with self.data_lock:
            self.timers[label] = time.perf_counter()
        
        logger.debug(f"Timer started: '{label}'")

    def end_timer(self, label: str) -> Optional[float]:
        """
        Stops a timer, logs the duration as a metric, and returns the value.
        
        If the timer was not started, logs a warning and returns None.
        
        Args:
            label (str): The unique identifier for the timer.
            
        Returns:
            Optional[float]: The elapsed time in the configured unit, or None.
        """
        if not self.enabled:
            return None
        
        start_time: Optional[float] = None
        with self.data_lock:
            start_time = self.timers.pop(label, None)
            
        if start_time is None:
            logger.warning(f"end_timer() called for non-existent timer: '{label}'")
            return None
            
        elapsed_sec = time.perf_counter() - start_time
        elapsed_configured = elapsed_sec * self.time_multiplier
        
        # Log the result automatically
        self.log(label, elapsed_configured, self.time_unit)
        
        return elapsed_configured

    def log(self, label: str, value: Any, unit: str = ""):
        """
        Logs an arbitrary key-value metric.
        
        Args:
            label (str): The name of the metric (e.g., "tokens_processed").
            value (Any): The value of the metric (e.g., 1500).
            unit (str): The unit of measurement (e.g., "tokens").
        """
        if not self.enabled:
            return

        metric_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "value": value,
            "unit": unit
        }
        
        with self.data_lock:
            self.metrics.append(metric_entry)
            
        logger.info(f"Metric logged: {label} = {value} {unit}")

    def _ensure_dir(self):
        """
        Internal helper to create the output directory if it doesn't exist.
        """
        if not self.output_path:
            return
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        except (IOError, OSError) as e:
            logger.error(f"Failed to create metrics directory: {self.output_path.parent}", exc_info=e)

    def save(self):
        """
        Saves all collected metrics to the JSON file specified in config.ini.
        This operation is thread-safe and writes a snapshot of the metrics.
        """
        if not self.enabled:
            return
            
        if not self.output_path:
            logger.warning("Metrics saving skipped: 'metrics_output_path' not set in config.")
            return

        # Snapshot the data inside the lock
        with self.data_lock:
            if not self.metrics:
                logger.info("Metrics saving skipped: No metrics to save.")
                return
            metrics_snapshot = list(self.metrics) # Create a shallow copy
            # Optionally clear metrics after saving
            # self.metrics.clear() 

        # Perform I/O outside the lock
        self._ensure_dir()
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_snapshot, f, indent=4)
            logger.info(f"Successfully saved {len(metrics_snapshot)} metrics to {self.output_path}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to write metrics file to {self.output_path}", exc_info=e)

    def summary(self):
        """
        Logs a summary of the metrics collected so far.
        """
        if not self.enabled:
            return

        with self.data_lock:
            count = len(self.metrics)
            timer_count = len(self.timers)
            
        logger.info("--- Metrics Summary ---")
        logger.info(f"  Metrics logged: {count}")
        logger.info(f"  Active timers: {timer_count}")
        if timer_count > 0:
            logger.warning(f"  Active timers (may indicate un-ended timers): {list(self.timers.keys())}")
        logger.info("-----------------------")


# --- Global Instance ---
# Provides a single, easy-to-import instance for all other modules.
metrics_logger = MetricsLogger.get_instance()


# --- Demo Block ---
# Run with: python src/services/metrics.py
if __name__ == "__main__":
    
    logger.info("--- 🚀 Iniciando Demo del MetricsLogger ---")

    # 1. Get the instance
    m_log = MetricsLogger.get_instance()
    
    # Check if another instance call returns the same object
    m_log_2 = MetricsLogger.get_instance()
    assert m_log is m_log_2
    logger.info(f"Singleton test passed: {id(m_log) == id(m_log_2)}")

    if m_log.enabled:
        # 2. Test logging
        m_log.log("tokens_processed", 1234, "tokens")
        m_log.log("llm_call_count", 1, "calls")
        
        # 3. Test timers
        m_log.start_timer("parsing_task")
        time.sleep(0.05) # Simulate work (50ms)
        elapsed = m_log.end_timer("parsing_task")
        logger.info(f"Parsing task took: {elapsed} {m_log.time_unit}")
        
        # 4. Test un-ended timer
        m_log.start_timer("orphaned_timer")
        
        # 5. Test summary
        m_log.summary()
        
        # 6. Test saving
        m_log.save()
        
        logger.info(f"Demo finished. Check the log and the file at '{m_log.output_path}'")
    else:
        logger.warning("MetricsLogger is disabled. Demo functions were skipped.")