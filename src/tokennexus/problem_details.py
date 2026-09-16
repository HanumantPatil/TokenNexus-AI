"""Safe framework-neutral RFC 9457 problem detail mapping."""

from __future__ import annotations

from uuid import UUID

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from tokennexus.contracts import DomainError, FieldViolation, InvalidParameter, ProblemDetails
from tokennexus.ids import new_uuid7
from tokennexus.reasons import PUBLIC_REASON_REGISTRY

PROBLEM_BASE_URI = "https://tokennexus.example/problems"


def _json_pointer(location: tuple[int | str, ...]) -> str:
    escaped = (str(part).replace("~", "~0").replace("/", "~1") for part in location)
    return "/" + "/".join(escaped)


def _safe_validation_message(error: ErrorDetails) -> str:
    error_type = error["type"]
    if error_type == "missing":
        return "This field is required."
    if error_type == "extra_forbidden":
        return "This field is not allowed."
    if error_type in {"literal_error", "enum"}:
        return "This value is not supported."
    if error_type.endswith("_type"):
        return "This value has the wrong type."
    if error_type in {"string_too_short", "too_short"}:
        return "This value must not be empty."
    return "This value does not satisfy the contract."


def domain_error_from_validation(
    error: ValidationError,
    *,
    occurrence_id: UUID | None = None,
    request_id: UUID | None = None,
) -> DomainError:
    """Convert Pydantic failures into a safe transport-neutral domain error."""
    violations: list[FieldViolation] = []
    for item in error.errors(include_url=False, include_context=False, include_input=False):
        reason = (
            "request.constraint_invalid"
            if item["loc"][:1] == ("constraints",)
            else "request.invalid"
        )
        violations.append(
            FieldViolation(
                path=_json_pointer(item["loc"]),
                public_reason_code=reason,
                safe_message=_safe_validation_message(item),
            )
        )
    return DomainError(
        domain_error_id=occurrence_id or new_uuid7(),
        request_id=request_id,
        public_reason_code="request.invalid",
        safe_message="The request does not satisfy the public contract.",
        component="contract",
        field_violations=tuple(violations),
    )


def problem_details_from_domain_error(error: DomainError, *, status: int = 400) -> ProblemDetails:
    """Map a safe domain error to an RFC 9457 problem details document."""
    definition = PUBLIC_REASON_REGISTRY[error.public_reason_code]
    instance_prefix = f"/requests/{error.request_id}" if error.request_id is not None else ""
    return ProblemDetails(
        type=f"{PROBLEM_BASE_URI}/{error.public_reason_code.replace('.', '-')}",
        title=definition.safe_title,
        status=status,
        detail=error.safe_message,
        instance=f"{instance_prefix}/errors/{error.domain_error_id}",
        request_id=error.request_id,
        public_reason_code=error.public_reason_code,
        invalid_params=tuple(
            InvalidParameter(
                path=violation.path,
                reason=violation.public_reason_code,
                message=violation.safe_message,
            )
            for violation in error.field_violations
        ),
    )