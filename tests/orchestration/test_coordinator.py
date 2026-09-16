"""Focused tests for governed orchestration and scoped idempotency."""

from collections import deque
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from uuid import UUID

import pytest

from tokennexus.contracts import (
    ModelAlias,
    Money,
    NormalizedRequest,
    Output,
    PublicRequest,
    QualitySummary,
    Task,
    Usage,
)
from tokennexus.coordinator import Coordinator
from tokennexus.fingerprint import normalize_request, request_fingerprint
from tokennexus.ids import new_uuid7
from tokennexus.journal import InMemoryJournal
from tokennexus.ports import ModelInvocation, ModelOutcome, ModelOutcomeStatus
from tokennexus.reasons import PublicStatus
from tokennexus.state import RunPhase, RunState, StateTransitionError


class FakeClock:
    """Return scripted monotonic values and retain the final value."""

    def __init__(self, *values: float) -> None:
        self._values = deque(values or (0.0,))
        self._last = self._values[-1]

    def now(self) -> float:
        if self._values:
            self._last = self._values.popleft()
        return self._last

    def utc_now(self) -> datetime:
        return datetime(2026, 9, 16, 12, 34, 56, 789000, tzinfo=UTC)


class FakeIds:
    """Generate valid UUIDv7 values for deterministic dependency injection."""

    def new(self) -> UUID:
        return new_uuid7()


class FakeCancellation:
    """Cancel on and after a configured coordinator check."""

    def __init__(self, cancel_on_call: int | None = None) -> None:
        self.cancel_on_call = cancel_on_call
        self.calls = 0

    def is_cancelled(self, request_id: UUID) -> bool:
        del request_id
        self.calls += 1
        return self.cancel_on_call is not None and self.calls >= self.cancel_on_call


class FakeBudget:
    """Record reservation order and return scripted admission decisions."""

    def __init__(self, *decisions: bool, events: list[str] | None = None) -> None:
        self._decisions = deque(decisions)
        self.calls: list[tuple[UUID, str, Money]] = []
        self.events = events if events is not None else []

    def reserve(
        self,
        *,
        request_id: UUID,
        operation_key: str,
        estimated_cost: Money,
    ) -> bool:
        self.events.append("reserve")
        self.calls.append((request_id, operation_key, estimated_cost))
        return self._decisions.popleft() if self._decisions else True


class FakeModel:
    """Return scripted model facts with one record per physical invocation."""

    def __init__(self, outcomes: list[ModelOutcome], events: list[str] | None = None) -> None:
        self._outcomes = deque(outcomes)
        self.calls: list[ModelInvocation] = []
        self.events = events if events is not None else []

    def estimate_cost(self, request: NormalizedRequest, model_alias: ModelAlias) -> Money:
        del request, model_alias
        return Money(amount="0.01")

    def invoke(self, invocation: ModelInvocation) -> ModelOutcome:
        self.events.append("model")
        self.calls.append(invocation)
        return self._outcomes.popleft()


class FakeQuality:
    """Return scripted quality facts with one record per evaluation."""

    def __init__(self, outcomes: list[QualitySummary], events: list[str] | None = None) -> None:
        self._outcomes = deque(outcomes)
        self.calls: list[tuple[NormalizedRequest, Output]] = []
        self.events = events if events is not None else []

    def estimate_cost(self, request: NormalizedRequest, output: Output) -> Money:
        del request, output
        return Money(amount="0")

    def evaluate(self, request: NormalizedRequest, output: Output) -> QualitySummary:
        self.events.append("quality")
        self.calls.append((request, output))
        return self._outcomes.popleft()


def successful_outcome(content: str = "Approved answer.") -> ModelOutcome:
    """Build one successful provider-neutral model outcome."""
    return ModelOutcome(
        status=ModelOutcomeStatus.SUCCEEDED,
        output=Output(content=content),
        usage=Usage(
            input_tokens=10,
            output_tokens=5,
            estimated_cost=Money(amount="0.01"),
            provider_latency_ms=20,
        ),
    )


def request(*, content: str = "Summarize the evidence.") -> PublicRequest:
    """Build a minimal orchestration request."""
    return PublicRequest(
        idempotency_key="request-001",
        application_id="claims-assistant",
        task=Task(content=content),
    )


