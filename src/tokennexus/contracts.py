"""Strict immutable request contracts for TokenNexus."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Final, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from tokennexus.reasons import PublicStatus, ensure_registered_reason, validate_public_reasons

CONTRACT_VERSION: Final = "1.0.0"
CANONICAL_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$")
CANONICAL_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{3}Z$"
)

ApplicationId = Annotated[str, StringConstraints(min_length=1, max_length=128)]
IdempotencyKey = Annotated[str, StringConstraints(min_length=1, max_length=256)]
NonEmptyText = Annotated[str, StringConstraints(min_length=1)]
PublicReasonCode = Annotated[str, AfterValidator(ensure_registered_reason)]
ContractVersion = Literal["1.0.0"]
ModelAlias = Literal["economical", "capable"]
EscalationStatus = Literal["not_required", "performed", "not_permitted"]
BudgetAction = Literal["allow", "downgrade", "approval_required", "block"]
EligibilityGateName = Literal["quality", "latency", "governance", "availability", "budget"]
EligibilityOutcome = Literal["passed", "failed", "not_evaluated"]
ReservationStatus = Literal["active", "settled", "released"]
PolicyAction = Literal["update", "rollback"]


def validate_canonical_utc_timestamp(value: object) -> str:
    """Require the exact UTC millisecond RFC 3339 wire profile."""
    if not isinstance(value, str) or CANONICAL_UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError("timestamp must use canonical UTC milliseconds")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as error:
        raise ValueError("timestamp must be a valid canonical UTC instant") from error
    return value


CanonicalUtcTimestamp = Annotated[str, AfterValidator(validate_canonical_utc_timestamp)]


class ContractModel(BaseModel):
    """Base configuration shared by all boundary contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, validate_default=True)


def contract_schema(model: type[ContractModel]) -> dict[str, object]:
    """Export a Draft 2020-12 schema with a stable contract identifier."""
    schema = model.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://schemas.tokennexus.example/v1/{model.__name__}.schema.json"
    return schema


def validate_canonical_decimal(
    value: object,
    *,
    field_name: str,
    minimum: Decimal,
    maximum: Decimal | None = None,
    maximum_scale: int = 6,
) -> str:
    """Validate and return an exact canonical decimal string."""
    if not isinstance(value, str) or CANONICAL_DECIMAL_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical decimal string")

    decimal_value = Decimal(value)
    if decimal_value < minimum or (maximum is not None and decimal_value > maximum):
        upper_bound = f" and at most {maximum}" if maximum is not None else ""
        raise ValueError(f"{field_name} must be at least {minimum}{upper_bound}")
    exponent = decimal_value.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError(f"{field_name} must be finite")
    if max(0, -exponent) > maximum_scale:
        raise ValueError(f"{field_name} must have at most {maximum_scale} fractional digits")
    return value


class Money(ContractModel):
    """A non-negative ISO 4217 amount represented without binary floats."""

    currency: Literal["USD"] = "USD"
    amount: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: object) -> str:
        """Require the MVP canonical money profile."""
        return validate_canonical_decimal(
            value,
            field_name="amount",
            minimum=Decimal(0),
        )


class EligibilityGate(ContractModel):
    """Safe outcome of one closed routing eligibility check."""

    gate: EligibilityGateName
    outcome: EligibilityOutcome


