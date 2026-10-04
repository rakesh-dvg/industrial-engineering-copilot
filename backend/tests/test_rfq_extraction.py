import os
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import Settings
from app.domain.spec_keys import SpecKey
from app.llm import get_llm_client
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.groq_client import GroqLLMClient
from app.main import create_app
from app.schemas.rfq import (
    AmbiguousRequirementNote,
    RequirementOperator,
    RequirementPriority,
    RfqExtractionResult,
    RfqExtractRequest,
    RfqExtractResponse,
    StructuredRequirement,
)
from app.services.rfq_extraction import extract_rfq_requirements

DEMO_ABC_RFQ = """Customer: ABC Manufacturing

Please quote 10 industrial Ethernet switches.

Requirements:
- 24 VDC power
- minimum 5 Ethernet ports
- DIN rail mounting
- Modbus TCP support
- operating temperature down to -20°C"""


def _demo_abc_extraction_result() -> RfqExtractionResult:
    return RfqExtractionResult(
        customer_name="ABC Manufacturing",
        quantity=10,
        requirements=[
            _requirement(
                SpecKey.INPUT_VOLTAGE,
                RequirementOperator.EQ,
                24,
                unit="V",
                source_text="24 VDC power",
            ),
            _requirement(
                SpecKey.ETHERNET_PORTS,
                RequirementOperator.GTE,
                5,
                source_text="minimum 5 Ethernet ports",
            ),
            _requirement(
                SpecKey.DIN_RAIL_MOUNTABLE,
                RequirementOperator.EQ,
                True,
                source_text="DIN rail mounting",
            ),
            _requirement(
                SpecKey.SUPPORTS_MODBUS_TCP,
                RequirementOperator.EQ,
                True,
                source_text="Modbus TCP support",
            ),
            _requirement(
                SpecKey.OPERATING_TEMP_MIN,
                RequirementOperator.LTE,
                -20,
                unit="°C",
                source_text="operating temperature down to -20°C",
            ),
        ],
        ambiguous_notes=[],
    )


def _assert_groq_compatible_rfq_schema() -> dict:
    """Validate RfqExtractionResult JSON schema invariants for Groq strict mode."""
    schema = RfqExtractionResult.model_json_schema()
    defs = schema.get("$defs", {})

    requirement_schema = defs["StructuredRequirement"]
    assert set(requirement_schema["required"]) == set(requirement_schema["properties"].keys())

    value_schema = requirement_schema["properties"]["value"]
    value_types = {
        option["type"]
        for option in value_schema["anyOf"]
        if isinstance(option, dict) and "type" in option
    }
    assert "integer" not in value_types
    assert "number" in value_types
    assert {"type": "null"} in value_schema["anyOf"]

    priority_schema = requirement_schema["properties"]["priority"]
    assert "anyOf" not in priority_schema
    assert priority_schema["type"] == "string"
    assert None in priority_schema["enum"]

    note_schema = defs["AmbiguousRequirementNote"]
    assert set(note_schema["required"]) == {"source_text", "description"}
    description_schema = note_schema["properties"]["description"]
    assert any(
        option.get("type") == "null"
        for option in description_schema.get("anyOf", [description_schema])
        if isinstance(option, dict)
    )

    object_schemas: list[tuple[str, dict]] = [("root", schema)]
    object_schemas.extend((name, definition) for name, definition in defs.items())

    incomplete_objects: list[str] = []
    for name, object_schema in object_schemas:
        if object_schema.get("type") != "object" or "properties" not in object_schema:
            continue
        properties = set(object_schema["properties"])
        required = set(object_schema.get("required") or [])
        if properties != required:
            incomplete_objects.append(name)

    assert incomplete_objects == []
    assert set(schema.get("required") or []) == set(schema["properties"].keys())

    return {
        "schema": schema,
        "root_required": sorted(schema.get("required") or []),
        "structured_requirement_required": sorted(requirement_schema["required"]),
        "incomplete_objects": incomplete_objects,
    }


@pytest.fixture
def mock_llm_client() -> MagicMock:
    return MagicMock(spec=GroqLLMClient)


@pytest_asyncio.fixture
async def rfq_client(mock_llm_client):
    from httpx import ASGITransport, AsyncClient

    app = create_app()
    app.dependency_overrides[get_llm_client] = lambda: mock_llm_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


def _requirement(
    spec_key: SpecKey,
    operator: RequirementOperator,
    value,
    *,
    unit: str | None = None,
    source_text: str | None = None,
) -> StructuredRequirement:
    return StructuredRequirement(
        spec_key=spec_key,
        operator=operator,
        value=value,
        unit=unit,
        source_text=source_text,
    )


