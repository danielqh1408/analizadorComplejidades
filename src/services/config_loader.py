"""
Configuration Loader Service

This module provides a Singleton class to load and access configuration
settings from 'config.ini' and environment variables.
"""

import os
import configparser
from pathlib import Path
from typing import Optional, Union

# Attempt to import dotenv for loading .env files
try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: 'python-dotenv' not found. API keys must be set manually.")
    load_dotenv = None

class ConfigLoader:
    """
    Singleton Configuration Loader.
    
    Loads settings from 'config.ini' at the project root and environment
    variables. Provides type-safe methods to access configuration values.
    """
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[configparser.ConfigParser] = None
    _project_root: Optional[Path] = None

    def __init__(self):
        """
        Private constructor. Do not call directly.
        Use ConfigLoader.get_instance() instead.
        """
        if ConfigLoader._instance is not None:
            raise RuntimeError("ConfigLoader is a Singleton. Use get_instance().")
        
        self._project_root = Path(__file__).resolve().parent.parent.parent

        if load_dotenv:
            env_path = self._project_root / '.env'
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)

        self._config = configparser.ConfigParser(interpolation=None)
        config_file_path = self._project_root / 'config.ini'

        if not config_file_path.exists():
            print(f"FATAL ERROR: config.ini not found at {config_file_path}")
            raise FileNotFoundError(f"config.ini not found at {config_file_path}")
        
        try:
            self._config.read(config_file_path)
            print(f"ConfigLoader: Successfully loaded '{config_file_path}'")
        except configparser.Error as e:
            print(f"FATAL ERROR: Failed to parse 'config.ini'. Error: {e}")
            raise

        env_mode = os.environ.get("APP_ENV")
        if env_mode:
            if not self._config.has_section("ENVIRONMENT"):
                self._config.add_section("ENVIRONMENT")
            self._config.set("ENVIRONMENT", "mode", env_mode)

    @classmethod
    def get_instance(cls) -> 'ConfigLoader':
        """
        Provides access to the singleton instance, creating it if necessary.
        
        Returns:
            ConfigLoader: The single, shared instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_project_root(self) -> Path:
        """
        Returns the calculated absolute path to the project root directory.
        
        Returns:
            Path: The project root path.
        """
        return self._project_root

    def get(self, section, key, default=None):
        """
        Retrieves a configuration value as a string.
        
        Args:
            section (str): The section name (e.g., '[PATHS]').
            key (str): The key name (e.g., 'source_dir').
            
        Returns:
            str: The configuration value.
            
        Raises:
            KeyError: If the section or key is not found.
        """
        try:
            return self._config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            if default is not None:
                print(f"WARNING: Missing key '{key}' in section '{section}', using default='{default}'")
                return default
            print(f"ERROR: Config key not found: section='{section}', key='{key}'")
            raise KeyError(f"Config key not found: {e}") from e


    def get_int(self, section: str, key: str, default: Optional[int] = None) -> int:
        """
        Retrieves a configuration value as an integer.
        
        Args:
            section (str): The section name.
            key (str): The key name.
            default (Optional[int]): Value to return if key is not found 
                                     or conversion fails. If None, raises error.
                                     
        Returns:
            int: The configuration value.
        """
        try:
            return self._config.getint(section, key)
        except (ValueError, KeyError) as e:
            if default is not None:
                return default
            print(f"ERROR: Config key '{section}.{key}' not a valid integer.")
            raise ValueError(f"Config key '{section}.{key}' not found or not int: {e}") from e

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """
        Retrieves a configuration value as a boolean.
        Accepts 'true', 'yes', '1', 'on' (case-insensitive) as True.
        
        Args:
            section (str): The section name.
            key (str): The key name.
            default (bool): Value to return if key is not found.
                                     
        Returns:
            bool: The configuration value.
        """
        try:
            return self._config.getboolean(section, key)
        except (ValueError, KeyError):
            return default

    def get_path(self, section: str, key: str) -> Path:
        """
        Retrieves a configuration value as an absolute Path object.
        Resolves the path relative to the project root.
        
        Args:
            section (str): The section name.
            key (str): The key name.
            
        Returns:
            Path: The absolute path.
        """
        path_str = self.get(section, key)
        return (self._project_root / path_str).resolve()

    def get_api_key(self, provider_key_name: str) -> str:
        """
        Securely retrieves an API key.
        
        It reads the *name* of the environment variable from [SECURITY] 
        section in config.ini, then fetches the *value* of that 
        environment variable from the system.
        
        Example:
            config.ini [SECURITY] -> gemini_api_key_env = "GEMINI_API_KEY"
            .env -> GEMINI_API_KEY="xyz123..."
            get_api_key('gemini_api_key_env') -> returns "xyz123..."
            
        Args:
            provider_key_name (str): The key in the [SECURITY] section that
                                     holds the name of the environment variable.
                                     (e.g., 'gemini_api_key_env')
        
        Returns:
            str: The API key.
            
        Raises:
            KeyError: If the API key is not found in the environment.
        """
        try:
            env_var_name = self.get('SECURITY', provider_key_name)
        except KeyError:
            msg = f"Config Error: No entry '{provider_key_name}' in [SECURITY]"
            print(msg)
            raise KeyError(msg)
            
        api_key = os.getenv(env_var_name)
        
        if not api_key:
            msg = (
                f"Security Error: Environment variable '{env_var_name}' is not set. "
                f"Please check your .env file or system environment."
            )
            print(msg)
            raise KeyError(msg)
            
        return api_key

# --- Global Instance ---
# Provides a single, easy-to-import instance for all other modules.
# Example usage in other files:
# from src.services.config_loader import config
# path = config.get_path('PATHS', 'data_dir')

config = ConfigLoader.get_instance()


# --- Demo Block ---
if __name__ == "__main__":
    print("\n--- 🚀 Iniciando Demo del ConfigLoader ---")
    
    # 1. Get singleton instance
    try:
        cfg = ConfigLoader.get_instance()
        print(f"Singleton instance created successfully.")
        
        # 2. Test basic 'get'
        mode = cfg.get('ENVIRONMENT', 'mode')
        print(f"ENVIRONMENT.mode: {mode} (Type: {type(mode)})")
        
        # 3. Test 'get_path'
        data_path = cfg.get_path('PATHS', 'data_dir')
        print(f"PATHS.data_dir: {data_path} (Type: {type(data_path)})")
        
        # 4. Test 'get_bool'
        use_gpu = cfg.get_bool('HARDWARE', 'use_gpu', default=False)
        print(f"HARDWARE.use_gpu: {use_gpu} (Type: {type(use_gpu)})")
        
        # 5. Test 'get_int'
        cpu_workers = cfg.get_int('HARDWARE', 'cpu_workers', default=1)
        print(f"HARDWARE.cpu_workers: {cpu_workers} (Type: {type(cpu_workers)})")
        
        # 6. Test 'get_api_key' (Secure retrieval)
        print("Testing API Key retrieval...")
        print("Set 'GEMINI_API_KEY=test_key_123' in your .env file to pass.")
        try:
            gemini_key = cfg.get_api_key('gemini_api_key_env')
            if gemini_key:
                print("✅ Successfully retrieved 'gemini_api_key_env'")
        except KeyError as e:
            print(f"⚠️  Warning (Expected if .env is not set): {e}")

        # 7. Test missing key
        print("\nTesting missing key (expected error)...")
        try:
            cfg.get('FAKE_SECTION', 'FAKE_KEY')
        except KeyError as e:
            print(f"✅ Successfully caught expected error: {e}")

    except (FileNotFoundError, KeyError) as e:
        print(f"\n--- ❌ Error en la Demo ---")
        print(f"Error: {e}")