def coordinator(
    *,
    journal: InMemoryJournal,
    budget: FakeBudget,
    model: FakeModel,
    quality: FakeQuality,
    cancellation: FakeCancellation | None = None,
    clock: FakeClock | None = None,
) -> Coordinator:
    """Build a coordinator with inspectable synchronous dependencies."""
    return Coordinator(
        journal=journal,
        budget=budget,
        model=model,
        quality=quality,
        cancellation=cancellation or FakeCancellation(),
        clock=clock or FakeClock(),
        ids=FakeIds(),
    )


def test_given_routine_request_when_executed_then_economical_result_completes_once() -> None:
    # Arrange
    events: list[str] = []
    journal = InMemoryJournal()
    budget = FakeBudget(events=events)
    model = FakeModel([successful_outcome()], events=events)
    quality = FakeQuality([QualitySummary(status="passed", score="5")], events=events)
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)

    # Act
    result = service.execute(request(), scope_id="tenant-a")

    # Assert
    assert result.status == PublicStatus.COMPLETED
    assert result.timestamp == "2026-09-16T12:34:56.789Z"
    assert result.decision_summary.model_alias == "economical"
    assert [call.model_alias for call in model.calls] == ["economical"]
    assert len(quality.calls) == 1
    assert events == ["reserve", "model", "reserve", "quality"]


def test_given_terminal_request_when_replayed_then_exact_result_has_no_new_effects() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    model = FakeModel([successful_outcome()])
    quality = FakeQuality([QualitySummary(status="passed", score="5")])
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)
    original = service.execute(request(), scope_id="tenant-a")

    # Act
    replay = service.execute(request(), scope_id="tenant-a")

    # Assert
    assert original.decision_summary.usage == Usage(
        input_tokens=10,
        output_tokens=5,
        estimated_cost=Money(amount="0.01"),
        provider_latency_ms=20,
    )
    assert replay is original
    assert len(model.calls) == 1
    assert len(quality.calls) == 1
    assert len(budget.calls) == 2


def test_given_active_replay_when_executed_then_in_progress_has_original_id_and_no_effects(
) -> None:
    # Arrange
    journal = InMemoryJournal()
    original_request_id = new_uuid7()
    public_request = request()
    normalized = normalize_request(
        public_request,
        scope_id="tenant-a",
        request_id=original_request_id,
    )
    fingerprint = request_fingerprint(normalized)
    initial = RunState(request=normalized, fingerprint=fingerprint, deadline=10.0)
    journal.claim(
        scope_id="tenant-a",
        idempotency_key=public_request.idempotency_key,
        fingerprint=fingerprint,
        initial_state=initial,
    )
    budget = FakeBudget()
    model = FakeModel([])
    quality = FakeQuality([])
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)

    # Act
    result = service.execute(public_request, scope_id="tenant-a")
    stored = journal.read(scope_id="tenant-a", idempotency_key=public_request.idempotency_key)

    # Assert
    assert result.status == PublicStatus.IN_PROGRESS
    assert result.request_id == original_request_id
    assert result.decision_summary.usage is None
    assert len(budget.calls) == 0
    assert len(model.calls) == 0
    assert len(quality.calls) == 0
    assert stored == initial


def test_given_reused_key_when_fingerprint_changes_then_conflict_precedes_effects() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    model = FakeModel([successful_outcome()])
    quality = FakeQuality([QualitySummary(status="passed", score="5")])
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)
    service.execute(request(), scope_id="tenant-a")

    # Act
    conflict = service.execute(request(content="Different task."), scope_id="tenant-a")

    # Assert
    assert conflict.status == PublicStatus.CONFLICT
    assert len(model.calls) == 1
    assert len(quality.calls) == 1
    assert len(budget.calls) == 2


def test_given_cancelled_request_when_executed_then_no_paid_effect_occurs() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    model = FakeModel([])
    quality = FakeQuality([])
    service = coordinator(
        journal=journal,
        budget=budget,
        model=model,
        quality=quality,
        cancellation=FakeCancellation(cancel_on_call=1),
    )

    # Act
    result = service.execute(request(), scope_id="tenant-a")

    # Assert
    assert result.status == PublicStatus.CANCELLED
    assert len(budget.calls) == 0
    assert len(model.calls) == 0
    assert len(quality.calls) == 0