class ModelPolicy(ContractModel):
    """Frozen eligibility and pricing facts for one stable model alias."""

    alias: ModelAlias
    enabled: bool = True
    supported_criticalities: tuple[Literal["standard", "high", "critical"], ...]
    maximum_supported_quality: str
    minimum_latency_ms: int = Field(ge=1, le=300_000)
    input_cost_per_1000_tokens: str
    output_cost_per_1000_tokens: str

    @field_validator(
        "maximum_supported_quality",
        "input_cost_per_1000_tokens",
        "output_cost_per_1000_tokens",
    )
    @classmethod
    def validate_policy_decimal(cls, value: object, info: object) -> str:
        """Require canonical non-negative policy decimal values."""
        field_name = getattr(info, "field_name", "policy value")
        maximum = Decimal(5) if field_name == "maximum_supported_quality" else None
        minimum = Decimal(1) if field_name == "maximum_supported_quality" else Decimal(0)
        return validate_canonical_decimal(
            value,
            field_name=field_name,
            minimum=minimum,
            maximum=maximum,
        )

    @field_validator("supported_criticalities")
    @classmethod
    def validate_supported_criticalities(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Reject duplicate criticality entries."""
        if not value or len(value) != len(set(value)):
            raise ValueError("supported_criticalities must be non-empty and unique")
        return value


class PolicySnapshot(ContractModel):
    """Immutable approved routing and pricing policy used for one admission."""

    policy_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    pricing_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    models: tuple[ModelPolicy, ...]
    capable_preferred_criticalities: tuple[Literal["high", "critical"], ...] = (
        "high",
        "critical",
    )
    approval_required_when_unfunded: bool = False

    @model_validator(mode="after")
    def validate_aliases(self) -> PolicySnapshot:
        """Require exactly one policy entry for each stable model alias."""
        aliases = tuple(model.alias for model in self.models)
        if len(aliases) != len(set(aliases)):
            raise ValueError("policy model aliases must be unique")
        if set(aliases) != {"economical", "capable"}:
            raise ValueError("policy must define economical and capable aliases")
        return self


class CandidateEstimate(ContractModel):
    """Pessimistic cost and eligibility evidence for one candidate alias."""

    model_alias: ModelAlias
    estimated_cost: Money
    eligibility_gates: tuple[EligibilityGate, ...]


class RouteBudgetDecision(ContractModel):
    """Deterministic admission decision produced without paid work."""

    policy_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    pricing_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    selected_model_alias: ModelAlias | None = None
    budget_action: BudgetAction
    candidate_estimates: tuple[CandidateEstimate, ...]
    selected_estimate: Money | None = None
    eligibility_gates: tuple[EligibilityGate, ...]
    public_reason_codes: tuple[PublicReasonCode, ...]

    @field_validator("public_reason_codes")
    @classmethod
    def validate_decision_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject duplicates and return deterministic public reasons."""
        if not value or len(value) != len(set(value)):
            raise ValueError("decision public_reason_codes must be non-empty and unique")
        return tuple(sorted(value))


class ReservationRequest(ContractModel):
    """Worst-case allowance required before one physical paid operation."""

    reservation_id: UUID
    request_id: UUID
    operation_key: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    dispatch_ordinal: int = Field(ge=1)
    pricing_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    estimated_cost: Money
    input_tokens: int = Field(ge=0, le=1_000_000)
    output_tokens: int = Field(ge=0, le=100_000)
    duration_ms: int = Field(ge=0, le=300_000)
    tool_calls: int = Field(ge=0, le=100)


class BudgetReservation(ContractModel):
    """Immutable receipt proving allowance existed before an operation."""

    request: ReservationRequest
    status: ReservationStatus = "active"


class PolicyChangeCommand(ContractModel):
    """Confirmed optimistic command for an immutable policy update."""

    expected_active_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    proposed_policy: PolicySnapshot
    confirmed: bool


class PolicyAuditEvent(ContractModel):
    """Safe immutable record of one policy administration attempt."""

    event_id: UUID
    action: PolicyAction
    actor_id_hash: Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
    outcome: Literal["applied", "denied", "invalid", "conflict"]
    previous_version: str
    source_version: str | None = None
    resulting_version: str | None = None
    public_reason_code: PublicReasonCode
    recorded_at_utc: CanonicalUtcTimestamp


class MandatoryContext(ContractModel):
    """Order-sensitive context that must survive request processing."""

    context_id: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    kind: Literal["instruction", "evidence"]
    content: NonEmptyText


class Task(ContractModel):
    """Caller task and its mandatory context."""

    content: NonEmptyText
    content_type: Literal["text/plain", "application/json"] = "text/plain"
    mandatory_context: tuple[MandatoryContext, ...] = ()


class RequestConstraints(ContractModel):
    """Declared and defaulted execution limits for one request."""

    criticality: Literal["standard", "high", "critical"] = "standard"
    minimum_quality: str = "4"
    maximum_latency_ms: int = Field(default=10_000, ge=1, le=300_000)
    maximum_budget: Money = Field(default_factory=lambda: Money(amount="0.02"))
    maximum_input_tokens: int = Field(default=8_000, ge=1, le=1_000_000)
    maximum_output_tokens: int = Field(default=1_000, ge=1, le=100_000)
    maximum_tool_calls: int = Field(default=1, ge=0, le=100)

    @field_validator("minimum_quality")
    @classmethod
    def validate_minimum_quality(cls, value: object) -> str:
        """Require the pilot 1-5 quality scale as a canonical decimal."""
        return validate_canonical_decimal(
            value,
            field_name="minimum_quality",
            minimum=Decimal(1),
            maximum=Decimal(5),
        )


class CacheDirectives(ContractModel):
    """Caller cache intent with deterministic admission defaults."""

    eligible: bool = True
    freshness: Literal["standard", "fresh"] = "standard"
    maximum_entry_age_ms: int = Field(default=3_600_000, ge=0, le=86_400_000)
    sensitivity: Literal["non_sensitive", "sensitive"] = "non_sensitive"


class PublicRequest(ContractModel):
    """Versioned caller envelope accepted at the public boundary."""

    schema_version: ContractVersion = CONTRACT_VERSION
    idempotency_key: IdempotencyKey
    application_id: ApplicationId
    task: Task
    constraints: RequestConstraints = Field(default_factory=RequestConstraints)
    cache_directives: CacheDirectives = Field(default_factory=CacheDirectives)


class NormalizedRequest(ContractModel):
    """Server-derived request projection used by policy and identity checks."""

    schema_version: ContractVersion = CONTRACT_VERSION
    request_id: UUID
    scope_id: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    application_id: ApplicationId
    task: Task
    effective_constraints: RequestConstraints
    cache_directives: CacheDirectives
    authorization_context_fingerprint: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: UUID) -> UUID:
        """Require generated request identifiers to be UUIDv7 values."""
        if value.version != 7:
            raise ValueError("request_id must be a UUIDv7 value")
        return value


