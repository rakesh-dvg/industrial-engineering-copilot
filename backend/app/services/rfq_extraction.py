"""RFQ text extraction via Groq structured output."""

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.llm.base import TextGenerationRequest
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.groq_client import GroqLLMClient
from app.llm.prompts.rfq_extraction import RFQ_EXTRACTION_SYSTEM_PROMPT
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.rfq import RfqExtractionResult, RfqExtractResponse


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(),
    )


def extract_rfq_requirements(raw_text: str, llm_client: GroqLLMClient) -> RfqExtractResponse:
    stripped = raw_text.strip()
    if not stripped:
        raise _http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "RFQ_EMPTY",
            "RFQ text must not be empty.",
        )

    request = TextGenerationRequest(
        system_prompt=RFQ_EXTRACTION_SYSTEM_PROMPT,
        user_prompt=stripped,
        temperature=0,
        max_tokens=2048,
    )

    try:
        result = llm_client.generate_structured_model(
            request,
            RfqExtractionResult,
            schema_name="rfq_extraction",
            strict=True,
        )
    except LLMConfigurationError as exc:
        raise _http_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            exc.code,
            exc.message,
        ) from exc
    except LLMProviderError as exc:
        raise _http_error(
            status.HTTP_502_BAD_GATEWAY,
            exc.code,
            exc.message,
        ) from exc
    except ValidationError as exc:
        raise _http_error(
            status.HTTP_502_BAD_GATEWAY,
            "RFQ_EXTRACTION_SCHEMA_ERROR",
            "Groq structured output failed schema validation.",
        ) from exc

    return RfqExtractResponse.model_validate(result.model_dump())
