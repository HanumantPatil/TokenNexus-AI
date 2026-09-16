"""Tests for safe RFC 9457 problem detail mapping."""

import pytest
from pydantic import ValidationError

from tokennexus.contracts import PublicRequest
from tokennexus.problem_details import (
    domain_error_from_validation,
    problem_details_from_domain_error,
)


def test_given_multiple_invalid_fields_when_mapped_then_problem_is_safe_and_field_specific() -> (
    None
):
    # Arrange
    unsafe_value = "provider-secret-value"
    with pytest.raises(ValidationError) as captured:
        PublicRequest.model_validate(
            {
                "idempotency_key": "run-001",
                "application_id": "claims-assistant",
                "task": {"content": ""},
                "constraints": {"minimum_quality": unsafe_value},
            }
        )

    # Act
    problem = problem_details_from_domain_error(domain_error_from_validation(captured.value))
    serialized = problem.model_dump_json()

    # Assert
    assert problem.status == 400
    assert {item.path for item in problem.invalid_params} == {
        "/constraints/minimum_quality",
        "/task/content",
    }
    assert unsafe_value not in serialized