class Usage(ContractModel):
    """Provider-neutral resource usage for an attempt or public decision."""

    input_tokens: int = Field(ge=0, le=1_000_000)
    output_tokens: int = Field(ge=0, le=100_000)
    estimated_cost: Money
    provider_latency_ms: int = Field(ge=0, le=300_000)
    tool_call_count: int = Field(default=0, ge=0, le=100)


class QualitySummary(ContractModel):
    """Safe quality facts exposed in a terminal decision summary."""

    status: Literal["passed", "below_threshold", "unavailable"]
    score: str | None = None
    threshold: str = "4"

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: object) -> str | None:
        """Validate an optional score on the pilot 1-5 scale."""
        if value is None:
            return None
        return validate_canonical_decimal(
            value,
            field_name="score",
            minimum=Decimal(1),
            maximum=Decimal(5),
        )

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, value: object) -> str:
        """Validate a threshold on the pilot 1-5 scale."""
        return validate_canonical_decimal(
            value,
            field_name="threshold",
            minimum=Decimal(1),
            maximum=Decimal(5),
        )

    @model_validator(mode="after")
    def validate_status_consistency(self) -> QualitySummary:
        """Keep quality status, score, and threshold mutually consistent."""
        if self.status == "unavailable":
            if self.score is not None:
                raise ValueError("unavailable quality must omit score")
            return self
        if self.score is None:
            raise ValueError(f"{self.status} quality requires score")

        score = Decimal(self.score)
        threshold = Decimal(self.threshold)
        if self.status == "passed" and score < threshold:
            raise ValueError("passed quality requires score at or above threshold")
        if self.status == "below_threshold" and score >= threshold:
            raise ValueError("below_threshold quality requires score below threshold")
        return self


class Output(ContractModel):
    """Bounded provider-neutral output returned to a caller."""

    content: NonEmptyText
    content_type: Literal["text/plain", "application/json"] = "text/plain"


