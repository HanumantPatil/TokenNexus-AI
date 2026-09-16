"""Immutable orchestration state and guarded state transitions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from uuid import UUID

from tokennexus.contracts import ModelAlias, NormalizedRequest, PublicResult, QualitySummary, Usage


class RunPhase(StrEnum):
    """Closed set of coordinator-owned run phases."""

    ADMITTED = "admitted"
    ATTEMPT_IN_PROGRESS = "attempt_in_progress"
    QUALITY_PENDING = "quality_pending"
    ESCALATION_PENDING = "escalation_pending"
    TERMINAL = "terminal"


class StateTransitionError(RuntimeError):
    """Raised when a transition would violate orchestration invariants."""


@dataclass(frozen=True, slots=True)
class AttemptState:
    """Immutable evidence for one quality attempt."""

    attempt_id: UUID
    operation_key: str
    model_alias: ModelAlias
    parent_attempt_id: UUID | None = None
    dispatch_count: int = 0
    usage: Usage | None = None
    quality: QualitySummary | None = None


@dataclass(frozen=True, slots=True)
class RunState:
    """Immutable journaled state for one normalized request."""

    request: NormalizedRequest
    fingerprint: str
    deadline: float
    revision: int = 0
    phase: RunPhase = RunPhase.ADMITTED
    attempts: tuple[AttemptState, ...] = ()
    quality_attempt_count: int = 0
    escalation_count: int = 0
    transient_retries_consumed: int = 0
    terminal_result: PublicResult | None = None

    @property
    def is_terminal(self) -> bool:
        """Return whether this run has an absorbing terminal result."""
        return self.terminal_result is not None


def require_active(state: RunState) -> None:
    """Reject all mutations after the first terminal transition."""
    if state.is_terminal:
        raise StateTransitionError("terminal run state is immutable")


def begin_attempt(
    state: RunState,
    *,
    attempt_id: UUID,
    operation_key: str,
    model_alias: ModelAlias,
    parent_attempt_id: UUID | None = None,
) -> RunState:
    """Append a new attempt while enforcing the two-attempt limit."""
    require_active(state)
    if state.phase not in {RunPhase.ADMITTED, RunPhase.ESCALATION_PENDING}:
        raise StateTransitionError(f"cannot begin an attempt from {state.phase.value}")
    if len(state.attempts) >= 2:
        raise StateTransitionError("a run cannot contain more than two attempts")
    attempt = AttemptState(
        attempt_id=attempt_id,
        operation_key=operation_key,
        model_alias=model_alias,
        parent_attempt_id=parent_attempt_id,
    )
    return replace(state, phase=RunPhase.ATTEMPT_IN_PROGRESS, attempts=(*state.attempts, attempt))


def record_dispatch(state: RunState) -> RunState:
    """Record one physical dispatch against the active logical attempt."""
    require_active(state)
    if state.phase != RunPhase.ATTEMPT_IN_PROGRESS or not state.attempts:
        raise StateTransitionError("a dispatch requires an active attempt")
    active = state.attempts[-1]
    updated = replace(active, dispatch_count=active.dispatch_count + 1)
    return replace(state, attempts=(*state.attempts[:-1], updated))


def consume_transient_retry(state: RunState) -> RunState:
    """Consume the single request-wide transient retry allowance."""
    require_active(state)
    if state.transient_retries_consumed >= 1:
        raise StateTransitionError("the request-wide transient retry is already consumed")
    return replace(state, transient_retries_consumed=1)


def record_model_success(state: RunState, usage: Usage) -> RunState:
    """Record successful model usage and advance to quality evaluation."""
    require_active(state)
    if state.phase != RunPhase.ATTEMPT_IN_PROGRESS or not state.attempts:
        raise StateTransitionError("model success requires an active attempt")
    active = replace(state.attempts[-1], usage=usage)
    return replace(
        state,
        phase=RunPhase.QUALITY_PENDING,
        attempts=(*state.attempts[:-1], active),
    )


def record_quality(state: RunState, quality: QualitySummary) -> RunState:
    """Record one quality evaluation while enforcing the two-evaluation limit."""
    require_active(state)
    if state.phase != RunPhase.QUALITY_PENDING or not state.attempts:
        raise StateTransitionError("quality evaluation requires a successful model attempt")
    if state.quality_attempt_count >= 2:
        raise StateTransitionError("a run cannot contain more than two quality attempts")
    active = replace(state.attempts[-1], quality=quality)
    return replace(
        state,
        attempts=(*state.attempts[:-1], active),
        quality_attempt_count=state.quality_attempt_count + 1,
    )


def approve_escalation(state: RunState) -> RunState:
    """Approve the single capable-model escalation."""
    require_active(state)
    if state.phase != RunPhase.QUALITY_PENDING:
        raise StateTransitionError("escalation requires a completed quality evaluation")
    if state.escalation_count >= 1:
        raise StateTransitionError("a run cannot escalate more than once")
    return replace(
        state,
        phase=RunPhase.ESCALATION_PENDING,
        escalation_count=1,
    )


def terminalize(state: RunState, result: PublicResult) -> RunState:
    """Apply the first terminal result and make the run absorbing."""
    require_active(state)
    if result.request_id != state.request.request_id:
        raise StateTransitionError("terminal result request_id does not match the run")
    return replace(state, phase=RunPhase.TERMINAL, terminal_result=result)