"""
Unit Tests for the Configuration Loader Service (src/services/config_loader.py)
"""

import pytest
import os
from src.services.config_loader import ConfigLoader

def test_config_singleton(config_loader_instance):
    """Tests that get_instance() always returns the same object."""
    instance1 = ConfigLoader.get_instance()
    instance2 = ConfigLoader.get_instance()
    assert instance1 is instance2
    assert instance1 is config_loader_instance

def test_config_load_string(config_loader_instance):
    """Tests loading a standard string value."""
    mode = config_loader_instance.get('ENVIRONMENT', 'mode')
    assert mode == "testing"

def test_config_load_int(config_loader_instance):
    """Tests loading an integer value."""
    workers = config_loader_instance.get_int('HARDWARE', 'cpu_workers')
    assert workers == 4

def test_config_load_bool(config_loader_instance):
    """Tests loading a boolean value."""
    use_gpu = config_loader_instance.get_bool('HARDWARE', 'use_gpu')
    assert use_gpu is False

def test_config_load_path(config_loader_instance):
    """Tests that paths are resolved correctly."""
    log_dir = config_loader_instance.get_path('PATHS', 'log_dir')
    assert log_dir.is_absolute()
    assert log_dir.name == "logs"

def test_config_missing_key_raises_error(config_loader_instance):
    """Tests that accessing a non-existent key raises KeyError."""
    with pytest.raises(KeyError):
        config_loader_instance.get('ENVIRONMENT', 'missing_key')

def test_config_missing_section_raises_error(config_loader_instance):
    """Tests that accessing a non-existent section raises KeyError."""
    with pytest.raises(KeyError):
        config_loader_instance.get('MISSING_SECTION', 'mode')

def test_config_get_api_key_from_env(config_loader_instance):
    """
    Tests that get_api_key() reads the env var *name* from config
    and retrieves the *value* from the (patched) os.environ.
    """
    # This is patched in conftest.py:
    # [SECURITY].gemini_api_key_env = "TEST_GEMINI_KEY"
    # os.environ["TEST_GEMINI_KEY"] = "fake-gemini-key-123"
    
    api_key = config_loader_instance.get_api_key('gemini_api_key_env')
    assert api_key == "fake-gemini-key-123"

def test_config_get_api_key_missing_env_var(config_loader_instance):
    """Tests that get_api_key() raises KeyError if the env var is not set."""
    # Temporarily remove the key from the patched environment
    with patch.dict(os.environ, clear=True):
        with pytest.raises(KeyError, match="Environment variable 'TEST_GEMINI_KEY' is not set"):
            config_loader_instance.get_api_key('gemini_api_key_env')