class PublicError(ContractModel):
    """Safe terminal error without provider or diagnostic internals."""

    public_reason_code: PublicReasonCode
    safe_message: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class DecisionSummary(ContractModel):
    """Safe, deterministic explanation of a terminal decision."""

    model_alias: ModelAlias | None = None
    policy_version: str | None = None
    pricing_version: str | None = None
    budget_action: BudgetAction | None = None
    estimated_cost: Money | None = None
    eligibility_gates: tuple[EligibilityGate, ...] = ()
    usage: Usage | None = None
    end_to_end_latency_ms: int = Field(ge=0, le=600_000)
    quality: QualitySummary | None = None
    cache_status: Literal["hit", "miss", "bypassed", "not_evaluated"] = "not_evaluated"
    escalation_status: EscalationStatus = "not_required"
    public_reason_codes: tuple[PublicReasonCode, ...]

    @field_validator("public_reason_codes")
    @classmethod
    def validate_reason_order(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject duplicates and materialize deterministic lexical order."""
        if len(value) != len(set(value)):
            raise ValueError("public_reason_codes must be unique")
        return tuple(sorted(value))


class PublicResult(ContractModel):
    """Strict public execution result."""

    schema_version: ContractVersion = CONTRACT_VERSION
    request_id: UUID
    timestamp: CanonicalUtcTimestamp
    status: PublicStatus
    output: Output | None = None
    decision_summary: DecisionSummary
    error: PublicError | None = None

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: UUID) -> UUID:
        """Require the result request identifier to remain UUIDv7."""
        if value.version != 7:
            raise ValueError("request_id must be a UUIDv7 value")
        return value

    @model_validator(mode="after")
    def validate_result_shape(self) -> PublicResult:
        """Validate output/error shape and status-compatible reason codes."""
        output_statuses = {
            PublicStatus.COMPLETED,
            PublicStatus.DEGRADED,
            PublicStatus.QUALITY_UNMET,
        }
        if self.status == PublicStatus.COMPLETED and self.output is None:
            raise ValueError("completed results require output")
        if self.status not in output_statuses and self.output is not None:
            raise ValueError(f"{self.status.value} results must omit output")
        if self.status in output_statuses and self.error is not None:
            raise ValueError(f"{self.status.value} results must omit error")
        if self.status not in output_statuses and self.error is None:
            raise ValueError(f"{self.status.value} results require a safe error")

        validate_public_reasons(self.status, self.decision_summary.public_reason_codes)
        if self.error is not None:
            validate_public_reasons(self.status, (self.error.public_reason_code,))
        return self


class FieldViolation(ContractModel):
    """Safe validation failure at a JSON Pointer path."""

    path: Annotated[str, StringConstraints(pattern=r"^/")]
    public_reason_code: PublicReasonCode
    safe_message: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class DomainError(ContractModel):
    """Transport-neutral safe domain error."""

    schema_version: ContractVersion = CONTRACT_VERSION
    domain_error_id: UUID
    request_id: UUID | None = None
    public_reason_code: PublicReasonCode
    safe_message: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    component: Literal["contract", "coordinator", "budget", "model", "quality", "journal"]
    retry_classification: Literal["none", "transient", "terminal"] = "none"
    field_violations: tuple[FieldViolation, ...] = ()

    @field_validator("domain_error_id", "request_id")
    @classmethod
    def validate_occurrence_id(cls, value: UUID | None) -> UUID | None:
        """Require generated domain identifiers to be UUIDv7."""
        if value is not None and value.version != 7:
            raise ValueError("domain identifiers must be UUIDv7 values")
        return value


class InvalidParameter(ContractModel):
    """RFC 9457 extension entry for one invalid request field."""

    path: Annotated[str, StringConstraints(pattern=r"^/")]
    reason: PublicReasonCode
    message: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class ProblemDetails(ContractModel):
    """Framework-neutral RFC 9457 problem details document."""

    type: Annotated[str, StringConstraints(pattern=r"^https://")]
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    status: int = Field(ge=400, le=599)
    detail: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    instance: Annotated[str, StringConstraints(pattern=r"^/")]
    request_id: UUID | None = None
    public_reason_code: PublicReasonCode
    invalid_params: tuple[InvalidParameter, ...] = ()


def parse_public_request_json(payload: str | bytes | bytearray) -> PublicRequest:
    """Parse a request while rejecting duplicate JSON object member names."""
    import json

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON member: {key}")
            result[key] = value
        return result

    document = json.loads(payload, object_pairs_hook=reject_duplicates)
    return PublicRequest.model_validate(document)
