"""
Unified Logging Service

This module provides a centralized and configurable logger for the entire 
project. It uses a thread-safe, idempotent setup function to configure 
the root logger on the first call, based on settings from config.ini.

It leverages 'rich.logging.RichHandler' for colorized, rich console output.

Usage in other modules:
    from src.services.logger import get_logger
    logger = get_logger(__name__)
    logger.info("This is an info message.")
"""

import logging
import sys
import threading
from pathlib import Path
from typing import Optional

# Attempt to import RichHandler (rich==13.8.0)
try:
    from rich.logging import RichHandler
except ImportError:
    RichHandler = None  # type: ignore
    print("Warning: 'rich' library not found. Console logging will be basic.")

# Import the global config instance
try:
    from src.services.config_loader import config
except ImportError as e:
    print(f"FATAL ERROR: ConfigLoader not found. Logger cannot be configured. {e}")
    # This is a hard dependency; if config_loader fails, logging can't work.
    raise

# Thread-lock to ensure the logger setup is atomic
_setup_lock = threading.Lock()

def get_logger(name: str = "AnalyzerApp") -> logging.Logger:
    """
    Retrieves a configured logger instance by name.

    On the first call, this function performs a thread-safe, one-time setup
    of the root logger, reading configuration from the global 'config' instance.
    All subsequent calls will return a logger instance inheriting this setup.

    Args:
        name (str): The name for the logger, typically __name__ from 
                    the calling module.

    Returns:
        logging.Logger: A configured logger instance.
    """
    root_logger = logging.getLogger()

    # Idempotency Check: If handlers are already configured, just return
    # the requested logger. This is thread-safe and efficient.
    if root_logger.hasHandlers():
        return logging.getLogger(name)

    # If not configured, acquire lock to perform one-time setup.
    with _setup_lock:
        # Double-check inside the lock in case another thread
        # completed setup while this one was waiting.
        if root_logger.hasHandlers():
            return logging.getLogger(name)

        # --- Begin One-Time Logger Configuration ---
        try:
            # 1. Get logging level from config.ini
            level_str = config.get('LOGGING', 'log_level', default='INFO')
            log_level = getattr(logging, level_str.upper(), logging.INFO)
            root_logger.setLevel(log_level)

            # 2. Get logging format from config
            log_format_str = config.get(
                'LOGGING', 
                'log_format',
                default="[%(asctime)s] [%(levelname)-8s] (%(name)s) - %(message)s"
            )
            date_format = "%Y-%m-%d %H:%M:%S"
            
            # This formatter is primarily for the file handler
            file_formatter = logging.Formatter(log_format_str, datefmt=date_format)

            # 3. Configure Console Handler (Rich or Standard)
            if config.get_bool('LOGGING', 'enable_console_logging', default=True):
                if RichHandler:
                    # Use RichHandler for beautiful, colorized console output
                    console_handler = RichHandler(
                        rich_tracebacks=True,
                        tracebacks_show_locals=False,
                        log_time_format="[%X]" # e.g., [14:30:55]
                    )
                    # RichHandler works best with a minimal formatter
                    console_handler.setFormatter(logging.Formatter(
                        "%(message)s", datefmt=""
                    ))
                else:
                    # Fallback to standard StreamHandler if rich is not installed
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setFormatter(file_formatter)
                
                console_handler.setLevel(log_level)
                root_logger.addHandler(console_handler)

            # 4. Configure File Handler
            if config.get_bool('LOGGING', 'enable_file_logging', default=True):
                try:
                    # Get log file path from config
                    log_file_str = config.get('LOGGING', 'log_file', default='logs/analyzer.log')
                    log_file_path = config.get_project_root() / log_file_str
                    
                    # Create the logs/ directory if it doesn't exist
                    log_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create the file handler
                    file_handler = logging.FileHandler(
                        log_file_path, mode='a', encoding='utf-8'
                    )
                    file_handler.setLevel(log_level)
                    file_handler.setFormatter(file_formatter)
                    root_logger.addHandler(file_handler)
                
                except (IOError, OSError) as e:
                    # Log error to console if file logging fails
                    root_logger.error(f"Failed to initialize file logger at {log_file_path}: {e}", exc_info=False)

            # 5. Handle no handlers
            if not root_logger.hasHandlers():
                root_logger.addHandler(logging.NullHandler())

            root_logger.info("Logger initialized successfully.")

        except Exception as e:
            # Catastrophic failure during logger setup
            # Fallback to a basic console logger to report the error
            print(f"FATAL: Logger configuration failed: {e}. Falling back to basic stdout logging.")
            root_logger.handlers.clear() # Clear any partial handlers
            root_logger.setLevel(logging.DEBUG)
            fallback_handler = logging.StreamHandler(sys.stdout)
            fallback_handler.setFormatter(
                logging.Formatter("[%(levelname)s] (FallbackLogger) %(message)s")
            )
            root_logger.addHandler(fallback_handler)
            root_logger.error("Logger setup failed", exc_info=True)
            
        return logging.getLogger(name)


# --- Demo Block ---
# This allows testing the logger configuration independently
# Run with: python src/services/logger.py
if __name__ == "__main__":
    
    # Get logger instances
    log1 = get_logger("MainDemo")
    log2 = get_logger("Module.Sub")
    
    log1.info("--- 🚀 Iniciando Demo del Logger ---")
    
    log1.debug("Este es un mensaje DEBUG.")
    log1.info("Este es un mensaje INFO.")
    log2.warning("Este es un mensaje WARNING desde otro logger.")
    log2.error("Este es un mensaje ERROR.")
    
    try:
        1 / 0
    except ZeroDivisionError:
        log1.critical("Este es un mensaje CRITICAL con traceback.", exc_info=True)
        
    log1.info("Demo del Logger finalizada.")