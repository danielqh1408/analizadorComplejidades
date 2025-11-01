"""
External Services Sub-package

This package contains wrappers for all external API communications,
primarily the LLM Assistant.
"""

try:
    from .llm_assistant import LLMAssistant
except ImportError:
    print("Warning: LLMAssistant could not be imported.")

# Define what 'from src.external import *' will import
__all__ = [
    "LLMAssistant"
]