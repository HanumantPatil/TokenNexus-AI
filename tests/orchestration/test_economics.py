"""Acceptance tests for atomic reservations and policy administration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from tokennexus.contracts import (
    Money,
    PolicyChangeCommand,
    PolicySnapshot,
    PublicRequest,
    RequestConstraints,
    ReservationRequest,
    Task,
)
from tokennexus.economics import (
    InMemoryBudgetLedger,
    InMemoryPolicyStore,
    PolicyAdministrationService,
)
from tokennexus.fingerprint import normalize_request
from tokennexus.policy import PolicyEvaluator, pilot_policy


class DeterministicClock:
    """Return one stable administration timestamp."""

    def now(self) -> float:
        return 100.0

    def utc_now(self) -> datetime:
        return datetime(2026, 9, 16, 12, 34, 56, 789000, tzinfo=UTC)


class DeterministicIds:
    """Generate repeatable UUIDv7 identifiers."""

    def __init__(self) -> None:
        self._ordinal = 0

    def new(self) -> UUID:
        self._ordinal += 1
        return UUID(f"01890f3e-0000-7000-8000-{self._ordinal:012x}")


def reservation(ordinal: int = 1, **updates: object) -> ReservationRequest:
    """Build one deterministic worst-case reservation request."""
    values: dict[str, object] = {
        "reservation_id": UUID(f"01890f3e-0000-7000-8000-{ordinal:012x}"),
        "request_id": UUID("01890f3e-0000-7000-8000-000000000100"),
        "operation_key": f"operation-{ordinal}",
        "dispatch_ordinal": ordinal,
        "pricing_version": "pilot-pricing-1",
        "estimated_cost": Money(amount="1"),
        "input_tokens": 10,
        "output_tokens": 5,
        "duration_ms": 20,
        "tool_calls": 1,
    }
    values.update(updates)
    return ReservationRequest.model_validate(values)


@pytest.mark.parametrize(
    "reservation_request",
    [
        reservation(estimated_cost=Money(amount="2")),
        reservation(input_tokens=11),
        reservation(output_tokens=6),
        reservation(duration_ms=21),
        reservation(tool_calls=2),
    ],
)
def test_given_any_exceeded_dimension_when_reserving_then_nothing_is_reserved(
    reservation_request: ReservationRequest,
) -> None:
    # Arrange
    ledger = InMemoryBudgetLedger(
        maximum_cost="1",
        maximum_input_tokens=10,
        maximum_output_tokens=5,
        maximum_duration_ms=20,
        maximum_tool_calls=1,
    )

    # Act
    receipt = ledger.reserve(reservation_request)

    # Assert
    assert receipt is None
    assert ledger.reservations == ()


def test_given_one_remaining_allowance_when_two_threads_reserve_then_only_one_succeeds() -> None:
    # Arrange
    ledger = InMemoryBudgetLedger(maximum_cost="1")
    requests = (reservation(1), reservation(2))

    # Act
    with ThreadPoolExecutor(max_workers=2) as executor:
        receipts = tuple(executor.map(ledger.reserve, requests))

    # Assert
    assert sum(receipt is not None for receipt in receipts) == 1
    assert len(ledger.reservations) == 1


def test_given_unauthorized_actor_when_updating_then_attempt_is_denied_and_safely_audited() -> None:
    # Arrange
    initial = pilot_policy()
    store = InMemoryPolicyStore(initial)
    service = PolicyAdministrationService(
        store=store,
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )
    command = PolicyChangeCommand(
        expected_active_version=initial.policy_version,
        proposed_policy=initial.model_copy(update={"policy_version": "pilot-2"}),
        confirmed=True,
    )

    # Act
    applied = service.update(
        command,
        actor_id="operator@example.test",
        actor_roles=frozenset({"viewer"}),
    )

    # Assert
    assert applied is False
    assert store.active() == initial
    assert store.audit_events[0].public_reason_code == "policy.unauthorized"
    assert store.audit_events[0].actor_id_hash != "operator@example.test"


def test_given_prior_policy_when_rollback_is_confirmed_then_new_version_clones_source() -> None:
    # Arrange
    initial = pilot_policy()
    store = InMemoryPolicyStore(initial)
    service = PolicyAdministrationService(
        store=store,
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )
    updated = initial.model_copy(
        update={"policy_version": "pilot-2", "pricing_version": "pilot-pricing-2"}
    )
    service.update(
        PolicyChangeCommand(
            expected_active_version="pilot-1",
            proposed_policy=updated,
            confirmed=True,
        ),
        actor_id="administrator",
        actor_roles=frozenset({"policy_admin"}),
    )

    # Act
    applied = service.rollback(
        expected_active_version="pilot-2",
        source_version="pilot-1",
        new_version="pilot-3",
        confirmed=True,
        actor_id="administrator",
        actor_roles=frozenset({"policy_admin"}),
    )

    # Assert
    assert applied is True
    assert tuple(snapshot.policy_version for snapshot in store.versions) == (
        "pilot-1",
        "pilot-2",
        "pilot-3",
    )
    assert store.active().pricing_version == initial.pricing_version
    assert store.audit_events[-1].source_version == "pilot-1"


def test_given_unconfirmed_update_when_submitted_then_it_is_denied_and_audited() -> None:
    # Arrange
    initial = pilot_policy()
    store = InMemoryPolicyStore(initial)
    service = PolicyAdministrationService(
        store=store,
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )

    # Act
    applied = service.update(
        PolicyChangeCommand(
            expected_active_version="pilot-1",
            proposed_policy=initial.model_copy(update={"policy_version": "pilot-2"}),
            confirmed=False,
        ),
        actor_id="administrator",
        actor_roles=frozenset({"policy_admin"}),
    )

    # Assert
    assert applied is False
    assert store.active() is initial
    assert store.audit_events[-1].public_reason_code == "policy.confirmation_required"


def test_given_stale_update_when_submitted_then_active_policy_is_unchanged() -> None:
    # Arrange
    initial = pilot_policy()
    store = InMemoryPolicyStore(initial)
    service = PolicyAdministrationService(
        store=store,
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )

    # Act
    applied = service.update(
        PolicyChangeCommand(
            expected_active_version="stale-version",
            proposed_policy=initial.model_copy(update={"policy_version": "pilot-2"}),
            confirmed=True,
        ),
        actor_id="administrator",
        actor_roles=frozenset({"policy_admin"}),
    )

    # Assert
    assert applied is False
    assert store.active() is initial
    assert store.audit_events[-1].outcome == "conflict"
    assert store.audit_events[-1].public_reason_code == "policy.version_conflict"


def test_given_invalid_policy_shape_when_constructed_then_contract_rejects_it() -> None:
    # Act and assert
    with pytest.raises(ValidationError, match="economical and capable"):
        PolicySnapshot(
            policy_version="pilot-invalid",
            pricing_version="pilot-pricing-invalid",
            models=(pilot_policy().models[0],),
        )


@pytest.mark.parametrize("source_version", ["missing-version", "pilot-1"])
def test_given_invalid_rollback_source_when_submitted_then_it_is_denied(
    source_version: str,
) -> None:
    # Arrange
    initial = pilot_policy()
    store = InMemoryPolicyStore(initial)
    service = PolicyAdministrationService(
        store=store,
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )

    # Act
    applied = service.rollback(
        expected_active_version="pilot-1",
        source_version=source_version,
        new_version="pilot-2",
        confirmed=True,
        actor_id="administrator",
        actor_roles=frozenset({"policy_admin"}),
    )

    # Assert
    assert applied is False
    assert store.active() is initial
    assert store.audit_events[-1].outcome == "invalid"
    assert store.audit_events[-1].public_reason_code == "policy.invalid_change"


def test_given_confirmed_update_when_applied_then_new_snapshot_changes_routing_only() -> None:
    # Arrange
    initial = pilot_policy()
    store = InMemoryPolicyStore(initial)
    service = PolicyAdministrationService(
        store=store,
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )
    economical, capable = initial.models
    updated = initial.model_copy(
        update={
            "policy_version": "pilot-2",
            "models": (
                economical.model_copy(
                    update={
                        "supported_criticalities": ("standard", "high", "critical"),
                        "maximum_supported_quality": "5",
                    }
                ),
                capable.model_copy(update={"enabled": False}),
            ),
        }
    )
    request = PublicRequest(
        idempotency_key="updated-routing",
        application_id="routing-corpus",
        task=Task(content="Evaluate updated routing."),
        constraints=RequestConstraints(
            criticality="high",
            maximum_budget=Money(amount="1"),
        ),
    )
    normalized = normalize_request(
        request,
        scope_id="tenant-a",
        request_id=UUID("01890f3e-0000-7000-8000-000000000001"),
    )

    # Act
    applied = service.update(
        PolicyChangeCommand(
            expected_active_version="pilot-1",
            proposed_policy=updated,
            confirmed=True,
        ),
        actor_id="administrator",
        actor_roles=frozenset({"policy_admin"}),
    )
    original_route = PolicyEvaluator().evaluate(initial, normalized)
    updated_route = PolicyEvaluator().evaluate(store.active(), normalized)

    # Assert
    assert applied is True
    assert original_route.selected_model_alias == "capable"
    assert updated_route.selected_model_alias == "economical"
    assert initial.policy_version == "pilot-1"
    assert tuple(snapshot.policy_version for snapshot in store.versions) == (
        "pilot-1",
        "pilot-2",
    )
    with pytest.raises((ValidationError, FrozenInstanceError)):
        initial.policy_version = "mutated"  # type: ignore[misc]