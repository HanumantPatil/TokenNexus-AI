"""Tests for deterministic provider-neutral orchestration substitutes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest

from tokennexus.adapters import (
    ModelCallRecord,
    ModelScript,
    QualityCallRecord,
    QualityFailure,
    QualityScript,
    ScriptedModelPort,
    ScriptedQualityEvaluator,
    ScriptExhaustedError,
)
from tokennexus.contracts import (
    BudgetReservation,
    Money,
    NormalizedRequest,
    Output,
    PublicRequest,
    PublicResult,
    QualitySummary,
    ReservationRequest,
    Task,
    Usage,
)
from tokennexus.coordinator import Coordinator
from tokennexus.fingerprint import normalize_request
from tokennexus.journal import InMemoryJournal
from tokennexus.ports import (
    ModelAlias,
    ModelInvocation,
    ModelOutcome,
    ModelOutcomeStatus,
    TransientDependencyError,
)
from tokennexus.reasons import PublicStatus


class DeterministicClock:
    """Return one stable monotonic timestamp."""

    def __init__(self, value: float = 100.0) -> None:
        self._value = value

    def now(self) -> float:
        return self._value

    def utc_now(self) -> datetime:
        return datetime(2026, 9, 16, 12, 34, 56, 789000, tzinfo=UTC)


class DeterministicIds:
    """Generate a repeatable sequence of valid UUIDv7 identifiers."""

    def __init__(self) -> None:
        self._ordinal = 0

    def new(self) -> UUID:
        self._ordinal += 1
        return UUID(f"01890f3e-0000-7000-8000-{self._ordinal:012x}")


class AllowAllBudget:
    """Allow and record every coordinator reservation."""

    def __init__(self) -> None:
        self.calls: list[ReservationRequest] = []

    def reserve(self, request: ReservationRequest) -> BudgetReservation:
        self.calls.append(request)
        return BudgetReservation(request=request)


class NeverCancelled:
    """Keep deterministic coordinator runs active."""

    def is_cancelled(self, request_id: UUID) -> bool:
        del request_id
        return False


def normalized_request() -> NormalizedRequest:
    """Build a normalized request with a fixed identifier."""
    request = PublicRequest(
        idempotency_key="adapter-test",
        application_id="adapter-tests",
        task=Task(content="Return a deterministic answer."),
    )
    return normalize_request(
        request,
        scope_id="tenant-a",
        request_id=UUID("01890f3e-0000-7000-8000-000000000001"),
    )


def successful_outcome(content: str, *, cost: str = "0.01") -> ModelOutcome:
    """Build one successful provider-neutral specialist outcome."""
    return ModelOutcome(
        status=ModelOutcomeStatus.SUCCEEDED,
        output=Output(content=content),
        usage=Usage(
            input_tokens=10,
            output_tokens=5,
            estimated_cost=Money(amount=cost),
            provider_latency_ms=20,
        ),
    )


def invocation(model_alias: ModelAlias, *, dispatch_ordinal: int = 1) -> ModelInvocation:
    """Build one deterministic model invocation."""
    return ModelInvocation(
        request=normalized_request(),
        attempt_id=UUID("01890f3e-0000-7000-8000-000000000002"),
        operation_key="operation-1",
        dispatch_ordinal=dispatch_ordinal,
        model_alias=model_alias,
    )


def test_given_both_aliases_when_invoked_then_same_contract_and_exact_calls_are_preserved() -> None:
    # Arrange
    economical = successful_outcome("Economical.")
    capable = successful_outcome("Capable.", cost="0.02")
    model = ScriptedModelPort(ModelScript(outcomes=(economical, capable)))

    # Act
    first = model.invoke(invocation("economical"))
    second = model.invoke(invocation("capable"))

    # Assert
    assert (first, second) == (economical, capable)
    assert tuple(call.invocation.model_alias for call in model.calls) == (
        "economical",
        "capable",
    )
    assert tuple(call.ordinal for call in model.calls) == (1, 2)


def test_given_exhausted_scripts_when_called_then_errors_are_clear_and_calls_stay_exact() -> None:
    # Arrange
    request = normalized_request()
    output = Output(content="Answer.")
    model = ScriptedModelPort(ModelScript(outcomes=()))
    quality = ScriptedQualityEvaluator(QualityScript(outcomes=()))

    # Act & Assert
    with pytest.raises(ScriptExhaustedError, match="model script exhausted at call 1"):
        model.invoke(invocation("economical"))
    with pytest.raises(ScriptExhaustedError, match="quality script exhausted at call 1"):
        quality.evaluate(request, output)
    assert len(model.calls) == 1
    assert len(quality.calls) == 1


def test_given_scripts_and_records_when_mutation_is_attempted_then_they_are_immutable() -> None:
    # Arrange
    outcome = successful_outcome("Stable.")
    model = ScriptedModelPort(ModelScript(outcomes=(outcome,)))
    model.invoke(invocation("economical"))

    # Act & Assert
    with pytest.raises(FrozenInstanceError):
        model.script.outcomes = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        model.calls[0].ordinal = 2  # type: ignore[misc]


def test_given_success_and_failure_shapes_when_created_then_safe_facts_are_enforced() -> None:
    # Act
    terminal = ModelOutcome(
        status=ModelOutcomeStatus.TERMINAL_FAILURE,
        public_reason_codes=("system.controlled_failure",),
    )

    # Assert
    assert terminal.output is None
    assert terminal.usage is None
    assert terminal.public_reason_codes == ("system.controlled_failure",)
    with pytest.raises(ValueError, match="require output and usage"):
        ModelOutcome(status=ModelOutcomeStatus.SUCCEEDED)
    with pytest.raises(ValueError, match="require safe reason codes"):
        ModelOutcome(status=ModelOutcomeStatus.TRANSIENT_FAILURE)
    with pytest.raises(ValueError, match="retryable reason codes"):
        ModelOutcome(
            status=ModelOutcomeStatus.TRANSIENT_FAILURE,
            public_reason_codes=("system.controlled_failure",),
        )


def test_given_transient_model_step_when_coordinated_then_only_coordinator_retries_once() -> None:
    # Arrange
    transient = ModelOutcome(
        status=ModelOutcomeStatus.TRANSIENT_FAILURE,
        public_reason_codes=("dependency.model_unavailable",),
    )
    model = ScriptedModelPort(
        ModelScript(outcomes=(transient, successful_outcome("Recovered.")))
    )
    quality = ScriptedQualityEvaluator(
        QualityScript(outcomes=(QualitySummary(status="passed", score="5"),))
    )
    service = Coordinator(
        journal=InMemoryJournal(),
        budget=AllowAllBudget(),
        model=model,
        quality=quality,
        cancellation=NeverCancelled(),
        clock=DeterministicClock(),
        ids=DeterministicIds(),
    )

    # Act
    result = service.execute(
        PublicRequest(
            idempotency_key="retry-test",
            application_id="adapter-tests",
            task=Task(content="Retry once."),
        ),
        scope_id="tenant-a",
    )

    # Assert
    assert result.status == PublicStatus.COMPLETED
    assert tuple(call.invocation.dispatch_ordinal for call in model.calls) == (1, 2)
    assert len(quality.calls) == 1


def test_given_identical_dependencies_when_runs_repeat_then_results_and_calls_are_stable() -> None:
    # Arrange
    def execute_once() -> tuple[
        PublicResult,
        tuple[ModelCallRecord, ...],
        tuple[QualityCallRecord, ...],
        int,
    ]:
        model = ScriptedModelPort(
            ModelScript(
                outcomes=(
                    successful_outcome("Economical."),
                    successful_outcome("Capable.", cost="0.02"),
                )
            )
        )
        quality = ScriptedQualityEvaluator(
            QualityScript(
                outcomes=(
                    QualitySummary(status="below_threshold", score="2"),
                    QualitySummary(status="passed", score="5"),
                )
            )
        )
        budget = AllowAllBudget()
        service = Coordinator(
            journal=InMemoryJournal(),
            budget=budget,
            model=model,
            quality=quality,
            cancellation=NeverCancelled(),
            clock=DeterministicClock(),
            ids=DeterministicIds(),
        )
        result = service.execute(
            PublicRequest(
                idempotency_key="repeatable-run",
                application_id="adapter-tests",
                task=Task(content="Escalate deterministically."),
            ),
            scope_id="tenant-a",
        )
        return result, model.calls, quality.calls, len(budget.calls)

    # Act
    first = execute_once()
    second = execute_once()

    # Assert
    assert first == second
    result, model_calls, quality_calls, budget_calls = first
    assert result.status == PublicStatus.COMPLETED
    assert tuple(call.invocation.model_alias for call in model_calls) == (
        "economical",
        "capable",
    )
    assert len(quality_calls) == 2
    assert budget_calls == 4


def test_given_quality_failure_when_evaluated_then_one_call_raises_typed_failure() -> None:
    # Arrange
    quality = ScriptedQualityEvaluator(
        QualityScript(outcomes=(QualityFailure("quality dependency unavailable"),))
    )

    # Act & Assert
    with pytest.raises(TransientDependencyError, match="quality dependency unavailable"):
        quality.evaluate(normalized_request(), Output(content="Answer."))
    assert len(quality.calls) == 1