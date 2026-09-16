"""Tests for public reason-code validation."""

import pytest
from pydantic import ValidationError

from tokennexus.contracts import DecisionSummary, Output, PublicResult
from tokennexus.ids import new_uuid7
from tokennexus.reasons import PublicStatus


def test_given_unsorted_registered_reasons_when_validated_then_codes_are_sorted() -> None:
    # Act
    summary = DecisionSummary(
        end_to_end_latency_ms=10,
        public_reason_codes=("route.economical_eligible", "budget.within_limit"),
    )

    # Assert
    assert summary.public_reason_codes == ("budget.within_limit", "route.economical_eligible")


def test_given_unknown_reason_when_validated_then_serialization_fails_closed() -> None:
    # Act & Assert
    with pytest.raises(ValidationError, match="unknown public reason code"):
        DecisionSummary(
            end_to_end_latency_ms=10,
            public_reason_codes=("internal.provider.timeout",),
        )


def test_given_reason_incompatible_with_status_when_validated_then_result_is_rejected() -> None:
    # Arrange
    summary = DecisionSummary(
        end_to_end_latency_ms=10,
        public_reason_codes=("quality.threshold_unmet",),
    )

    # Act & Assert
    with pytest.raises(ValidationError, match="not valid for status completed"):
        PublicResult(
            request_id=new_uuid7(),
            timestamp="2026-09-16T12:34:56.789Z",
            status=PublicStatus.COMPLETED,
            output=Output(content="Done."),
            decision_summary=summary,
        )