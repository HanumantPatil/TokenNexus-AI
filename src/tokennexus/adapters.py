"""Deterministic provider-neutral substitutes for orchestration tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from tokennexus.contracts import Money, NormalizedRequest, Output, QualitySummary
from tokennexus.ports import (
    ModelAlias,
    ModelInvocation,
    ModelOutcome,
    TransientDependencyError,
)


class ScriptExhaustedError(RuntimeError):
    """Report that a deterministic substitute received an unconfigured call."""


@dataclass(frozen=True, slots=True)
class ModelScript:
    """Immutable outcomes and cost estimate for model invocations."""

    outcomes: tuple[ModelOutcome, ...]
    estimated_cost: Money = field(default_factory=lambda: Money(amount="0"))

    def __post_init__(self) -> None:
        """Reject mutable script containers."""
        if not isinstance(self.outcomes, tuple):
            raise TypeError("model script outcomes must be a tuple")


@dataclass(frozen=True, slots=True)
class QualityFailure:
    """Immutable typed transient failure for one quality evaluation."""

    message: str

    def __post_init__(self) -> None:
        """Require a useful deterministic failure message."""
        if not self.message:
            raise ValueError("quality failure message must not be empty")


QualityScriptStep = QualitySummary | QualityFailure


@dataclass(frozen=True, slots=True)
class QualityScript:
    """Immutable outcomes and cost estimate for quality evaluations."""

    outcomes: tuple[QualityScriptStep, ...]
    estimated_cost: Money = field(default_factory=lambda: Money(amount="0"))

    def __post_init__(self) -> None:
        """Reject mutable script containers."""
        if not isinstance(self.outcomes, tuple):
            raise TypeError("quality script outcomes must be a tuple")


@dataclass(frozen=True, slots=True)
class ModelCallRecord:
    """Immutable record of one model-port invocation."""

    ordinal: int
    invocation: ModelInvocation


@dataclass(frozen=True, slots=True)
class QualityCallRecord:
    """Immutable record of one quality-evaluator call."""

    ordinal: int
    request: NormalizedRequest
    output: Output


class ScriptedModelPort:
    """Consume exactly one configured model outcome per invocation."""

    def __init__(self, script: ModelScript) -> None:
        self._script = script
        self._next_outcome = 0
        self._calls: list[ModelCallRecord] = []

    @property
    def script(self) -> ModelScript:
        """Return the immutable configured script."""
        return self._script

    @property
    def calls(self) -> tuple[ModelCallRecord, ...]:
        """Return an immutable snapshot of recorded calls."""
        return tuple(self._calls)

    def estimate_cost(self, request: NormalizedRequest, model_alias: ModelAlias) -> Money:
        """Return the fixed configured reservation estimate."""
        del request, model_alias
        return self._script.estimated_cost

    def invoke(self, invocation: ModelInvocation) -> ModelOutcome:
        """Record one invocation and consume exactly one scripted outcome."""
        ordinal = len(self._calls) + 1
        self._calls.append(ModelCallRecord(ordinal=ordinal, invocation=invocation))
        if self._next_outcome >= len(self._script.outcomes):
            raise ScriptExhaustedError(
                f"model script exhausted at call {ordinal} for alias {invocation.model_alias}"
            )
        outcome = self._script.outcomes[self._next_outcome]
        self._next_outcome += 1
        return outcome


class ScriptedQualityEvaluator:
    """Consume exactly one configured quality step per evaluation."""

    def __init__(self, script: QualityScript) -> None:
        self._script = script
        self._next_outcome = 0
        self._calls: list[QualityCallRecord] = []

    @property
    def script(self) -> QualityScript:
        """Return the immutable configured script."""
        return self._script

    @property
    def calls(self) -> tuple[QualityCallRecord, ...]:
        """Return an immutable snapshot of recorded calls."""
        return tuple(self._calls)

    def estimate_cost(self, request: NormalizedRequest, output: Output) -> Money:
        """Return the fixed configured reservation estimate."""
        del request, output
        return self._script.estimated_cost

    def evaluate(self, request: NormalizedRequest, output: Output) -> QualitySummary:
        """Record one evaluation and consume exactly one scripted step."""
        ordinal = len(self._calls) + 1
        self._calls.append(QualityCallRecord(ordinal=ordinal, request=request, output=output))
        if self._next_outcome >= len(self._script.outcomes):
            raise ScriptExhaustedError(f"quality script exhausted at call {ordinal}")
        outcome = self._script.outcomes[self._next_outcome]
        self._next_outcome += 1
        if isinstance(outcome, QualityFailure):
            raise TransientDependencyError(outcome.message)
        return outcome