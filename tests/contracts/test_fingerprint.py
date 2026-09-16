"""Tests for normalized RFC 8785 request fingerprints."""

from tokennexus.contracts import PublicRequest
from tokennexus.fingerprint import normalize_request, request_fingerprint
from tokennexus.ids import new_uuid7


def request_from_json(payload: str) -> PublicRequest:
    """Validate a public request fixture from JSON."""
    return PublicRequest.model_validate_json(payload)


def test_given_property_reordering_when_fingerprinted_then_identity_is_unchanged() -> None:
    # Arrange
    first = request_from_json(
        '{"idempotency_key":"first","application_id":"claims-assistant",'
        '"task":{"content":"Summarize evidence."}}'
    )
    second = request_from_json(
        '{"task":{"content":"Summarize evidence."},"application_id":"claims-assistant",'
        '"idempotency_key":"second"}'
    )

    # Act
    first_fingerprint = request_fingerprint(normalize_request(first, scope_id="tenant-a"))
    second_fingerprint = request_fingerprint(normalize_request(second, scope_id="tenant-a"))

    # Assert
    assert first_fingerprint == second_fingerprint


def test_given_semantic_constraint_change_when_fingerprinted_then_identity_changes() -> None:
    # Arrange
    first = request_from_json(
        '{"idempotency_key":"same","application_id":"claims-assistant",'
        '"task":{"content":"Summarize evidence."}}'
    )
    second = request_from_json(
        '{"idempotency_key":"same","application_id":"claims-assistant",'
        '"task":{"content":"Summarize evidence."},'
        '"constraints":{"maximum_output_tokens":2000}}'
    )

    # Act
    first_fingerprint = request_fingerprint(normalize_request(first, scope_id="tenant-a"))
    second_fingerprint = request_fingerprint(normalize_request(second, scope_id="tenant-a"))

    # Assert
    assert first_fingerprint != second_fingerprint


def test_given_generated_request_id_when_checked_then_it_is_uuid7() -> None:
    # Act
    request_id = new_uuid7()

    # Assert
    assert request_id.version == 7