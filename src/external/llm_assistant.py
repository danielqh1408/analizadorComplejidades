"""
LLM Assistant Wrapper (External Service)

This module provides a unified, asynchronous interface to communicate with
external LLM providers (Gemini).

It handles:
- Asynchronous requests using aiohttp.
- Dynamic provider selection based on config.ini.
- Secure API key management (via ConfigLoader).
- Request/Response (de)serialization for each provider.
- Error handling with exponential backoff retries.
- Integration with project-wide logging (Logger) and metrics (MetricsLogger).
"""

import os
import aiohttp
import asyncio
import json
import time
from typing import Dict, Any, Optional


# --- Project-Specific Imports ---
try:
    from src.services.config_loader import config
    from src.services.logger import get_logger
    from src.services.metrics import metrics_logger
except ImportError:
    print("FATAL ERROR: LLMAssistant failed to import base services.")
    # Fallback for standalone demo
    import logging
    get_logger = lambda name: logging.getLogger(name)
    class DummyConfig:
        def get(self, *args, default=None): return default
        def get_int(self, *args, default=0): return default
        def get_bool(self, *args, default=False): return default
        def get_api_key(self, env_var): return os.getenv(env_var, "DUMMY_KEY_NOT_SET")
    config = DummyConfig()
    class DummyMetrics:
        def start_timer(self, label): pass
        def end_timer(self, label): return 0
        def log(self, *args): pass
    metrics_logger = DummyMetrics()
# --- End Project-Specific Imports ---

logger = get_logger(__name__)

