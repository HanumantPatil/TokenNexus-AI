"""Atomic in-memory economics adapters and policy administration."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from threading import RLock

from tokennexus.contracts import (
    BudgetReservation,
    PolicyAuditEvent,
    PolicyChangeCommand,
    PolicySnapshot,
    ReservationRequest,
)
from tokennexus.ports import Clock, IdSource, PolicyStore


class InMemoryBudgetLedger:
    """Atomically reserve configured multidimensional request allowances."""

    def __init__(
        self,
        *,
        maximum_cost: str = "1000",
        maximum_input_tokens: int = 1_000_000,
        maximum_output_tokens: int = 100_000,
        maximum_duration_ms: int = 300_000,
        maximum_tool_calls: int = 100,
    ) -> None:
        self._limits = (
            Decimal(maximum_cost),
            maximum_input_tokens,
            maximum_output_tokens,
            maximum_duration_ms,
            maximum_tool_calls,
        )
        self._reservations: list[BudgetReservation] = []
        self._lock = RLock()

    @property
    def reservations(self) -> tuple[BudgetReservation, ...]:
        """Return immutable reservation evidence in append order."""
        with self._lock:
            return tuple(self._reservations)

    def reserve(self, request: ReservationRequest) -> BudgetReservation | None:
        """Reserve all dimensions atomically when aggregate limits permit them."""
        with self._lock:
            if any(
                receipt.request.reservation_id == request.reservation_id
                for receipt in self._reservations
            ):
                raise ValueError("reservation_id must be unique")
            totals = (
                sum(
                    (Decimal(item.request.estimated_cost.amount) for item in self._reservations),
                    Decimal(0),
                )
                + Decimal(request.estimated_cost.amount),
                sum(item.request.input_tokens for item in self._reservations)
                + request.input_tokens,
                sum(item.request.output_tokens for item in self._reservations)
                + request.output_tokens,
                sum(item.request.duration_ms for item in self._reservations)
                + request.duration_ms,
                sum(item.request.tool_calls for item in self._reservations)
                + request.tool_calls,
            )
            if any(total > limit for total, limit in zip(totals, self._limits, strict=True)):
                return None
            receipt = BudgetReservation(request=request)
            self._reservations.append(receipt)
            return receipt


class InMemoryPolicyStore:
    """Lock-protected immutable policy history and audit journal."""

    def __init__(self, initial: PolicySnapshot) -> None:
        self._history = {initial.policy_version: initial}
        self._active_version = initial.policy_version
        self._audit_events: list[PolicyAuditEvent] = []
        self._lock = RLock()

    @property
    def versions(self) -> tuple[PolicySnapshot, ...]:
        """Return approved snapshots in insertion order."""
        with self._lock:
            return tuple(self._history.values())

    @property
    def audit_events(self) -> tuple[PolicyAuditEvent, ...]:
        """Return append-only administration audit evidence."""
        with self._lock:
            return tuple(self._audit_events)

    def active(self) -> PolicySnapshot:
        """Return the current immutable policy snapshot."""
        with self._lock:
            return self._history[self._active_version]

    def get(self, policy_version: str) -> PolicySnapshot | None:
        """Return one approved immutable snapshot."""
        with self._lock:
            return self._history.get(policy_version)

    def transition(
        self,
        *,
        expected_active_version: str,
        snapshot: PolicySnapshot,
        audit_event: PolicyAuditEvent,
    ) -> bool:
        """Apply one unique version and its audit record as one transaction."""
        with self._lock:
            if self._active_version != expected_active_version:
                return False
            if snapshot.policy_version in self._history:
                return False
            self._history[snapshot.policy_version] = snapshot
            self._active_version = snapshot.policy_version
            self._audit_events.append(audit_event)
            return True

    def record_audit(self, audit_event: PolicyAuditEvent) -> None:
        """Append a denied, invalid, or conflicting administration attempt."""
        with self._lock:
            self._audit_events.append(audit_event)


class PolicyAdministrationService:
    """Authorize, confirm, validate, and audit immutable policy transitions."""

    def __init__(self, *, store: PolicyStore, clock: Clock, ids: IdSource) -> None:
        self._store = store
        self._clock = clock
        self._ids = ids

    def update(
        self,
        command: PolicyChangeCommand,
        *,
        actor_id: str,
        actor_roles: frozenset[str],
    ) -> bool:
        """Apply an authorized, confirmed, valid optimistic policy update."""
        active = self._store.active()
        if "policy_admin" not in actor_roles:
            self._audit(
                "update",
                actor_id,
                active.policy_version,
                "denied",
                "policy.unauthorized",
            )
            return False
        if not command.confirmed:
            self._audit(
                "update",
                actor_id,
                active.policy_version,
                "denied",
                "policy.confirmation_required",
            )
            return False
        event = self._event(
            action="update",
            actor_id=actor_id,
            previous_version=active.policy_version,
            outcome="applied",
            resulting_version=command.proposed_policy.policy_version,
            reason="policy.updated",
        )
        applied = self._store.transition(
            expected_active_version=command.expected_active_version,
            snapshot=command.proposed_policy,
            audit_event=event,
        )
        if not applied:
            self._audit(
                "update",
                actor_id,
                active.policy_version,
                "conflict",
                "policy.version_conflict",
            )
        return applied

    def rollback(
        self,
        *,
        expected_active_version: str,
        source_version: str,
        new_version: str,
        confirmed: bool,
        actor_id: str,
        actor_roles: frozenset[str],
    ) -> bool:
        """Clone a prior approved policy into a new auditable version."""
        active = self._store.active()
        source = self._store.get(source_version)
        if "policy_admin" not in actor_roles:
            self._audit(
                "rollback",
                actor_id,
                active.policy_version,
                "denied",
                "policy.unauthorized",
                source_version,
            )
            return False
        if not confirmed:
            self._audit(
                "rollback",
                actor_id,
                active.policy_version,
                "denied",
                "policy.confirmation_required",
                source_version,
            )
            return False
        if source is None or source_version == active.policy_version:
            self._audit(
                "rollback",
                actor_id,
                active.policy_version,
                "invalid",
                "policy.invalid_change",
                source_version,
            )
            return False
        snapshot = source.model_copy(update={"policy_version": new_version})
        event = self._event(
            action="rollback",
            actor_id=actor_id,
            previous_version=active.policy_version,
            source_version=source_version,
            outcome="applied",
            resulting_version=new_version,
            reason="policy.rolled_back",
        )
        applied = self._store.transition(
            expected_active_version=expected_active_version,
            snapshot=snapshot,
            audit_event=event,
        )
        if not applied:
            self._audit(
                "rollback",
                actor_id,
                active.policy_version,
                "conflict",
                "policy.version_conflict",
                source_version,
            )
        return applied

    def _audit(
        self,
        action: str,
        actor_id: str,
        previous_version: str,
        outcome: str,
        reason: str,
        source_version: str | None = None,
    ) -> None:
        self._store.record_audit(
            self._event(
                action=action,
                actor_id=actor_id,
                previous_version=previous_version,
                source_version=source_version,
                outcome=outcome,
                reason=reason,
            )
        )

    def _event(
        self,
        *,
        action: str,
        actor_id: str,
        previous_version: str,
        outcome: str,
        reason: str,
        source_version: str | None = None,
        resulting_version: str | None = None,
    ) -> PolicyAuditEvent:
        timestamp = (
            self._clock.utc_now()
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        return PolicyAuditEvent(
            event_id=self._ids.new(),
            action=action,
            actor_id_hash=f"sha256:{sha256(actor_id.encode('utf-8')).hexdigest()}",
            outcome=outcome,
            previous_version=previous_version,
            source_version=source_version,
            resulting_version=resulting_version,
            public_reason_code=reason,
            recorded_at_utc=timestamp,
        )