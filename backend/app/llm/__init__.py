"""LLM gateway — Groq-only implementation.

Groq is used for extraction, explanation, and drafting only.
Deterministic engineering validation remains outside this layer.
"""

from app.config import Settings, get_settings
from app.llm.base import LLMClient, TextGenerationRequest, TextGenerationResponse
from app.llm.config import (
    GroqConfigurationStatus,
    GroqSettings,
    get_groq_settings,
    require_groq_configuration,
    validate_groq_configuration,
)
from app.llm.errors import LLMConfigurationError, LLMError, LLMProviderError
from app.llm.groq_client import GroqLLMClient


def get_llm_client(settings: Settings | None = None) -> GroqLLMClient:
    """Return the project's sole LLM client (Groq)."""
    return GroqLLMClient(settings or get_settings())


__all__ = [
    "GroqConfigurationStatus",
    "GroqLLMClient",
    "GroqSettings",
    "LLMClient",
    "LLMConfigurationError",
    "LLMError",
    "LLMProviderError",
    "TextGenerationRequest",
    "TextGenerationResponse",
    "get_groq_settings",
    "get_llm_client",
    "require_groq_configuration",
    "validate_groq_configuration",
]
