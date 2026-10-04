"""Application-level LLM errors with secret-safe messaging."""

from dataclasses import dataclass


@dataclass(slots=True)
class LLMError(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return self.message


class LLMConfigurationError(LLMError):
    """Raised when Groq configuration is missing or invalid."""


class LLMProviderError(LLMError):
    """Raised when the Groq API returns an error."""


def sanitize_message(message: str, secret: str | None) -> str:
    if not secret:
        return message
    return message.replace(secret, "[REDACTED]")
