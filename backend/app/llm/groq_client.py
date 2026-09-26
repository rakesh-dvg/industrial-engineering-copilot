"""Groq LLM client — the sole LLM provider for this project."""

import json
from typing import Any

from groq import APIConnectionError, APIStatusError, Groq, RateLimitError

from app.config import Settings
from app.llm.base import LLMClient, TextGenerationRequest, TextGenerationResponse
from app.llm.config import get_groq_settings, require_groq_configuration
from app.llm.errors import LLMConfigurationError, LLMProviderError, sanitize_message


class GroqLLMClient(LLMClient):
    """Groq-backed LLM client for extraction, explanation, and drafting."""

    def __init__(self, settings: Settings, *, client: Groq | None = None) -> None:
        self._settings = settings
        self._groq_settings = get_groq_settings(settings)
        self._client = client

    def _resolve_client(self) -> Groq:
        if self._client is not None:
            return self._client

        groq_settings = require_groq_configuration(self._settings)
        return Groq(api_key=groq_settings.api_key, base_url=groq_settings.base_url)

    def _build_messages(self, request: TextGenerationRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend(request.extra_messages)
        messages.append({"role": "user", "content": request.user_prompt})
        return messages

    def _build_completion_kwargs(self, request: TextGenerationRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._groq_settings.model,
            "messages": self._build_messages(request),
        }
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        return kwargs

    def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        try:
            client = self._resolve_client()
            response = client.chat.completions.create(**self._build_completion_kwargs(request))
        except LLMConfigurationError:
            raise
        except (APIStatusError, APIConnectionError, RateLimitError) as exc:
            raise self._translate_provider_error(exc) from exc
        except Exception as exc:  # noqa: BLE001 - normalize unexpected provider failures
            raise self._translate_provider_error(exc) from exc

        choice = response.choices[0]
        return TextGenerationResponse(
            content=choice.message.content or "",
            model=response.model,
            finish_reason=choice.finish_reason,
        )

    def generate_structured(
        self,
        request: TextGenerationRequest,
        *,
        schema_name: str,
        json_schema: dict[str, Any],
        strict: bool = True,
    ) -> dict[str, Any]:
        completion_kwargs = self._build_completion_kwargs(request)
        completion_kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": strict,
                "schema": json_schema,
            },
        }

        try:
            client = self._resolve_client()
            response = client.chat.completions.create(**completion_kwargs)
        except LLMConfigurationError:
            raise
        except (APIStatusError, APIConnectionError, RateLimitError) as exc:
            raise self._translate_provider_error(exc) from exc
        except Exception as exc:  # noqa: BLE001 - normalize unexpected provider failures
            raise self._translate_provider_error(exc) from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMProviderError(
                code="GROQ_EMPTY_STRUCTURED_RESPONSE",
                message="Groq returned an empty structured response.",
            )

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                code="GROQ_INVALID_STRUCTURED_RESPONSE",
                message="Groq structured response was not valid JSON.",
            ) from exc

    def _translate_provider_error(self, exc: Exception) -> LLMProviderError:
        api_key = self._groq_settings.api_key
        message = sanitize_message(str(exc), api_key)
        status_code = getattr(exc, "status_code", None)
        code = "GROQ_API_ERROR"
        if isinstance(exc, RateLimitError):
            code = "GROQ_RATE_LIMIT"
        elif isinstance(exc, APIConnectionError):
            code = "GROQ_CONNECTION_ERROR"

        if status_code is not None:
            message = f"Groq API request failed with status {status_code}: {message}"
        else:
            message = f"Groq API request failed: {message}"

        return LLMProviderError(code=code, message=message)
