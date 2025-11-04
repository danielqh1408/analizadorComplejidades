"""
Unit Tests for the Configuration Loader Service (src/services/config_loader.py)
"""

import pytest
import os
from src.services.config_loader import ConfigLoader
from unittest.mock import patch

def test_config_singleton(config_loader_instance):
    """Tests that get_instance() always returns the same object."""
    instance1 = ConfigLoader.get_instance()
    instance2 = ConfigLoader.get_instance()
    assert instance1 is instance2
    assert instance1 is config_loader_instance

def test_config_load_string(monkeypatch):
    """
    Prueba que el ConfigLoader lee valores string (como el modo)
    correctamente, forzando el modo 'testing'.
    """

    monkeypatch.setenv("APP_ENV", "testing") 
    config = ConfigLoader.get_instance()
    
    ConfigLoader._instance = None
    monkeypatch.setenv("APP_ENV", "testing")
    config = ConfigLoader.get_instance()

    mode = config.get("ENVIRONMENT", "mode")
    
    assert mode == "testing"

def test_config_load_int(config_loader_instance):
    """Tests loading an integer value."""
    workers = config_loader_instance.get_int('HARDWARE', 'cpu_workers')
    assert workers == 16

def test_config_load_bool(config_loader_instance):
    """Tests loading a boolean value."""
    use_gpu = config_loader_instance.get_bool('HARDWARE', 'use_gpu')
    assert use_gpu is True

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

def test_config_get_api_key_from_env(config_loader_instance, monkeypatch):
    """
    Tests that get_api_key() reads the env var *name* from config
    and retrieves the *value* from the (patched) os.environ.
    """
    
    # 1. Definir el nombre falso de la variable y su valor falso
    MOCK_ENV_VAR_NAME = "TEST_GEMINI_KEY"
    MOCK_API_KEY_VALUE = "fake-gemini-key-123"

    # Esto asegura que os.getenv("TEST_GEMINI_KEY") devuelva el valor falso
    monkeypatch.setenv(MOCK_ENV_VAR_NAME, MOCK_API_KEY_VALUE)

    # Esto simula que el config.ini dice:
    # [SECURITY]
    # gemini_api_key_env = "TEST_GEMINI_KEY"
    def mock_get(section, key):
        if section == 'SECURITY' and key == 'gemini_api_key_env':
            return MOCK_ENV_VAR_NAME
        # (Opcional) puedes levantar un error si no es lo que esperas
        raise KeyError(f"Llamada inesperada a mock_get: {section}.{key}")

    monkeypatch.setattr(config_loader_instance, "get", mock_get)

    # get_api_key llamará a config.get('SECURITY', 'gemini_api_key_env'),
    # que devolverá "TEST_GEMINI_KEY" gracias al parche.
    # Luego llamará a os.getenv("TEST_GEMINI_KEY"),
    # que devolverá "fake-gemini-key-123" gracias al parche.
    api_key = config_loader_instance.get_api_key('gemini_api_key_env')

    assert api_key == MOCK_API_KEY_VALUE

def test_config_get_api_key_missing_env_var(config_loader_instance, monkeypatch):
    """Prueba que get_api_key() lanza KeyError si la variable de entorno no está seteada."""
    
    MOCK_ENV_VAR_NAME = "TEST_GEMINI_KEY_MISSING"

    # Forzamos a que 'get' devuelva el nombre de nuestra variable de prueba
    def mock_get(section, key):
        if section == 'SECURITY' and key == 'gemini_api_key_env':
            return MOCK_ENV_VAR_NAME
        # Si la prueba intenta leer otra cosa, fallamos (es un buen seguro)
        raise KeyError(f"Llamada inesperada a mock_get: {section}.{key}")

    monkeypatch.setattr(config_loader_instance, "get", mock_get)

    # 'raising=False' evita que falle si la variable ya no existía
    monkeypatch.delenv(MOCK_ENV_VAR_NAME, raising=False)

    expected_error_regex = f"Environment variable '{MOCK_ENV_VAR_NAME}' is not set"

    with pytest.raises(KeyError, match=expected_error_regex):
        config_loader_instance.get_api_key('gemini_api_key_env')