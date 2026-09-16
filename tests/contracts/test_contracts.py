"""Tests for strict public request contracts."""

import pytest
from pydantic import ValidationError

from tokennexus.contracts import (
    DecisionSummary,
    PublicError,
    PublicRequest,
    PublicResult,
    contract_schema,
    parse_public_request_json,
)
from tokennexus.ids import new_uuid7
from tokennexus.reasons import PublicStatus


def valid_request_data() -> dict[str, object]:
    """Return the smallest valid public request document."""
    return {
        "idempotency_key": "run-001",
        "application_id": "claims-assistant",
        "task": {"content": "Summarize the approved evidence."},
    }


def test_given_minimal_request_when_validated_then_defaults_materialize() -> None:
    # Arrange
    request_data = valid_request_data()

    # Act
    request = PublicRequest.model_validate(request_data)

    # Assert
    assert request.model_dump(mode="json") == {
        "schema_version": "1.0.0",
        "idempotency_key": "run-001",
        "application_id": "claims-assistant",
        "task": {
            "content": "Summarize the approved evidence.",
            "content_type": "text/plain",
            "mandatory_context": [],
        },
        "constraints": {
            "criticality": "standard",
            "minimum_quality": "4",
            "maximum_latency_ms": 10_000,
            "maximum_budget": {"currency": "USD", "amount": "0.02"},
            "maximum_input_tokens": 8_000,
            "maximum_output_tokens": 1_000,
            "maximum_tool_calls": 1,
        },
        "cache_directives": {
            "eligible": True,
            "freshness": "standard",
            "maximum_entry_age_ms": 3_600_000,
            "sensitivity": "non_sensitive",
        },
    }


def test_given_valid_request_when_mutated_then_model_is_frozen() -> None:
    # Arrange
    request = PublicRequest.model_validate(valid_request_data())

    # Act & Assert
    with pytest.raises(ValidationError, match="frozen"):
        request.application_id = "other-application"  # type: ignore[misc]


@pytest.mark.parametrize("amount", [0.02, "-0", "+1", "01", "1.0", "1e-2", "0.0000001"])
def test_given_noncanonical_budget_when_validated_then_request_is_rejected(amount: object) -> None:
    # Arrange
    request_data = valid_request_data()
    request_data["constraints"] = {"maximum_budget": {"amount": amount}}

    # Act & Assert
    with pytest.raises(ValidationError):
        PublicRequest.model_validate(request_data)


def test_given_unknown_field_when_validated_then_request_is_rejected() -> None:
    # Arrange
    request_data = valid_request_data()
    request_data["provider_endpoint"] = "https://provider.invalid"

    # Act & Assert
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PublicRequest.model_validate(request_data)


def test_given_wrong_scalar_type_when_validated_then_request_is_rejected() -> None:
    # Arrange
    request_data = valid_request_data()
    request_data["cache_directives"] = {"eligible": 1}

    # Act & Assert
    with pytest.raises(ValidationError):
        PublicRequest.model_validate(request_data)


def test_given_unsupported_schema_version_when_validated_then_request_is_rejected() -> None:
    # Arrange
    request_data = valid_request_data()
    request_data["schema_version"] = "2.0.0"

    # Act & Assert
    with pytest.raises(ValidationError):
        PublicRequest.model_validate(request_data)


def test_given_unsupported_schema_version_when_result_validated_then_rejected() -> None:
    # Arrange
    result_data = {
        "schema_version": "2.0.0",
        "request_id": new_uuid7(),
        "timestamp": "2026-09-16T12:34:56.789Z",
        "status": PublicStatus.IN_PROGRESS,
        "error": {
            "public_reason_code": "request.in_progress",
            "safe_message": "The matching request is already being processed.",
        },
        "decision_summary": {
            "end_to_end_latency_ms": 0,
            "public_reason_codes": ("request.in_progress",),
        },
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        PublicResult.model_validate(result_data)


def test_given_canonical_timestamp_when_result_validated_then_wire_value_is_preserved() -> None:
    # Arrange
    timestamp = "2026-09-16T12:34:56.789Z"

    # Act
    result = PublicResult(
        request_id=new_uuid7(),
        timestamp=timestamp,
        status=PublicStatus.IN_PROGRESS,
        error=PublicError(
            public_reason_code="request.in_progress",
            safe_message="The matching request is already being processed.",
        ),
        decision_summary=DecisionSummary(
            end_to_end_latency_ms=0,
            public_reason_codes=("request.in_progress",),
        ),
    )

    # Assert
    assert result.model_dump(mode="json")["timestamp"] == timestamp


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-09-16T12:34:56.789+00:00",
        "2026-09-16T12:34:56Z",
        "2026-09-16T12:34:56.789z",
        "2026-09-16 12:34:56.789Z",
        "2026-02-30T12:34:56.789Z",
        "2026-09-16T12:34:56.7890Z",
    ],
)
def test_given_noncanonical_timestamp_when_result_validated_then_rejected(timestamp: str) -> None:
    # Arrange
    result_data = {
        "request_id": new_uuid7(),
        "timestamp": timestamp,
        "status": PublicStatus.IN_PROGRESS,
        "error": {
            "public_reason_code": "request.in_progress",
            "safe_message": "The matching request is already being processed.",
        },
        "decision_summary": {
            "end_to_end_latency_ms": 0,
            "public_reason_codes": ("request.in_progress",),
        },
    }

    # Act & Assert
    with pytest.raises(ValidationError, match="timestamp"):
        PublicResult.model_validate(result_data)


def test_given_duplicate_json_member_when_parsed_then_request_is_rejected() -> None:
    # Arrange
    payload = '{"idempotency_key":"one","idempotency_key":"two"}'

    # Act & Assert
    with pytest.raises(ValueError, match="duplicate JSON member"):
        parse_public_request_json(payload)


def test_given_request_contract_when_schema_exported_then_dialect_and_id_are_stable() -> None:
    # Act
    schema = contract_schema(PublicRequest)

    # Assert
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "https://schemas.tokennexus.example/v1/PublicRequest.schema.json"