import json
import os
from unittest.mock import MagicMock

import pytest
from groq import APIStatusError
from pydantic import BaseModel, ConfigDict

from app.config import Settings
from app.llm.base import TextGenerationRequest
from app.llm.config import (
    get_groq_settings,
    normalize_groq_base_url,
    require_groq_configuration,
    validate_groq_configuration,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.groq_client import GroqLLMClient


class ExampleRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[str]


@pytest.fixture
def groq_settings() -> Settings:
    return Settings(
        groq_api_key="test-groq-key",
        groq_model="openai/gpt-oss-120b",
        groq_base_url="https://api.groq.com/openai/v1",
    )


@pytest.fixture
def mock_groq_client() -> MagicMock:
    client = MagicMock()
    completion = MagicMock()
    completion.model = "openai/gpt-oss-120b"
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = "Generated explanation."
    completion.choices[0].finish_reason = "stop"
    client.chat.completions.create.return_value = completion
    return client


def test_default_groq_model_and_base_url() -> None:
    settings = Settings()
    assert settings.groq_model == "openai/gpt-oss-120b"
    assert settings.groq_base_url == "https://api.groq.com"


def test_missing_api_key_reported_by_validation() -> None:
    settings = Settings(groq_api_key=None)
    status = validate_groq_configuration(settings)

    assert status.api_key_configured is False
    assert "GROQ_API_KEY is not configured." in status.issues
    assert status.is_ready is False


def test_require_groq_configuration_raises_when_api_key_missing() -> None:
    settings = Settings(groq_api_key=None)

    with pytest.raises(LLMConfigurationError) as exc_info:
        require_groq_configuration(settings)

    assert exc_info.value.code == "GROQ_NOT_CONFIGURED"
    assert "GROQ_API_KEY" in exc_info.value.message


def test_get_groq_settings_strips_api_key(groq_settings: Settings) -> None:
    settings = groq_settings.model_copy(update={"groq_api_key": "  test-groq-key  "})
    resolved = get_groq_settings(settings)

    assert resolved.api_key == "test-groq-key"
    assert resolved.model == "openai/gpt-oss-120b"
    assert resolved.base_url == "https://api.groq.com"


def test_normalize_groq_base_url_strips_duplicate_openai_suffix() -> None:
    assert normalize_groq_base_url("https://api.groq.com/openai/v1") == "https://api.groq.com"
    assert normalize_groq_base_url("https://api.groq.com/openai/v1/") == "https://api.groq.com"
    assert normalize_groq_base_url("https://api.groq.com") == "https://api.groq.com"


def test_generate_text_request_is_constructed_correctly(
    groq_settings: Settings,
    mock_groq_client: MagicMock,
) -> None:
    client = GroqLLMClient(groq_settings, client=mock_groq_client)
    request = TextGenerationRequest(
        system_prompt="You explain engineering trade-offs.",
        user_prompt="Summarize DIN rail mounting.",
        temperature=0.2,
        max_tokens=128,
    )

    response = client.generate_text(request)

    mock_groq_client.chat.completions.create.assert_called_once_with(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You explain engineering trade-offs."},
            {"role": "user", "content": "Summarize DIN rail mounting."},
        ],
        temperature=0.2,
        max_tokens=128,
    )
    assert response.content == "Generated explanation."
    assert response.model == "openai/gpt-oss-120b"


def test_generate_structured_request_uses_json_schema(
    groq_settings: Settings,
    mock_groq_client: MagicMock,
) -> None:
    structured_payload = {"requirements": ["output_voltage equals 24 VDC"]}
    mock_groq_client.chat.completions.create.return_value.choices[
        0
    ].message.content = json.dumps(structured_payload)

    client = GroqLLMClient(groq_settings, client=mock_groq_client)
    request = TextGenerationRequest(user_prompt="Extract requirements from the RFQ.")
    schema = ExampleRequirements.model_json_schema()

    result = client.generate_structured(
        request,
        schema_name="example_requirements",
        json_schema=schema,
        strict=True,
    )

    kwargs = mock_groq_client.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"]["type"] == "json_schema"
    assert kwargs["response_format"]["json_schema"]["name"] == "example_requirements"
    assert kwargs["response_format"]["json_schema"]["strict"] is True
    assert kwargs["response_format"]["json_schema"]["schema"] == schema
    assert result == structured_payload


def test_generate_structured_model_validates_payload(
    groq_settings: Settings,
    mock_groq_client: MagicMock,
) -> None:
    mock_groq_client.chat.completions.create.return_value.choices[
        0
    ].message.content = json.dumps({"requirements": ["din rail mounting"]})

    client = GroqLLMClient(groq_settings, client=mock_groq_client)
    request = TextGenerationRequest(user_prompt="Extract requirements.")

    parsed = client.generate_structured_model(request, ExampleRequirements)

    assert parsed.requirements == ["din rail mounting"]


def test_api_errors_are_translated_without_exposing_secret(
    groq_settings: Settings,
    mock_groq_client: MagicMock,
) -> None:
    mock_groq_client.chat.completions.create.side_effect = APIStatusError(
        "Invalid API Key test-groq-key",
        response=MagicMock(status_code=401),
        body={"error": {"message": "Invalid API Key test-groq-key"}},
    )

    client = GroqLLMClient(groq_settings, client=mock_groq_client)
    request = TextGenerationRequest(user_prompt="Hello")

    with pytest.raises(LLMProviderError) as exc_info:
        client.generate_text(request)

    assert exc_info.value.code == "GROQ_API_ERROR"
    assert "test-groq-key" not in exc_info.value.message
    assert "[REDACTED]" in exc_info.value.message


def test_generate_text_requires_configuration_when_client_not_injected() -> None:
    settings = Settings(groq_api_key=None)
    client = GroqLLMClient(settings)
    request = TextGenerationRequest(user_prompt="Hello")

    with pytest.raises(LLMConfigurationError):
        client.generate_text(request)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_GROQ_INTEGRATION_TESTS", "false").lower() != "true",
    reason="Set RUN_GROQ_INTEGRATION_TESTS=true to run live Groq integration tests.",
)
def test_live_groq_text_generation() -> None:
    settings = Settings()
    status = validate_groq_configuration(settings)
    if not status.is_ready:
        pytest.skip("Groq is not configured for live integration testing.")

    client = GroqLLMClient(settings)
    response = client.generate_text(
        TextGenerationRequest(
            user_prompt="Reply with the single word READY.",
            temperature=0,
            max_tokens=16,
        )
    )

    assert "READY" in response.content.upper()
