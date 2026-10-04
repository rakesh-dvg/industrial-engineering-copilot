"""Provider-agnostic LLM interface.

The architecture allows a pluggable LLM layer. This repository implements Groq only.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass(slots=True)
class TextGenerationRequest:
    user_prompt: str
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    extra_messages: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class TextGenerationResponse:
    content: str
    model: str
    finish_reason: str | None = None


class LLMClient(ABC):
    """Abstract LLM client for extraction, explanation, and drafting only."""

    @abstractmethod
    def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate free-form text from a prompt."""

    @abstractmethod
    def generate_structured(
        self,
        request: TextGenerationRequest,
        *,
        schema_name: str,
        json_schema: dict[str, Any],
        strict: bool = True,
    ) -> dict[str, Any]:
        """Generate JSON matching a JSON Schema via provider structured outputs."""

    def generate_structured_model[T: BaseModel](
        self,
        request: TextGenerationRequest,
        response_model: type[T],
        *,
        schema_name: str | None = None,
        strict: bool = True,
    ) -> T:
        payload = self.generate_structured(
            request,
            schema_name=schema_name or response_model.__name__,
            json_schema=response_model.model_json_schema(),
            strict=strict,
        )
        return response_model.model_validate(payload)
