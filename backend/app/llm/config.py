"""Groq-specific LLM configuration and lightweight validation."""

from dataclasses import dataclass

from app.config import Settings
from app.llm.errors import LLMConfigurationError


@dataclass(frozen=True, slots=True)
class GroqSettings:
    api_key: str | None
    model: str
    base_url: str

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())


@dataclass(frozen=True, slots=True)
class GroqConfigurationStatus:
    api_key_configured: bool
    model_configured: bool
    base_url_configured: bool
    client_instantiable: bool
    model: str
    base_url: str
    issues: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return (
            self.api_key_configured
            and self.model_configured
            and self.base_url_configured
            and self.client_instantiable
            and not self.issues
        )


def get_groq_settings(settings: Settings) -> GroqSettings:
    api_key = settings.groq_api_key.strip() if settings.groq_api_key else None
    return GroqSettings(
        api_key=api_key,
        model=settings.groq_model,
        base_url=settings.groq_base_url,
    )


def validate_groq_configuration(settings: Settings) -> GroqConfigurationStatus:
    groq_settings = get_groq_settings(settings)
    issues: list[str] = []

    if not groq_settings.api_key_configured:
        issues.append("GROQ_API_KEY is not configured.")

    if not groq_settings.model.strip():
        issues.append("GROQ_MODEL is not configured.")

    if not groq_settings.base_url.strip():
        issues.append("GROQ_BASE_URL is not configured.")

    client_instantiable = False
    if groq_settings.api_key_configured and groq_settings.base_url.strip():
        try:
            from groq import Groq

            Groq(api_key=groq_settings.api_key, base_url=groq_settings.base_url)
            client_instantiable = True
        except Exception as exc:  # noqa: BLE001 - surface safe configuration issue
            issues.append(f"Groq client could not be instantiated: {exc}")

    return GroqConfigurationStatus(
        api_key_configured=groq_settings.api_key_configured,
        model_configured=bool(groq_settings.model.strip()),
        base_url_configured=bool(groq_settings.base_url.strip()),
        client_instantiable=client_instantiable,
        model=groq_settings.model,
        base_url=groq_settings.base_url,
        issues=tuple(issues),
    )


def require_groq_configuration(settings: Settings) -> GroqSettings:
    status = validate_groq_configuration(settings)
    if not status.is_ready:
        raise LLMConfigurationError(
            code="GROQ_NOT_CONFIGURED",
            message="; ".join(status.issues) or "Groq is not configured.",
        )
    return get_groq_settings(settings)
