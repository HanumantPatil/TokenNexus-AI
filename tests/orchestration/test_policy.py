"""Acceptance tests for governed economics policy."""

from dataclasses import dataclass
from uuid import UUID

import pytest

from tokennexus.contracts import PublicRequest, RequestConstraints, Task
from tokennexus.fingerprint import normalize_request
from tokennexus.policy import PolicyEvaluator, pilot_policy
from tokennexus.reasons import PUBLIC_REASON_REGISTRY


@dataclass(frozen=True, slots=True)
class RoutingCase:
    """One labeled request and its expected stable model alias."""

    label: str
    criticality: str
    minimum_quality: str
    maximum_latency_ms: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    expected_alias: str


ROUTING_CASES = (
    RoutingCase("routine-default", "standard", "4", 10_000, 8_000, 1_000, "economical"),
    RoutingCase("routine-quality-low", "standard", "1", 10_000, 8_000, 1_000, "economical"),
    RoutingCase("routine-quality-boundary", "standard", "4", 10_000, 8_000, 1_000, "economical"),
    RoutingCase("routine-latency-boundary", "standard", "4", 100, 8_000, 1_000, "economical"),
    RoutingCase("routine-input-low", "standard", "4", 10_000, 1, 1_000, "economical"),
    RoutingCase("routine-input-high", "standard", "4", 10_000, 20_000, 1_000, "economical"),
    RoutingCase("routine-output-low", "standard", "4", 10_000, 8_000, 1, "economical"),
    RoutingCase("routine-output-high", "standard", "4", 10_000, 8_000, 5_000, "economical"),
    RoutingCase("routine-latency-high", "standard", "3", 300_000, 4_000, 500, "economical"),
    RoutingCase("routine-small", "standard", "2", 500, 100, 100, "economical"),
    RoutingCase("complex-default", "high", "4", 10_000, 8_000, 1_000, "capable"),
    RoutingCase("complex-quality-low", "high", "1", 10_000, 8_000, 1_000, "capable"),
    RoutingCase("complex-quality-high", "high", "5", 10_000, 8_000, 1_000, "capable"),
    RoutingCase("complex-latency-boundary", "high", "4", 300, 8_000, 1_000, "capable"),
    RoutingCase("complex-input-low", "high", "4", 10_000, 1, 1_000, "capable"),
    RoutingCase("complex-input-high", "high", "4", 10_000, 20_000, 1_000, "capable"),
    RoutingCase("complex-output-low", "high", "4", 10_000, 8_000, 1, "capable"),
    RoutingCase("complex-output-high", "high", "4", 10_000, 8_000, 5_000, "capable"),
    RoutingCase("complex-latency-high", "high", "3", 300_000, 4_000, 500, "capable"),
    RoutingCase("complex-small", "high", "2", 500, 100, 100, "capable"),
    RoutingCase("critical-default", "critical", "4", 10_000, 8_000, 1_000, "capable"),
    RoutingCase("critical-quality-low", "critical", "1", 10_000, 8_000, 1_000, "capable"),
    RoutingCase("critical-quality-high", "critical", "5", 10_000, 8_000, 1_000, "capable"),
    RoutingCase("critical-latency-boundary", "critical", "4", 300, 8_000, 1_000, "capable"),
    RoutingCase("critical-input-low", "critical", "4", 10_000, 1, 1_000, "capable"),
    RoutingCase("critical-input-high", "critical", "4", 10_000, 20_000, 1_000, "capable"),
    RoutingCase("critical-output-low", "critical", "4", 10_000, 8_000, 1, "capable"),
    RoutingCase("critical-output-high", "critical", "4", 10_000, 8_000, 5_000, "capable"),
    RoutingCase("critical-latency-high", "critical", "3", 300_000, 4_000, 500, "capable"),
    RoutingCase("critical-small", "critical", "2", 500, 100, 100, "capable"),
)


def test_given_critical_request_when_policy_evaluates_then_capable_path_is_selected() -> None:
    # Arrange
    request = PublicRequest(
        idempotency_key="critical-route",
        application_id="claims-assistant",
        task=Task(content="Review the approved evidence."),
        constraints=RequestConstraints(criticality="critical", maximum_budget={"amount": "1"}),
    )
    normalized = normalize_request(
        request,
        scope_id="tenant-a",
        request_id=UUID("01890f3e-0000-7000-8000-000000000001"),
    )

    # Act
    decision = PolicyEvaluator().evaluate(pilot_policy(), normalized)

    # Assert
    assert decision.selected_model_alias == "capable"
    assert decision.budget_action == "allow"
    assert decision.policy_version == "pilot-1"
    assert decision.pricing_version == "pilot-pricing-1"
    assert decision.selected_estimate is not None
    assert {gate.gate for gate in decision.eligibility_gates} == {
        "availability",
        "budget",
        "governance",
        "latency",
        "quality",
    }
    assert decision.public_reason_codes == (
        "budget.within_limit",
        "route.capable_required",
    )


@pytest.mark.parametrize("case", ROUTING_CASES, ids=lambda case: case.label)
def test_given_frozen_corpus_when_policy_evaluates_then_expected_route_is_stable(
    case: RoutingCase,
) -> None:
    # Arrange
    request = PublicRequest(
        idempotency_key=f"route-{case.label}",
        application_id="routing-corpus",
        task=Task(content="Evaluate governed routing."),
        constraints=RequestConstraints(
            criticality=case.criticality,
            minimum_quality=case.minimum_quality,
            maximum_latency_ms=case.maximum_latency_ms,
            maximum_budget={"amount": "1"},
            maximum_input_tokens=case.maximum_input_tokens,
            maximum_output_tokens=case.maximum_output_tokens,
        ),
    )
    normalized = normalize_request(
        request,
        scope_id="tenant-a",
        request_id=UUID("01890f3e-0000-7000-8000-000000000001"),
    )
    evaluator = PolicyEvaluator()
    snapshot = pilot_policy()

    # Act
    first = evaluator.evaluate(snapshot, normalized)
    second = evaluator.evaluate(snapshot, normalized)

    # Assert
    assert first == second
    assert first.selected_model_alias == case.expected_alias
    assert first.policy_version == "pilot-1"
    assert first.pricing_version == "pilot-pricing-1"
    assert first.selected_estimate is not None
    assert first.budget_action == "allow"
    assert first.public_reason_codes
    assert all(code in PUBLIC_REASON_REGISTRY for code in first.public_reason_codes)
    assert {gate.gate for gate in first.eligibility_gates} == {
        "availability",
        "budget",
        "governance",
        "latency",
        "quality",
    }