def test_given_expired_deadline_when_executed_then_times_out_before_reservation() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    model = FakeModel([])
    quality = FakeQuality([])
    service = coordinator(
        journal=journal,
        budget=budget,
        model=model,
        quality=quality,
        clock=FakeClock(0.0, 11.0),
    )

    # Act
    result = service.execute(request(), scope_id="tenant-a")

    # Assert
    assert result.status == PublicStatus.TIMED_OUT
    assert len(budget.calls) == 0
    assert len(model.calls) == 0


def test_given_budget_denial_when_executed_then_model_is_not_invoked() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget(False)
    model = FakeModel([])
    quality = FakeQuality([])
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)

    # Act
    result = service.execute(request(), scope_id="tenant-a")

    # Assert
    assert result.status == PublicStatus.BLOCKED
    assert len(budget.calls) == 1
    assert len(model.calls) == 0
    assert len(quality.calls) == 0


def test_given_repeated_transient_failure_when_executed_then_only_one_retry_occurs() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    transient = ModelOutcome(
        status=ModelOutcomeStatus.TRANSIENT_FAILURE,
        public_reason_codes=("dependency.model_unavailable",),
    )
    model = FakeModel([transient, transient])
    quality = FakeQuality([])
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)

    # Act
    result = service.execute(request(), scope_id="tenant-a")
    state = journal.read(scope_id="tenant-a", idempotency_key="request-001")

    # Assert
    assert result.status == PublicStatus.FAILED
    assert [call.dispatch_ordinal for call in model.calls] == [1, 2]
    assert model.calls[0].operation_key == model.calls[1].operation_key
    assert state is not None and state.transient_retries_consumed == 1
    assert len(budget.calls) == 2


def test_given_low_quality_when_executed_then_escalation_and_quality_are_bounded() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    model = FakeModel([successful_outcome("First."), successful_outcome("Second.")])
    quality = FakeQuality(
        [
            QualitySummary(status="below_threshold", score="2"),
            QualitySummary(status="below_threshold", score="3"),
        ]
    )
    service = coordinator(journal=journal, budget=budget, model=model, quality=quality)

    # Act
    result = service.execute(request(), scope_id="tenant-a")
    state = journal.read(scope_id="tenant-a", idempotency_key="request-001")

    # Assert
    assert result.status == PublicStatus.QUALITY_UNMET
    assert [call.model_alias for call in model.calls] == ["economical", "capable"]
    assert len(quality.calls) == 2
    assert state is not None and state.quality_attempt_count == 2
    assert state.escalation_count == 1
    assert len(budget.calls) == 4


def test_given_late_result_after_cancellation_then_terminal_state_is_unchanged() -> None:
    # Arrange
    journal = InMemoryJournal()
    budget = FakeBudget()
    model = FakeModel([successful_outcome("Late answer.")])
    quality = FakeQuality([])
    service = coordinator(
        journal=journal,
        budget=budget,
        model=model,
        quality=quality,
        cancellation=FakeCancellation(cancel_on_call=3),
    )

    # Act
    result = service.execute(request(), scope_id="tenant-a")
    terminal = journal.read(scope_id="tenant-a", idempotency_key="request-001")
    assert terminal is not None
    winner = journal.commit_terminal(
        scope_id="tenant-a",
        idempotency_key="request-001",
        expected_revision=0,
        result=result,
    )

    # Assert
    assert result.status == PublicStatus.CANCELLED
    assert len(model.calls) == 1
    assert len(quality.calls) == 0
    assert terminal.attempts[0].usage is None
    assert winner == terminal
    with pytest.raises(StateTransitionError, match="terminal run state is immutable"):
        journal.compare_and_set(
            scope_id="tenant-a",
            idempotency_key="request-001",
            expected_revision=terminal.revision,
            state=replace(terminal, phase=RunPhase.QUALITY_PENDING),
        )


def test_given_run_and_attempt_state_when_mutated_then_records_are_frozen() -> None:
    # Arrange
    journal = InMemoryJournal()
    service = coordinator(
        journal=journal,
        budget=FakeBudget(),
        model=FakeModel([successful_outcome()]),
        quality=FakeQuality([QualitySummary(status="passed", score="5")]),
    )
    service.execute(request(), scope_id="tenant-a")
    state = journal.read(scope_id="tenant-a", idempotency_key="request-001")
    assert state is not None

    # Act & Assert
    with pytest.raises(FrozenInstanceError):
        state.revision = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        state.attempts[0].dispatch_count = 99  # type: ignore[misc]