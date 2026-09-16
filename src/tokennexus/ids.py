"""UUIDv7 identifier generation and validation."""

from __future__ import annotations

import uuid
from uuid import UUID

from uuid6 import uuid7 as compatibility_uuid7


def new_uuid7() -> UUID:
    """Generate a UUIDv7 using the standard library when available."""
    standard_uuid7 = getattr(uuid, "uuid7", None)
    generated = standard_uuid7() if standard_uuid7 is not None else compatibility_uuid7()
    if generated.version != 7:
        raise RuntimeError("UUIDv7 source returned an incompatible identifier")
    return generated


def require_uuid7(value: UUID) -> UUID:
    """Return a UUIDv7 or reject an incompatible identifier."""
    if value.version != 7:
        raise ValueError("identifier must be UUIDv7")
    return value