class LLMAssistant:
    """
    Asynchronous client for handling requests to LLM APIs.
    
    This class manages a persistent aiohttp.ClientSession and encapsulates
    all logic for building payloads, parsing responses, and handling
    errors for different providers.
    """
    
    def __init__(self):

        """
        Initializes the LLM Assistant, loading configuration from the
        global 'config' instance.
        """
        logger.info("Initializing LLMAssistant...")
        
        if config.get_bool("LLM", "mock_mode", default=False):
            self.mock_mode = True
            self.mock_response = {"text": "Simulated response for test."}
            logger.info("✅ LLMAssistant inicializado en modo simulado (mock_mode=True).")
            return

        # --- Load General Config ---
        self.primary_provider = config.get('LLM', 'primary_provider', default='gemini')
        self.timeout = config.get_int('API', 'timeout', default=30)
        self.max_retries = config.get_int('API', 'max_retries', default=3)
        self.api_keys: Dict[str, str] = {}
        
        # --- Load Gemini Config ---
        try:
            self.gemini_model = config.get('LLM', 'gemini_model')
            self.gemini_url = config.get('LLM', 'gemini_api_base_url')
            gemini_key_env = config.get('SECURITY', 'gemini_api_key_env')
            self.api_keys['gemini'] = config.get_api_key(gemini_key_env)
        except KeyError as e:
            logger.warning(f"Gemini config incomplete. Provider disabled. Missing: {e}")
            self.api_keys['gemini'] = None
        # --- Initialize HTTP Session ---
        # (aiohttp==3.10.5)
        # Create the session in the constructor. It will be managed
        # by the application lifecycle (e.g., FastAPI startup/shutdown).
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        logger.info(f"LLMAssistant initialized. Primary provider: {self.primary_provider}")

    async def close_session(self):
        """
        Gracefully closes the aiohttp ClientSession.
        Should be called on application shutdown.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("LLMAssistant session closed.")

    def _build_headers(self, provider: str) -> Dict[str, str]:
        """Builds the required HTTP headers for the specified provider."""
        if provider == 'gemini':
            # Gemini API key is passed as a URL parameter, not a header
            return {'Content-Type': 'application/json'}
        raise ValueError(f"Unknown provider: {provider}")

    def _build_payload(self, prompt: str, provider: str) -> Dict[str, Any]:
        """Builds the provider-specific JSON payload."""
        if provider == 'gemini':
            # Payload for Gemini (v1beta)
            return {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            }
        raise ValueError(f"Unknown provider: {provider}")

    def _parse_response(self, data: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        Parses the JSON response from the provider into a standardized dict.
        Extracts content and token count.
        """
        try:
            if provider == 'gemini':
                # Parse Gemini response [cite: ArquitecturaF.png - Extractor]
                content = data['candidates'][0]['content']['parts'][0]['text']
                # Note: 'usageMetadata' may not always be present
                tokens = data.get('usageMetadata', {}).get('totalTokenCount', 0)     
            else:
                raise ValueError(f"Unknown provider: {provider}")

            return {
                "status": "ok",
                "provider": provider,
                "content": content.strip(),
                "tokens": tokens
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse LLM response structure: {e}", exc_info=True)
            logger.debug(f"Raw data dump: {data}")
            return self._handle_error(500, "InvalidResponseStructure", provider, str(e))

    def _handle_error(self, code: int, error: str, provider: str, details: str = "") -> Dict[str, Any]:
        """Returns a standardized error dictionary."""
        return {
            "status": "error",
            "provider": provider,
            "error_code": code,
            "error": error,
            "details": details
        }

    async def _request_with_retry(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to perform the HTTP request with exponential backoff.
        
        Handles transient errors (timeouts, connection issues) and HTTP errors.
        """
        headers = self._build_headers(provider)
        url = ""
        params = {}
        
        if provider == 'gemini':
            if not self.api_keys['gemini']:
                return self._handle_error(401, "NotConfigured", provider, "Gemini API key is missing.")
            url = f"{self.gemini_url}/{self.gemini_model}:generateContent"
            params = {'key': self.api_keys['gemini']}
        else:
            return self._handle_error(400, "UnknownProvider", provider, f"Provider '{provider}' not supported.")

        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.post(url, headers=headers, params=params, json=payload) as response:
                    # Raise HTTPError for 4xx/5xx responses
                    response.raise_for_status() 
                    return await response.json()
            
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                # Transient errors (retryable)
                logger.warning(f"LLM request failed (Attempt {attempt+1}/{self.max_retries+1}): {e}")
                if attempt == self.max_retries:
                    logger.error(f"Max retries exceeded for provider {provider}.")
                    return self._handle_error(504, "TimeoutOrConnectionError", provider, str(e))
                
                # Exponential backoff: 1s, 2s, 4s...
                sleep_time = (2 ** attempt)
                await asyncio.sleep(sleep_time)
                
            except aiohttp.ClientResponseError as e:
                # Non-transient HTTP errors (e.g., 400, 401, 404, 500)
                logger.error(f"LLM request HTTP error: {e.status} {e.message}", exc_info=True)
                return self._handle_error(e.status, "HTTPError", provider, e.message)
            
            except Exception as e:
                # Other unexpected errors
                logger.critical(f"Unexpected error during LLM request: {e}", exc_info=True)
                return self._handle_error(500, "InternalError", provider, str(e))
        
        return self._handle_error(500, "MaxRetriesExceeded", provider)


    async def send_request(self, prompt: str, task_type: str = "general") -> Dict[str, Any]:
        """
        Sends a prompt to the primary LLM provider asynchronously.
        
        This method manages the full lifecycle:
        1. Metrics timer start
        2. Payload construction
        3. Asynchronous request with retries
        4. Response parsing
        5. Metrics timer end and logging
        
        Args:
            prompt (str): The text prompt to send to the LLM.
            task_type (str): A label for the task (e.g., "validation", "translation")
                             used for metrics.
                             
        Returns:
            Dict[str, Any]: A standardized response dictionary.
                            On success: {"status": "ok", "content": "...", "tokens": ...}
                            On error:   {"status": "error", "error": "..."}
        """
        metric_label = f"llm_request.{self.primary_provider}.{task_type}"
        metrics_logger.start_timer(metric_label)
        logger.info(f"Sending request to {self.primary_provider} (Task: {task_type})...")

        try:
            # 1. Build provider-specific payload
            payload = self._build_payload(prompt, self.primary_provider)
            
            # 2. Perform request with retry logic
            raw_response = await self._request_with_retry(self.primary_provider, payload)

            # 3. Check for errors during the request
            if raw_response.get("status") == "error":
                metrics_logger.end_timer(metric_label) # End timer on error
                return raw_response # Already a standardized error dict
            
            # 4. Parse the successful response
            parsed_response = self._parse_response(raw_response, self.primary_provider)
            
            # 5. Log metrics and finalize
            elapsed_time = metrics_logger.end_timer(metric_label)
            if parsed_response['status'] == 'ok':
                tokens = parsed_response.get('tokens', 0)
                logger.info(f"LLM response received in {elapsed_time:.3f}s. Tokens: {tokens}")
                metrics_logger.log(f"llm_tokens.{self.primary_provider}", tokens, "tokens")
            
            return parsed_response

        except Exception as e:
            # Catch-all for safety
            logger.critical(f"Critical failure in send_request: {e}", exc_info=True)
            elapsed_time = metrics_logger.end_timer(metric_label)
            return self._handle_error(500, "UnhandledException", self.primary_provider, str(e))


# --- Demo Block ---
# Run with: python src/external/llm_assistant.py
# Requires a .env file in the project root (ANALIZADORCOMPLEJIDADES/)
# with a valid GEMINI_API_KEY.

async def main_demo():
    """
    Demonstrates how to use the LLMAssistant.
    """
    print("--- 🚀 Iniciando Demo del LLMAssistant ---")
    
    # We must load the real config for the demo
    from src.services.config_loader import ConfigLoader
    global config
    config = ConfigLoader.get_instance()

    assistant = LLMAssistant()
    
    test_prompt = "Explain what 'Big O notation' is in 3 sentences."
    
    try:
        response = await assistant.send_request(test_prompt, task_type="demo_test")
        
        print("\n--- ✅ Response Received ---")
        print(json.dumps(response, indent=2))
        
        if response['status'] == 'ok':
            print(f"\nContent: {response['content']}")
            
    except Exception as e:
        print(f"\n--- ❌ Error during demo ---")
        print(e)
        
    finally:
        # Always close the session
        await assistant.close_session()

if __name__ == "__main__":
    # Check for .env file
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not set. Demo will likely fail.")
        print("Please create a .env file in the project root.")
    
    try:
        asyncio.run(main_demo())
    except Exception as e:
        print(f"Demo failed: {e}")