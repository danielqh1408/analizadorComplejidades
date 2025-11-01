"""
Global Pytest Fixtures

This file defines reusable fixtures that are available to all tests
in the test suite. It handles setup for configuration, services,
and mocking external dependencies.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

# --- Core Service Fixtures (Session-Scoped) ---

@pytest.fixture(scope="session")
def config():
    """
    Loads the global ConfigLoader instance once for the entire test session.
    Relies on the config_loader module to handle the singleton pattern.
    """
    from src.services.config_loader import config as global_config
    # Ensure config is loaded in 'testing' mode (if config.ini exists)
    try:
        if global_config.get('ENVIRONMENT', 'mode') != 'testing':
            print("\nWarning: Running tests but ENVIRONMENT.mode is not 'testing' in config.ini.")
    except KeyError:
        print("\nWarning: Could not read ENVIRONMENT.mode from config.ini.")
        
    return global_config

@pytest.fixture(scope="session")
def logger(config):
    """
    Provides the shared logger instance, configured by the global config.
    """
    from src.services.logger import get_logger
    # Get the logger named 'TestSuite'
    return get_logger("TestSuite")

@pytest.fixture(scope="function")
def metrics(config):
    """
    Provides a function-scoped MetricsLogger instance.
    This ensures that metrics are clean for each individual test.
    """
    from src.services.metrics import MetricsLogger
    # Create a new instance for the test
    test_metrics = MetricsLogger()
    # Ensure it's enabled for testing, overriding config if necessary
    test_metrics.enabled = True 
    yield test_metrics
    # Teardown: clear metrics after test
    test_metrics.metrics.clear()
    test_metrics.timers.clear()

# --- Mocking Fixtures ---

@pytest.fixture(scope="session", autouse=True)
def llm_mock(monkeypatch):
    """
    Session-scoped, auto-used fixture to mock the LLMAssistant.
    This replaces the real 'send_request' and 'close_session' methods
    on the class, so any instance created (like in src/main.py)
    will use these mocks.
    """
    
    # Define the mock async function for send_request
    async def mock_send_request(self, prompt: str, task_type: str = "general"):
        await asyncio.sleep(0.01) # Simulate network latency
        
        # Return a standardized mock response
        if "fail" in prompt:
            return {
                "status": "error",
                "provider": "mock_llm",
                "error": "MockedFailure",
                "details": "Prompt contained 'fail'"
            }
        
        return {
            "status": "ok",
            "provider": "mock_llm",
            "content": f"Mocked response for task '{task_type}': {prompt[:20]}...",
            "tokens": 42
        }

    # Define the mock async function for close_session
    async def mock_close_session(self):
        # This is an async no-op
        pass

    # Use monkeypatch to replace the methods on the class definition
    monkeypatch.setattr(
        "src.external.llm_assistant.LLMAssJessica.send_request",
        mock_send_request
    )
    monkeypatch.setattr(
        "src.external.llm_assistant.LLMAssistant.close_session",
        mock_close_session
    )
    
    logger.info("LLMAssistant has been mocked for the test session.")

# --- API Test Client ---

@pytest.fixture(scope="session")
def client(llm_mock):
    """
    Provides a session-scoped FastAPI TestClient.
    
    This fixture imports the 'app' from 'src/main.py'.
    The 'app' instance, upon creation, will import and create an
    instance of LLMAssistant, which will already be mocked by
    the 'llm_mock' fixture (due to dependency).
    """
    from src.main import app
    
    with TestClient(app) as test_client:
        yield test_client