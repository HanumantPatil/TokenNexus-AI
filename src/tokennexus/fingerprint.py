"""Normalized request projection and RFC 8785 request fingerprints."""

from __future__ import annotations

import hashlib
import unicodedata
from typing import TypeAlias
from uuid import UUID

import rfc8785

from tokennexus.contracts import NormalizedRequest, PublicRequest
from tokennexus.ids import new_uuid7

FINGERPRINT_PROFILE = "tokennexus-request-fingerprint-v1"
JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


def normalize_request(
    request: PublicRequest,
    *,
    scope_id: str,
    request_id: UUID | None = None,
    authorization_context_fingerprint: str | None = None,
) -> NormalizedRequest:
    """Materialize the immutable server-owned request used for fingerprinting."""
    normalized_context = tuple(
        item.model_copy(update={"context_id": unicodedata.normalize("NFC", item.context_id)})
        for item in request.task.mandatory_context
    )
    normalized_task = request.task.model_copy(update={"mandatory_context": normalized_context})
    return NormalizedRequest(
        request_id=request_id or new_uuid7(),
        scope_id=unicodedata.normalize("NFC", scope_id),
        application_id=unicodedata.normalize("NFC", request.application_id),
        task=normalized_task,
        effective_constraints=request.constraints,
        cache_directives=request.cache_directives,
        authorization_context_fingerprint=authorization_context_fingerprint,
    )


def normalized_request_projection(request: NormalizedRequest) -> dict[str, JsonValue]:
    """Build the closed semantic projection, excluding generated and mutable fields."""
    projection: dict[str, JsonValue] = {
        "fingerprint_profile": FINGERPRINT_PROFILE,
        "public_contract_major": 1,
        "scope_id": request.scope_id,
        "application_id": request.application_id,
        "task": request.task.model_dump(mode="json"),
        "effective_constraints": request.effective_constraints.model_dump(mode="json"),
        "cache_directives": request.cache_directives.model_dump(mode="json"),
    }
    if request.authorization_context_fingerprint is not None:
        projection["authorization_context_fingerprint"] = request.authorization_context_fingerprint
    return projection


def canonical_request_bytes(request: NormalizedRequest) -> bytes:
    """Serialize the semantic request projection with RFC 8785 JCS."""
    return rfc8785.dumps(normalized_request_projection(request))


def request_fingerprint(request: NormalizedRequest) -> str:
    """Return a lowercase SHA-256 fingerprint over canonical request bytes."""
    digest = hashlib.sha256(canonical_request_bytes(request)).hexdigest()
    return f"sha256:{digest}"
