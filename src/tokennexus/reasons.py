"""Closed public reason-code registry and status compatibility rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class PublicStatus(StrEnum):
    """Public execution result statuses."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEGRADED = "degraded"
    QUALITY_UNMET = "quality_unmet"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    CONFLICT = "conflict"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ReasonDefinition:
    """Immutable public meaning and allowed terminal statuses for a reason."""

    code: str
    allowed_statuses: frozenset[PublicStatus]
    retryable: bool
    safe_title: str
    safe_message: str


def _reason(
    code: str,
    statuses: tuple[PublicStatus, ...],
    *,
    retryable: bool = False,
    title: str,
    message: str,
) -> ReasonDefinition:
    return ReasonDefinition(code, frozenset(statuses), retryable, title, message)


_REASONS = (
    _reason(
        "request.in_progress",
        (PublicStatus.IN_PROGRESS,),
        retryable=True,
        title="Request in progress",
        message="The matching request is already being processed.",
    ),
    _reason(
        "request.invalid",
        (PublicStatus.REJECTED,),
        title="Invalid request",
        message="The request does not satisfy the contract.",
    ),
    _reason(
        "request.constraint_invalid",
        (PublicStatus.REJECTED,),
        title="Invalid request constraint",
        message="A request constraint is invalid or unsupported.",
    ),
    _reason(
        "request.idempotency_conflict",
        (PublicStatus.CONFLICT,),
        title="Idempotency key conflict",
        message="The idempotency key was already used for a different request.",
    ),
    _reason(
        "request.cancelled_by_client",
        (PublicStatus.CANCELLED,),
        title="Request cancelled",
        message="The request was cancelled by the client.",
    ),
    _reason(
        "request.deadline_exceeded",
        (PublicStatus.TIMED_OUT,),
        title="Request deadline exceeded",
        message="The request deadline expired before processing completed.",
    ),
    _reason(
        "budget.within_limit",
        (PublicStatus.COMPLETED, PublicStatus.DEGRADED, PublicStatus.QUALITY_UNMET),
        title="Budget within limit",
        message="The approved execution remained within its budget.",
    ),
    _reason(
        "budget.limit_exceeded",
        (PublicStatus.BLOCKED, PublicStatus.QUALITY_UNMET),
        title="Budget limit exceeded",
        message="No eligible execution path fits the request budget.",
    ),
    _reason(
        "route.economical_eligible",
        (PublicStatus.COMPLETED, PublicStatus.DEGRADED, PublicStatus.QUALITY_UNMET),
        title="Economical route eligible",
        message="The economical model tier satisfied the routing requirements.",
    ),
    _reason(
        "route.capable_required",
        (PublicStatus.COMPLETED, PublicStatus.DEGRADED, PublicStatus.QUALITY_UNMET),
        title="Capable route required",
        message="The capable model tier was required by governed routing.",
    ),
    _reason(
        "quality.threshold_met",
        (PublicStatus.COMPLETED,),
        title="Quality threshold met",
        message="The evaluated output met the required quality threshold.",
    ),
    _reason(
        "quality.threshold_unmet",
        (PublicStatus.QUALITY_UNMET,),
        title="Quality threshold unmet",
        message="The evaluated output did not meet the required quality threshold.",
    ),
    _reason(
        "quality.evaluation_unavailable",
        (PublicStatus.DEGRADED,),
        title="Quality evaluation unavailable",
        message="Quality could not be evaluated for this output.",
    ),
    _reason(
        "escalation.quality_triggered",
        (PublicStatus.COMPLETED, PublicStatus.QUALITY_UNMET),
        title="Quality escalation triggered",
        message="A below-threshold result triggered the single governed escalation.",
    ),
    _reason(
        "escalation.not_permitted_budget",
        (PublicStatus.QUALITY_UNMET,),
        title="Escalation not permitted",
        message="The remaining budget did not permit escalation.",
    ),
    _reason(
        "escalation.not_permitted_latency",
        (PublicStatus.QUALITY_UNMET,),
        title="Escalation not permitted",
        message="The remaining time did not permit escalation.",
    ),
    _reason(
        "escalation.not_permitted_policy",
        (PublicStatus.QUALITY_UNMET,),
        title="Escalation not permitted",
        message="The active policy did not permit escalation.",
    ),
    _reason(
        "dependency.model_unavailable",
        (PublicStatus.FAILED, PublicStatus.DEGRADED),
        retryable=True,
        title="Model unavailable",
        message="An eligible model path was unavailable.",
    ),
    _reason(
        "system.controlled_failure",
        (PublicStatus.FAILED,),
        title="Controlled failure",
        message="Processing failed safely.",
    ),
)

PUBLIC_REASON_REGISTRY = MappingProxyType({entry.code: entry for entry in _REASONS})


def ensure_registered_reason(code: str) -> str:
    """Return a public reason code or fail closed when it is unknown."""
    if code not in PUBLIC_REASON_REGISTRY:
        raise ValueError(f"unknown public reason code: {code}")
    return code


def validate_public_reasons(status: PublicStatus, codes: tuple[str, ...]) -> None:
    """Validate every reason against its allowed terminal statuses."""
    if not codes:
        raise ValueError("at least one public reason code is required")
    for code in codes:
        definition = PUBLIC_REASON_REGISTRY[ensure_registered_reason(code)]
        if status not in definition.allowed_statuses:
            raise ValueError(f"public reason code {code} is not valid for status {status.value}")
