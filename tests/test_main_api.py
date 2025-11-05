"""
Integration Tests for the FastAPI Orchestrator (src/main.py)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture
def mock_deterministic_analysis():
    """Mocks the CPU-bound analysis function."""
    
    # This is the function run in `asyncio.to_thread`
    with patch('src.main.run_deterministic_analysis') as mock_run:
        mock_run.return_value = {
            "status": "ok",
            "token_count": 25,
            "complexity": {
                "O": "O(n)", "Omega": "Ω(n)", "Theta": "Θ(n)", "raw": "n"
            }
        }
        yield mock_run

@pytest.fixture
def mock_llm_validation():
    """Mocks the LLM assistant's send_request method."""
    
    # We must patch the *instance* used by the app
    with patch('src.main.llm_assistant.send_request', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {
            "status": "ok",
            "provider": "gemini",
            "content": "The analysis appears correct.",
            "tokens": 50
        }
        yield mock_send

def test_api_analyze_pseudocode(client, mock_deterministic_analysis, mock_llm_validation, mocker):
    """
    Tests the /api/analyze endpoint with type: pseudocode.
    Checks that deterministic and LLM tasks run.
    """

    mock_metrics = mocker.patch('src.main.metrics_logger')
    mock_metrics.end_timer.return_value = 123.45

    payload = {
        "type": "pseudocode",
        "content": "FOR i 🡨 1 TO n DO x 🡨 1 END"
    }
    
    response = client.post("/api/analyze", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that both mocks were called
    mock_deterministic_analysis.assert_called_once_with(payload['content'])
    mock_llm_validation.assert_called_once()
    
    # Check deterministic results in output
    assert data['status'] == 'ok'
    assert data['complexity']['O'] == "O(n)"
    assert data['token_count'] == 25
    
    # Check LLM results in output
    assert data['llm_validation']['status'] == 'ok'
    assert data['llm_validation']['content'] == "The analysis appears correct."
    assert data['execution_time_ms'] > 0
    assert data['execution_time_ms'] == 123.45

def test_api_analyze_natural_language(client, mock_deterministic_analysis, mock_llm_validation, mocker):
    """
    Tests the /api/analyze endpoint with type: natural.
    Checks that LLM is called twice (translate + validate).
    """

    mock_metrics = mocker.patch('src.main.metrics_logger')
    mock_metrics.end_timer.return_value = 123.45
    
    # 1. Setup mock to return translation first, then validation
    translated_code = "FOR i 🡨 1 TO n DO x 🡨 1 END"
    mock_llm_validation.side_effect = [
        # 1st call (translation)
        {"status": "ok", "provider": "gemini", "content": translated_code, "tokens": 30},
        # 2nd call (validation)
        {"status": "ok", "provider": "gemini", "content": "Validated O(n).", "tokens": 20},
    ]
    
    payload = {
        "type": "natural",
        "content": "a simple loop from 1 to n"
    }
    
    # 2. Call API
    response = client.post("/api/analyze", json=payload)
    
    # 3. Assertions
    assert response.status_code == 200
    data = response.json()
    
    assert data['status'] == 'ok'
    assert data['type'] == 'natural'
    assert data['analyzed_code'] == translated_code
    
    # Check that deterministic analysis was called with the *translated* code
    mock_deterministic_analysis.assert_called_once_with(translated_code)
    assert data['complexity']['O'] == "O(n)"
    
    # Check that LLM was called twice
    assert mock_llm_validation.call_count == 2
    assert data['llm_validation']['content'] == "Validated O(n)."

def test_api_analyze_bad_input(client):
    """Tests for 422 Unprocessable Entity on bad payload."""
    
    # Missing 'content'
    response = client.post("/api/analyze", json={"type": "pseudocode"})
    assert response.status_code == 422
    
    # Invalid 'type'
    response = client.post("/api/analyze", json={"type": "python", "content": "..."})
    assert response.status_code == 422