def test_structured_requirement_applies_python_defaults_when_fields_omitted() -> None:
    req = StructuredRequirement(
        spec_key=SpecKey.ETHERNET_PORTS,
        operator=RequirementOperator.GTE,
        value=5,
    )
    assert req.required is True
    assert req.unit is None
    assert req.priority is None
    assert req.source_text is None


def test_structured_requirement_accepts_valid_fields() -> None:
    req = StructuredRequirement(
        spec_key=SpecKey.ETHERNET_PORTS,
        operator=RequirementOperator.GTE,
        value=5,
        source_text="minimum 5 Ethernet ports",
    )
    assert req.spec_key == SpecKey.ETHERNET_PORTS
    assert req.operator == RequirementOperator.GTE


def test_structured_requirement_rejects_invalid_operator() -> None:
    with pytest.raises(ValidationError):
        StructuredRequirement(
            spec_key=SpecKey.INPUT_VOLTAGE,
            operator="equals",  # type: ignore[arg-type]
            value=24,
        )


def test_rfq_extract_request_requires_non_empty_text() -> None:
    with pytest.raises(ValidationError):
        RfqExtractRequest(raw_text="")


def test_rfq_extract_response_quantity_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        RfqExtractResponse(quantity=0)


def test_extract_primary_ethernet_switch_rfq(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        customer_name="ABC Manufacturing",
        quantity=10,
        requirements=[
            _requirement(
                SpecKey.INPUT_VOLTAGE,
                RequirementOperator.EQ,
                24,
                unit="V",
                source_text="24 VDC power",
            ),
            _requirement(
                SpecKey.ETHERNET_PORTS,
                RequirementOperator.GTE,
                5,
                source_text="minimum 5 Ethernet ports",
            ),
            _requirement(
                SpecKey.DIN_RAIL_MOUNTABLE,
                RequirementOperator.EQ,
                True,
                source_text="DIN rail mounting",
            ),
            _requirement(
                SpecKey.SUPPORTS_MODBUS_TCP,
                RequirementOperator.EQ,
                True,
                source_text="Modbus TCP support",
            ),
            _requirement(
                SpecKey.OPERATING_TEMP_MIN,
                RequirementOperator.LTE,
                -20,
                unit="°C",
                source_text="operating temperature down to -20°C",
            ),
        ],
    )

    result = extract_rfq_requirements(
        "Customer: ABC Manufacturing\nPlease quote 10 industrial Ethernet switches.",
        mock_llm_client,
    )

    assert result.customer_name == "ABC Manufacturing"
    assert result.quantity == 10
    assert len(result.requirements) == 5
    ports = next(r for r in result.requirements if r.spec_key == SpecKey.ETHERNET_PORTS)
    assert ports.operator == RequirementOperator.GTE
    assert ports.value == 5


def test_extract_numeric_minimum(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        requirements=[
            _requirement(
                SpecKey.ETHERNET_PORTS,
                RequirementOperator.GTE,
                8,
                source_text="At least 8 Ethernet ports.",
            ),
        ],
    )

    result = extract_rfq_requirements("At least 8 Ethernet ports.", mock_llm_client)
    req = result.requirements[0]
    assert req.spec_key == SpecKey.ETHERNET_PORTS
    assert req.operator == RequirementOperator.GTE
    assert req.value == 8


def test_extract_exact_voltage(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        requirements=[
            _requirement(
                SpecKey.INPUT_VOLTAGE,
                RequirementOperator.EQ,
                24,
                unit="V",
                source_text="Supply voltage must be 24 VDC.",
            ),
        ],
    )

    result = extract_rfq_requirements("Supply voltage must be 24 VDC.", mock_llm_client)
    req = result.requirements[0]
    assert req.operator == RequirementOperator.EQ
    assert req.value == 24
    assert req.unit == "V"


def test_extract_temperature_requirement(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        requirements=[
            _requirement(
                SpecKey.OPERATING_TEMP_MIN,
                RequirementOperator.LTE,
                -20,
                unit="°C",
                source_text="The switch must operate down to -20°C.",
            ),
        ],
    )

    result = extract_rfq_requirements("The switch must operate down to -20°C.", mock_llm_client)
    req = result.requirements[0]
    assert req.spec_key == SpecKey.OPERATING_TEMP_MIN
    assert req.operator == RequirementOperator.LTE
    assert req.value == -20


def test_extract_boolean_requirement(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        requirements=[
            _requirement(
                SpecKey.DIN_RAIL_MOUNTABLE,
                RequirementOperator.EQ,
                True,
                source_text="DIN rail mounting is required.",
            ),
        ],
    )

    result = extract_rfq_requirements("DIN rail mounting is required.", mock_llm_client)
    req = result.requirements[0]
    assert req.value is True


