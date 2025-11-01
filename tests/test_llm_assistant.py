"""
Unit Tests for the LLM Assistant (src/external/llm_assistant.py)
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

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
def llm_assistant(config_loader_instance, metrics_logger_instance):
    """Provides an LLMAssistant instance for testing."""
    from src.external.llm_assistant import LLMAssistant
    # It will be configured using the mock config
    assistant = LLMAssistant()
    # We patch its internal session to our mock
    assistant.session = AsyncMock()
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

async def test_llm_send_openai_request_success(llm_assistant, mocker):
    """Tests a successful request to OpenAI."""
    
    # 1. Change provider
    llm_assistant.primary_provider = 'openai'
    
    # 2. Setup Mock Response (OpenAI format)
    mock_response_json = {
        "choices": [{
            "message": {"content": " This is O(n^2). "}
        }],
        "usage": {"total_tokens": 75}
    }
    
    mocker.patch.object(
        llm_assistant, 
        '_request_with_retry',
        new=AsyncMock(return_value=mock_response_json)
    )
    
    # 3. Call public method
    prompt = "Analyze this nested loop"
    response = await llm_assistant.send_request(prompt, "test_task_openai")
    
    # 4. Assertions
    assert response['status'] == 'ok'
    assert response['provider'] == 'openai'
    assert response['content'] == 'This is O(n^2).'
    assert response['tokens'] == 75
    
    # Check payload
    expected_payload = {
        "model": "gpt-test-model", # From mock config
        "messages": [{"role": "user", "content": prompt}]
    }
    llm_assistant._request_with_retry.assert_called_once_with('openai', expected_payload)

async def test_llm_request_retry_on_timeout(llm_assistant, mocker):
    """Tests the retry logic on a connection error."""
    
    # 1. Mock _request_with_retry to simulate failures
    mock_request = AsyncMock(side_effect=[
        asyncio.TimeoutError("First attempt timed out"), # 1st call fails
        {"candidates": [{"content": {"parts": [{"text": "OK"}]}}], "usageMetadata": {"totalTokenCount": 10}} # 2nd call succeeds
    ])
    mocker.patch.object(llm_assistant, '_request_with_retry', new=mock_request)
    mocker.patch('asyncio.sleep', new=AsyncMock()) # Patch sleep
    
    # 2. Call
    response = await llm_assistant.send_request("prompt", "retry_test")
    
    # 3. Assert
    assert response['status'] == 'ok'
    assert response['content'] == 'OK'
    assert mock_request.call_count == 2 # Called twice
    asyncio.sleep.assert_called_once() # Slept once

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