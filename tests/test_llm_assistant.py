"""
Unit Tests for the LLM Assistant (src/external/llm_assistant.py)
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.external.llm_assistant import LLMAssistant

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_aiohttp_session():
    """Mocks the aiohttp.ClientSession."""
    with patch('aiohttp.ClientSession', autospec=True) as MockSession:
        # Mock the session instance
        mock_session_instance = MockSession.return_value
        
        # Mock the __aenter__ context manager
        mock_post_response = AsyncMock()
        mock_post_context = AsyncMock()
        mock_post_context.__aenter__.return_value = mock_post_response
        
        # Mock the post() method
        mock_session_instance.post = MagicMock(return_value=mock_post_context)
        
        yield mock_session_instance, mock_post_response

@pytest.fixture
def llm_assistant(config_loader_instance, metrics_logger_instance, monkeypatch):
    
    # 1. SIMULAMOS la función 'get_bool' del config
    # Forzamos que CUALQUIER llamada a get_bool("LLM", "mock_mode") 
    # devuelva True.
    def mock_get_bool(section, key, default=None):
        if section == "LLM" and key == "mock_mode":
            return True
        
        # Para cualquier otra llamada a get_bool, usamos el default
        return default if default is not None else False

    # 2. Aplicamos el parche (monkeypatch) a la instancia del config
    monkeypatch.setattr(
        config_loader_instance, 
        "get_bool", 
        mock_get_bool
    )

    # 3. Ahora, la creación del asistente SÍ funcionará
    # porque cuando llame a config.get_bool("LLM", "mock_mode"),
    # recibirá 'True' de nuestro mock.
    assistant = LLMAssistant()
    assistant.primary_provider = "gemini"
    return assistant

async def test_llm_send_gemini_request_success(llm_assistant, mocker):
    """Tests a successful request to Gemini."""
    
    # 1. Setup Mock Response (Gemini format)
    mock_response_json = {
        "candidates": [{
            "content": {"parts": [{"text": " This is O(n). "}]},
        }],
        "usageMetadata": {"totalTokenCount": 50}
    }
    
    # 2. Mock the internal _request_with_retry method
    mocker.patch.object(
        llm_assistant, 
        '_request_with_retry',
        new=AsyncMock(return_value=mock_response_json)
    )
    
    mock_metrics = mocker.patch('src.external.llm_assistant.metrics_logger')
    mock_metrics.end_timer.return_value = 0.123
    # 3. Call the public method
    prompt = "Analyze this code"
    response = await llm_assistant.send_request(prompt, "test_task")
    
    # 4. Assertions
    assert response['status'] == 'ok'
    assert response['provider'] == 'gemini' # From mock config
    assert response['content'] == 'This is O(n).' # Check stripping
    assert response['tokens'] == 50

    # Check that _request_with_retry was called correctly
    llm_assistant._request_with_retry.assert_called_once_with(
        'gemini',
        {'contents': [{'parts': [{'text': prompt}]}]}
    )

async def test_llm_request_http_error(llm_assistant, mocker):
    """Tests a non-retryable 400 Bad Request error."""
    
    # 1. Mock _request_with_retry to return a standard error dict
    error_response = {
        "status": "error", "provider": "gemini", "error_code": 400,
        "error": "HTTPError", "details": "Invalid request"
    }
    mocker.patch.object(
        llm_assistant, 
        '_request_with_retry',
        new=AsyncMock(return_value=error_response)
    )
    
    # 2. Call
    response = await llm_assistant.send_request("bad prompt", "error_test")
    
    # 3. Assert
    assert response['status'] == 'error'
    assert response['error_code'] == 400
    assert response['details'] == "Invalid request"
    llm_assistant._request_with_retry.assert_called_once() # No retries