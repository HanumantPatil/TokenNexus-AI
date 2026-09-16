"""Narrow synchronous dependency protocols for governed orchestration."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from tokennexus.contracts import (
    ModelAlias,
    Money,
    NormalizedRequest,
    Output,
    QualitySummary,
    Usage,
)
from tokennexus.ids import new_uuid7
from tokennexus.reasons import PUBLIC_REASON_REGISTRY, ensure_registered_reason


class Clock(Protocol):
    """Provide monotonic time and canonical-result wall time."""

    def now(self) -> float:
        """Return a monotonic timestamp in seconds."""
        raise NotImplementedError

    def utc_now(self) -> datetime:
        """Return the current timezone-aware UTC instant."""
        raise NotImplementedError


class IdSource(Protocol):
    """Generate correlation identifiers."""

    def new(self) -> UUID:
        """Return a UUIDv7 identifier."""
        raise NotImplementedError


class CancellationPort(Protocol):
    """Report whether a request has been cancelled."""

    def is_cancelled(self, request_id: UUID) -> bool:
        """Return whether cancellation has been requested."""
        raise NotImplementedError


class BudgetPort(Protocol):
    """Atomically reserve worst-case allowance before an operation."""

    def reserve(
        self,
        *,
        request_id: UUID,
        operation_key: str,
        estimated_cost: Money,
    ) -> bool:
        """Reserve allowance once and return whether the operation may proceed."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ModelInvocation:
    """One physical provider-neutral model dispatch."""

    request: NormalizedRequest
    attempt_id: UUID
    operation_key: str
    dispatch_ordinal: int
    model_alias: ModelAlias


class ModelOutcomeStatus(StrEnum):
    """Facts returned by a model dependency without policy decisions."""

    SUCCEEDED = "succeeded"
    TRANSIENT_FAILURE = "transient_failure"
    TERMINAL_FAILURE = "terminal_failure"


@dataclass(frozen=True, slots=True)
class ModelOutcome:
    """Provider-neutral facts from one physical model dispatch."""

    status: ModelOutcomeStatus
    output: Output | None = None
    usage: Usage | None = None
    public_reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require complete, safe facts for successful and failed outcomes."""
        reason_codes = tuple(sorted(self.public_reason_codes))
        if len(reason_codes) != len(set(reason_codes)):
            raise ValueError("model outcome public_reason_codes must be unique")
        for code in reason_codes:
            ensure_registered_reason(code)
        object.__setattr__(self, "public_reason_codes", reason_codes)

        if self.status == ModelOutcomeStatus.SUCCEEDED:
            if self.output is None or self.usage is None:
                raise ValueError("successful model outcomes require output and usage")
            if reason_codes:
                raise ValueError("successful model outcomes must omit failure reason codes")
            return

        if self.output is not None or self.usage is not None:
            raise ValueError("failed model outcomes must omit output and usage")
        if not reason_codes:
            raise ValueError("failed model outcomes require safe reason codes")
        if self.status == ModelOutcomeStatus.TRANSIENT_FAILURE and any(
            not PUBLIC_REASON_REGISTRY[code].retryable for code in reason_codes
        ):
            raise ValueError("transient model failures require retryable reason codes")


class ModelPort(Protocol):
    """Invoke either governed model alias without hidden retries."""

    def estimate_cost(self, request: NormalizedRequest, model_alias: ModelAlias) -> Money:
        """Return the worst-case reservation for one physical dispatch."""
        raise NotImplementedError

    def invoke(self, invocation: ModelInvocation) -> ModelOutcome:
        """Perform exactly one physical dispatch."""
        raise NotImplementedError


class QualityEvaluator(Protocol):
    """Evaluate one output without choosing escalation or terminal status."""

    def estimate_cost(self, request: NormalizedRequest, output: Output) -> Money:
        """Return the worst-case reservation for one evaluation call."""
        raise NotImplementedError

    def evaluate(self, request: NormalizedRequest, output: Output) -> QualitySummary:
        """Return quality facts for one output."""
        raise NotImplementedError


class TransientDependencyError(RuntimeError):
    """Signal an allowlisted failure known to precede dependency acceptance."""


class SystemClock:
    """Production monotonic and UTC wall clock."""

    def now(self) -> float:
        """Return the process monotonic clock."""
        return time.monotonic()

    def utc_now(self) -> datetime:
        """Return the current UTC wall-clock instant."""
        return datetime.now(UTC)


class Uuid7Source:
    """Production UUIDv7 source."""

    def new(self) -> UUID:
        """Return a new UUIDv7 identifier."""
        return new_uuid7()


class NeverCancelled:
    """Default cancellation source for callers without cancellation wiring."""

    def is_cancelled(self, request_id: UUID) -> bool:
        """Return false for every request."""
        del request_id
        return False