def test_extract_quantity_only(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(quantity=25)

    result = extract_rfq_requirements("Please quote 25 units.", mock_llm_client)
    assert result.quantity == 25
    assert result.requirements == []


def test_extract_missing_values_not_invented(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        requirements=[
            _requirement(
                SpecKey.SUPPORTS_MODBUS_TCP,
                RequirementOperator.EQ,
                True,
                source_text="industrial Ethernet switch with Modbus TCP",
            ),
        ],
    )

    result = extract_rfq_requirements(
        "We need an industrial Ethernet switch with Modbus TCP.",
        mock_llm_client,
    )
    keys = {req.spec_key for req in result.requirements}
    assert SpecKey.SUPPORTS_MODBUS_TCP in keys
    assert SpecKey.ETHERNET_PORTS not in keys
    assert SpecKey.INPUT_VOLTAGE not in keys
    assert SpecKey.OPERATING_TEMP_MIN not in keys


def test_extract_ambiguous_language(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        requirements=[],
        ambiguous_notes=[
            AmbiguousRequirementNote(
                source_text="We need a rugged industrial Ethernet switch.",
                description="Ruggedness is not mapped to a specific specification.",
            ),
        ],
    )

    result = extract_rfq_requirements(
        "We need a rugged industrial Ethernet switch.",
        mock_llm_client,
    )
    assert result.requirements == []
    assert len(result.ambiguous_notes) == 1
    assert "rugged" in result.ambiguous_notes[0].source_text.lower()


def test_extract_empty_text_raises(mock_llm_client: MagicMock) -> None:
    with pytest.raises(HTTPException) as exc_info:
        extract_rfq_requirements("   ", mock_llm_client)

    assert exc_info.value.status_code == 422
    mock_llm_client.generate_structured_model.assert_not_called()


def test_extract_groq_configuration_error(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.side_effect = LLMConfigurationError(
        code="GROQ_NOT_CONFIGURED",
        message="GROQ_API_KEY is not configured.",
    )

    with pytest.raises(HTTPException) as exc_info:
        extract_rfq_requirements("Need 10 switches.", mock_llm_client)

    assert exc_info.value.status_code == 503


def test_extract_groq_provider_error(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.side_effect = LLMProviderError(
        code="GROQ_API_ERROR",
        message="Groq API request failed.",
    )

    with pytest.raises(HTTPException) as exc_info:
        extract_rfq_requirements("Need 10 switches.", mock_llm_client)

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_api_extract_rfq_success(rfq_client, mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(
        quantity=10,
        requirements=[
            _requirement(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5),
        ],
    )

    response = await rfq_client.post(
        "/api/v1/rfqs/extract",
        json={"raw_text": "Please quote 10 switches with minimum 5 ports."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["quantity"] == 10
    assert payload["requirements"][0]["spec_key"] == "ethernet_ports"
    assert payload["requirements"][0]["operator"] == "gte"


@pytest.mark.asyncio
async def test_api_extract_empty_rfq_returns_422(rfq_client, mock_llm_client: MagicMock) -> None:
    response = await rfq_client.post("/api/v1/rfqs/extract", json={"raw_text": "   "})
    assert response.status_code == 422
    mock_llm_client.generate_structured_model.assert_not_called()


@pytest.mark.asyncio
async def test_api_extract_malformed_request(rfq_client) -> None:
    response = await rfq_client.post("/api/v1/rfqs/extract", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_extract_groq_failure(rfq_client, mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.side_effect = LLMProviderError(
        code="GROQ_API_ERROR",
        message="Provider unavailable.",
    )

    response = await rfq_client.post(
        "/api/v1/rfqs/extract",
        json={"raw_text": "Need 10 switches."},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "GROQ_API_ERROR"


def test_rfq_extraction_schema_is_groq_compatible_for_nested_objects() -> None:
    report = _assert_groq_compatible_rfq_schema()
    assert report["root_required"] == [
        "ambiguous_notes",
        "customer_name",
        "customer_reference",
        "quantity",
        "requirements",
        "title",
    ]
    assert report["structured_requirement_required"] == [
        "operator",
        "priority",
        "required",
        "source_text",
        "spec_key",
        "unit",
        "value",
    ]


def test_rfq_extraction_result_applies_python_defaults_when_fields_omitted() -> None:
    result = RfqExtractionResult(quantity=10)
    assert result.customer_name is None
    assert result.customer_reference is None
    assert result.title is None
    assert result.quantity == 10
    assert result.requirements == []
    assert result.ambiguous_notes == []


@pytest.mark.parametrize(
    ("raw_priority", "expected"),
    [
        (None, None),
        ("must_have", RequirementPriority.MUST_HAVE),
        ("preferred", RequirementPriority.PREFERRED),
        (RequirementPriority.MUST_HAVE, RequirementPriority.MUST_HAVE),
    ],
)
def test_structured_requirement_priority_accepts_representative_values(
    raw_priority: object,
    expected: RequirementPriority | None,
) -> None:
    requirement = StructuredRequirement(
        spec_key=SpecKey.INPUT_VOLTAGE,
        operator=RequirementOperator.EQ,
        value=24,
        priority=raw_priority,  # type: ignore[arg-type]
    )
    assert requirement.priority == expected


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (24, 24),
        (5, 5),
        (True, True),
        ("panel_mount", "panel_mount"),
        (None, None),
    ],
)
def test_structured_requirement_value_accepts_representative_types(
    raw_value: object,
    expected: object,
) -> None:
    requirement = StructuredRequirement(
        spec_key=SpecKey.INPUT_VOLTAGE,
        operator=RequirementOperator.EQ,
        value=raw_value,  # type: ignore[arg-type]
    )
    assert requirement.value == expected


@pytest.mark.asyncio
async def test_extract_rfq_endpoint_locally_with_mocked_groq(
    rfq_client,
    mock_llm_client: MagicMock,
) -> None:
    schema_report = _assert_groq_compatible_rfq_schema()
    mocked_result = _demo_abc_extraction_result()
    mock_llm_client.generate_structured_model.return_value = mocked_result

    response = await rfq_client.post(
        "/api/v1/rfqs/extract",
        json={"raw_text": DEMO_ABC_RFQ},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["customer_name"] == "ABC Manufacturing"
    assert payload["quantity"] == 10
    assert len(payload["requirements"]) == 5

    by_key = {item["spec_key"]: item for item in payload["requirements"]}
    assert by_key["input_voltage"]["operator"] == "eq"
    assert by_key["input_voltage"]["value"] == 24
    assert by_key["input_voltage"]["unit"] == "V"
    assert by_key["ethernet_ports"]["operator"] == "gte"
    assert by_key["ethernet_ports"]["value"] == 5
    assert by_key["din_rail_mountable"]["value"] is True
    assert by_key["supports_modbus_tcp"]["value"] is True
    assert by_key["operating_temp_min"]["operator"] == "lte"
    assert by_key["operating_temp_min"]["value"] == -20
    assert by_key["operating_temp_min"]["unit"] == "°C"
    assert payload["ambiguous_notes"] == []

    mock_llm_client.generate_structured_model.assert_called_once()
    args, kwargs = mock_llm_client.generate_structured_model.call_args
    assert args[1] is RfqExtractionResult
    assert kwargs["schema_name"] == "rfq_extraction"
    assert kwargs.get("strict") is True
    assert schema_report["incomplete_objects"] == []


def test_generate_structured_model_used_for_extraction(mock_llm_client: MagicMock) -> None:
    mock_llm_client.generate_structured_model.return_value = RfqExtractionResult(quantity=1)
    extract_rfq_requirements("Quote 1 switch.", mock_llm_client)

    mock_llm_client.generate_structured_model.assert_called_once()
    args, kwargs = mock_llm_client.generate_structured_model.call_args
    assert args[1] is RfqExtractionResult
    assert kwargs["schema_name"] == "rfq_extraction"


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_GROQ_INTEGRATION_TESTS", "false").lower() != "true",
    reason="Set RUN_GROQ_INTEGRATION_TESTS=true to run live Groq RFQ extraction tests.",
)
def test_live_groq_rfq_extraction() -> None:
    settings = Settings()
    client = GroqLLMClient(settings)
    raw_text = (
        "Customer: ABC Manufacturing\n\n"
        "Please quote 10 industrial Ethernet switches.\n\n"
        "Requirements:\n"
        "- 24 VDC power\n"
        "- minimum 5 Ethernet ports\n"
        "- DIN rail mounting\n"
        "- Modbus TCP support\n"
        "- operating temperature down to -20°C"
    )

    result = extract_rfq_requirements(raw_text, client)

    assert result.quantity == 10
    keys = {req.spec_key for req in result.requirements}
    assert SpecKey.ETHERNET_PORTS in keys
    ports = next(r for r in result.requirements if r.spec_key == SpecKey.ETHERNET_PORTS)
    assert ports.operator == RequirementOperator.GTE
    assert ports.value == 5
