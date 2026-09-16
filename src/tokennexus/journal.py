"""Atomic scoped idempotency journal protocol and in-memory implementation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from threading import RLock
from typing import Protocol

from tokennexus.contracts import PublicResult
from tokennexus.state import RunState, StateTransitionError, terminalize


class ClaimStatus(StrEnum):
    """Outcome of an atomic scope-and-key admission claim."""

    CREATED = "created"
    REPLAY = "replay"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class JournalClaim:
    """Immutable result of an idempotency claim."""

    status: ClaimStatus
    state: RunState


class JournalRevisionError(RuntimeError):
    """Raised when compare-and-set observes a stale run revision."""


class Journal(Protocol):
    """Persist run state with atomic admission and first-terminal-wins semantics."""

    def claim(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        fingerprint: str,
        initial_state: RunState,
    ) -> JournalClaim:
        """Atomically create or read one scope-and-key entry."""
        raise NotImplementedError

    def read(self, *, scope_id: str, idempotency_key: str) -> RunState | None:
        """Read the current immutable run state."""
        raise NotImplementedError

    def compare_and_set(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        expected_revision: int,
        state: RunState,
    ) -> RunState:
        """Replace active state only when the revision matches."""
        raise NotImplementedError

    def commit_terminal(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        expected_revision: int,
        result: PublicResult,
    ) -> RunState:
        """Commit the first terminal result or return the existing winner."""
        raise NotImplementedError


class InMemoryJournal:
    """Lock-protected journal preserving production atomicity semantics in tests."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], RunState] = {}
        self._lock = RLock()

    def claim(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        fingerprint: str,
        initial_state: RunState,
    ) -> JournalClaim:
        """Atomically claim a scoped key or classify its existing fingerprint."""
        key = (scope_id, idempotency_key)
        with self._lock:
            current = self._entries.get(key)
            if current is None:
                self._entries[key] = initial_state
                return JournalClaim(ClaimStatus.CREATED, initial_state)
            if current.fingerprint != fingerprint:
                return JournalClaim(ClaimStatus.CONFLICT, current)
            return JournalClaim(ClaimStatus.REPLAY, current)

    def read(self, *, scope_id: str, idempotency_key: str) -> RunState | None:
        """Read one state while holding the journal lock."""
        with self._lock:
            return self._entries.get((scope_id, idempotency_key))

    def compare_and_set(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        expected_revision: int,
        state: RunState,
    ) -> RunState:
        """Apply an active-state update with optimistic revision protection."""
        key = (scope_id, idempotency_key)
        with self._lock:
            current = self._require_entry(key)
            if current.is_terminal:
                raise StateTransitionError("terminal run state is immutable")
            if current.revision != expected_revision:
                raise JournalRevisionError(
                    f"expected revision {expected_revision}, found {current.revision}"
                )
            if state.request.request_id != current.request.request_id:
                raise StateTransitionError("replacement state belongs to another request")
            if state.fingerprint != current.fingerprint:
                raise StateTransitionError("replacement state changed the request fingerprint")
            updated = replace(state, revision=expected_revision + 1)
            self._entries[key] = updated
            return updated

    def commit_terminal(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        expected_revision: int,
        result: PublicResult,
    ) -> RunState:
        """Commit the first terminal result and preserve it for all later callers."""
        key = (scope_id, idempotency_key)
        with self._lock:
            current = self._require_entry(key)
            if current.is_terminal:
                return current
            if current.revision != expected_revision:
                raise JournalRevisionError(
                    f"expected revision {expected_revision}, found {current.revision}"
                )
            updated = replace(terminalize(current, result), revision=expected_revision + 1)
            self._entries[key] = updated
            return updated

    def _require_entry(self, key: tuple[str, str]) -> RunState:
        try:
            return self._entries[key]
        except KeyError as error:
            raise KeyError(f"journal entry does not exist for scope {key[0]!r}") from error