"""Deterministic synchronous coordinator for governed model execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from tokennexus.contracts import (
    BudgetReservation,
    DecisionSummary,
    EscalationStatus,
    ModelAlias,
    Money,
    Output,
    PublicError,
    PublicRequest,
    PublicResult,
    QualitySummary,
    ReservationRequest,
    RouteBudgetDecision,
    Usage,
)
from tokennexus.economics import InMemoryPolicyStore
from tokennexus.fingerprint import normalize_request, request_fingerprint
from tokennexus.journal import ClaimStatus, Journal
from tokennexus.policy import PolicyEvaluator, pilot_policy
from tokennexus.ports import (
    BudgetPort,
    CancellationPort,
    Clock,
    IdSource,
    ModelInvocation,
    ModelOutcome,
    ModelOutcomeStatus,
    ModelPort,
    PolicyStore,
    QualityEvaluator,
    TransientDependencyError,
)
from tokennexus.reasons import PUBLIC_REASON_REGISTRY, PublicStatus
from tokennexus.state import (
    RunState,
    approve_escalation,
    begin_attempt,
    consume_transient_retry,
    record_dispatch,
    record_model_success,
    record_quality,
    record_reservation,
)


@dataclass(frozen=True, slots=True)
class _AttemptExecution:
    state: RunState
    outcome: ModelOutcome | None = None
    terminal_result: PublicResult | None = None
    budget_denied: bool = False


@dataclass(frozen=True, slots=True)
class _QualityExecution:
    state: RunState
    quality: QualitySummary | None = None
    terminal_result: PublicResult | None = None


class Coordinator:
    """Own request admission, bounded work, and every terminal transition."""

    def __init__(
        self,
        *,
        journal: Journal,
        budget: BudgetPort,
        model: ModelPort,
        quality: QualityEvaluator,
        cancellation: CancellationPort,
        clock: Clock,
        ids: IdSource,
        policy_store: PolicyStore | None = None,
        policy_evaluator: PolicyEvaluator | None = None,
    ) -> None:
        self._journal = journal
        self._budget = budget
        self._model = model
        self._quality = quality
        self._cancellation = cancellation
        self._clock = clock
        self._ids = ids
        self._policy_store = policy_store or InMemoryPolicyStore(pilot_policy())
        self._policy_evaluator = policy_evaluator or PolicyEvaluator()

    def execute(self, request: PublicRequest, *, scope_id: str) -> PublicResult:
        """Execute a request once or return its exact stored terminal replay."""
        started_at = self._clock.now()
        normalized = normalize_request(request, scope_id=scope_id, request_id=self._ids.new())
        fingerprint = request_fingerprint(normalized)
        deadline = started_at + request.constraints.maximum_latency_ms / 1_000
        policy_snapshot = self._policy_store.active()
        route_decision = self._policy_evaluator.evaluate(policy_snapshot, normalized)
        initial = RunState(
            request=normalized,
            fingerprint=fingerprint,
            deadline=deadline,
            policy_snapshot=policy_snapshot,
            route_decision=route_decision,
        )
        claim = self._journal.claim(
            scope_id=scope_id,
            idempotency_key=request.idempotency_key,
            fingerprint=fingerprint,
            initial_state=initial,
        )
        if claim.status == ClaimStatus.CONFLICT:
            return self._result(
                initial,
                status=PublicStatus.CONFLICT,
                started_at=started_at,
                reasons=("request.idempotency_conflict",),
            )
        if claim.status == ClaimStatus.REPLAY:
            if claim.state.terminal_result is not None:
                return claim.state.terminal_result
            current = self._journal.read(
                scope_id=scope_id,
                idempotency_key=request.idempotency_key,
            )
            if current is not None and current.terminal_result is not None:
                return current.terminal_result
            return self._result(
                claim.state,
                status=PublicStatus.IN_PROGRESS,
                started_at=started_at,
                reasons=("request.in_progress",),
            )

        state = claim.state
        guarded = self._guard(state, request.idempotency_key, started_at)
        if guarded is not None:
            return guarded

        decision = self._require_route_decision(state)
        if decision.selected_model_alias is None:
            return self._finish(
                state,
                request.idempotency_key,
                self._result(
                    state,
                    status=PublicStatus.BLOCKED,
                    started_at=started_at,
                    reasons=decision.public_reason_codes,
                ),
            )
        first_alias = decision.selected_model_alias

        first = self._execute_attempt(
            state,
            request.idempotency_key,
            started_at,
            model_alias=first_alias,
            parent_attempt_id=None,
        )
        if first.terminal_result is not None:
            return first.terminal_result
        if first.budget_denied:
            return self._finish(
                first.state,
                request.idempotency_key,
                self._result(
                    first.state,
                    status=PublicStatus.BLOCKED,
                    started_at=started_at,
                    reasons=("budget.limit_exceeded",),
                ),
            )
        state = first.state
        outcome = self._require_success(first.outcome)
        quality_execution = self._evaluate_quality(
            state,
            request.idempotency_key,
            started_at,
            outcome.output,
        )
        if quality_execution.terminal_result is not None:
            return quality_execution.terminal_result
        state = quality_execution.state
        quality = quality_execution.quality
        if quality is None:
            return self._finish(
                state,
                request.idempotency_key,
                self._result(
                    state,
                    status=PublicStatus.DEGRADED,
                    started_at=started_at,
                    output=outcome.output,
                    model_alias=first_alias,
                    quality=QualitySummary(
                        status="unavailable",
                        threshold=request.constraints.minimum_quality,
                    ),
                    reasons=("quality.evaluation_unavailable",),
                ),
            )
        if quality.status == "passed":
            return self._finish_success(
                state,
                request.idempotency_key,
                started_at,
                outcome.output,
                first_alias,
                quality,
                escalated=False,
            )

        if first_alias == "capable":
            return self._finish(
                state,
                request.idempotency_key,
                self._result(
                    state,
                    status=PublicStatus.QUALITY_UNMET,
                    started_at=started_at,
                    output=outcome.output,
                    model_alias="capable",
                    quality=quality,
                    reasons=(
                        "budget.within_limit",
                        "quality.threshold_unmet",
                        "route.capable_required",
                    ),
                ),
            )

        guarded = self._guard(state, request.idempotency_key, started_at)
        if guarded is not None:
            return guarded
        second = self._execute_attempt(
            state,
            request.idempotency_key,
            started_at,
            model_alias="capable",
            parent_attempt_id=state.attempts[-1].attempt_id,
        )
        if second.terminal_result is not None:
            return second.terminal_result
        if second.budget_denied:
            return self._finish(
                second.state,
                request.idempotency_key,
                self._result(
                    second.state,
                    status=PublicStatus.QUALITY_UNMET,
                    started_at=started_at,
                    output=outcome.output,
                    model_alias="economical",
                    quality=quality,
                    escalation_status="not_permitted",
                    reasons=(
                        "budget.limit_exceeded",
                        "escalation.not_permitted_budget",
                        "quality.threshold_unmet",
                    ),
                ),
            )

        state = second.state
        capable_outcome = self._require_success(second.outcome)
        capable_quality_execution = self._evaluate_quality(
            state,
            request.idempotency_key,
            started_at,
            capable_outcome.output,
        )
        if capable_quality_execution.terminal_result is not None:
            return capable_quality_execution.terminal_result
        state = capable_quality_execution.state
        capable_quality = capable_quality_execution.quality
        if capable_quality is None:
            return self._finish(
                state,
                request.idempotency_key,
                self._result(
                    state,
                    status=PublicStatus.DEGRADED,
                    started_at=started_at,
                    output=capable_outcome.output,
                    model_alias="capable",
                    quality=QualitySummary(
                        status="unavailable",
                        threshold=request.constraints.minimum_quality,
                    ),
                    escalation_status="performed",
                    reasons=("quality.evaluation_unavailable",),
                ),
            )
        if capable_quality.status == "passed":
            return self._finish_success(
                state,
                request.idempotency_key,
                started_at,
                capable_outcome.output,
                "capable",
                capable_quality,
                escalated=True,
            )
        return self._finish(
            state,
            request.idempotency_key,
            self._result(
                state,
                status=PublicStatus.QUALITY_UNMET,
                started_at=started_at,
                output=capable_outcome.output,
                model_alias="capable",
                quality=capable_quality,
                escalation_status="performed",
                reasons=(
                    "budget.within_limit",
                    "escalation.quality_triggered",
                    "quality.threshold_unmet",
                    "route.capable_required",
                ),
            ),
        )

    def _execute_attempt(
        self,
        state: RunState,
        idempotency_key: str,
        started_at: float,
        *,
        model_alias: ModelAlias,
        parent_attempt_id: UUID | None,
    ) -> _AttemptExecution:
        attempt_id = self._ids.new()
        operation_key = str(self._ids.new())
        estimate = self._model.estimate_cost(state.request, model_alias)
        receipt = self._reserve(
            state,
            operation_key=operation_key,
            dispatch_ordinal=1,
            estimated_cost=estimate,
        )
        if receipt is None:
            return _AttemptExecution(state=state, budget_denied=True)
        state = self._update(
            state,
            idempotency_key,
            record_reservation(state, receipt),
        )
        guarded = self._guard(state, idempotency_key, started_at)
        if guarded is not None:
            return _AttemptExecution(state=state, terminal_result=guarded)
        if parent_attempt_id is not None:
            state = self._update(state, idempotency_key, approve_escalation(state))
        state = self._update(
            state,
            idempotency_key,
            begin_attempt(
                state,
                attempt_id=attempt_id,
                operation_key=operation_key,
                model_alias=model_alias,
                parent_attempt_id=parent_attempt_id,
            ),
        )
        dispatch_ordinal = 0
        while True:
            dispatch_ordinal += 1
            state = self._update(state, idempotency_key, record_dispatch(state))
            outcome = self._model.invoke(
                ModelInvocation(
                    request=state.request,
                    attempt_id=attempt_id,
                    operation_key=operation_key,
                    dispatch_ordinal=dispatch_ordinal,
                    model_alias=model_alias,
                )
            )
            guarded = self._guard(state, idempotency_key, started_at)
            if guarded is not None:
                return _AttemptExecution(state=state, terminal_result=guarded)
            if outcome.status == ModelOutcomeStatus.SUCCEEDED:
                if outcome.usage is None:
                    raise ValueError("successful model outcome omitted usage")
                state = self._update(
                    state,
                    idempotency_key,
                    record_model_success(state, outcome.usage),
                )
                return _AttemptExecution(state=state, outcome=outcome)
            if outcome.status == ModelOutcomeStatus.TERMINAL_FAILURE:
                result = self._result(
                    state,
                    status=PublicStatus.FAILED,
                    started_at=started_at,
                    reasons=("system.controlled_failure",),
                )
                return _AttemptExecution(
                    state=state,
                    terminal_result=self._finish(state, idempotency_key, result),
                )
            if state.transient_retries_consumed >= 1:
                result = self._result(
                    state,
                    status=PublicStatus.FAILED,
                    started_at=started_at,
                    reasons=("dependency.model_unavailable",),
                )
                return _AttemptExecution(
                    state=state,
                    terminal_result=self._finish(state, idempotency_key, result),
                )
            state = self._update(state, idempotency_key, consume_transient_retry(state))
            guarded = self._guard(state, idempotency_key, started_at)
            if guarded is not None:
                return _AttemptExecution(state=state, terminal_result=guarded)
            receipt = self._reserve(
                state,
                operation_key=operation_key,
                dispatch_ordinal=dispatch_ordinal + 1,
                estimated_cost=estimate,
            )
            if receipt is None:
                result = self._result(
                    state,
                    status=PublicStatus.FAILED,
                    started_at=started_at,
                    reasons=("dependency.model_unavailable",),
                )
                return _AttemptExecution(
                    state=state,
                    terminal_result=self._finish(state, idempotency_key, result),
                )
            state = self._update(
                state,
                idempotency_key,
                record_reservation(state, receipt),
            )
            guarded = self._guard(state, idempotency_key, started_at)
            if guarded is not None:
                return _AttemptExecution(state=state, terminal_result=guarded)

    def _evaluate_quality(
        self,
        state: RunState,
        idempotency_key: str,
        started_at: float,
        output: Output | None,
    ) -> _QualityExecution:
        if output is None:
            raise ValueError("quality evaluation requires model output")
        operation_key = str(self._ids.new())
        estimate = self._quality.estimate_cost(state.request, output)
        dispatch_ordinal = 0
        while True:
            guarded = self._guard(state, idempotency_key, started_at)
            if guarded is not None:
                return _QualityExecution(state=state, terminal_result=guarded)
            dispatch_ordinal += 1
            receipt = self._reserve(
                state,
                operation_key=operation_key,
                dispatch_ordinal=dispatch_ordinal,
                estimated_cost=estimate,
            )
            if receipt is None:
                return _QualityExecution(state=state)
            state = self._update(
                state,
                idempotency_key,
                record_reservation(state, receipt),
            )
            guarded = self._guard(state, idempotency_key, started_at)
            if guarded is not None:
                return _QualityExecution(state=state, terminal_result=guarded)
            try:
                quality = self._quality.evaluate(state.request, output)
            except TransientDependencyError:
                if state.transient_retries_consumed >= 1:
                    return _QualityExecution(state=state)
                state = self._update(state, idempotency_key, consume_transient_retry(state))
                continue
            guarded = self._guard(state, idempotency_key, started_at)
            if guarded is not None:
                return _QualityExecution(state=state, terminal_result=guarded)
            state = self._update(state, idempotency_key, record_quality(state, quality))
            return _QualityExecution(state=state, quality=quality)

    def _reserve(
        self,
        state: RunState,
        *,
        operation_key: str,
        dispatch_ordinal: int,
        estimated_cost: Money,
    ) -> BudgetReservation | None:
        decision = self._require_route_decision(state)
        constraints = state.request.effective_constraints
        return self._budget.reserve(
            ReservationRequest(
                reservation_id=self._ids.new(),
                request_id=state.request.request_id,
                operation_key=operation_key,
                dispatch_ordinal=dispatch_ordinal,
                pricing_version=decision.pricing_version,
                estimated_cost=estimated_cost,
                input_tokens=constraints.maximum_input_tokens,
                output_tokens=constraints.maximum_output_tokens,
                duration_ms=constraints.maximum_latency_ms,
                tool_calls=constraints.maximum_tool_calls,
            )
        )

    def _guard(
        self,
        state: RunState,
        idempotency_key: str,
        started_at: float,
    ) -> PublicResult | None:
        if self._cancellation.is_cancelled(state.request.request_id):
            return self._finish(
                state,
                idempotency_key,
                self._result(
                    state,
                    status=PublicStatus.CANCELLED,
                    started_at=started_at,
                    reasons=("request.cancelled_by_client",),
                ),
            )
        if self._clock.now() >= state.deadline:
            return self._finish(
                state,
                idempotency_key,
                self._result(
                    state,
                    status=PublicStatus.TIMED_OUT,
                    started_at=started_at,
                    reasons=("request.deadline_exceeded",),
                ),
            )
        return None

    def _finish_success(
        self,
        state: RunState,
        idempotency_key: str,
        started_at: float,
        output: Output | None,
        model_alias: ModelAlias,
        quality: QualitySummary,
        *,
        escalated: bool,
    ) -> PublicResult:
        reasons = ["budget.within_limit", "quality.threshold_met"]
        reasons.append(
            "route.capable_required"
            if model_alias == "capable"
            else "route.economical_eligible"
        )
        if escalated:
            reasons.append("escalation.quality_triggered")
        result = self._result(
            state,
            status=PublicStatus.COMPLETED,
            started_at=started_at,
            output=output,
            model_alias=model_alias,
            quality=quality,
            escalation_status="performed" if escalated else "not_required",
            reasons=tuple(reasons),
        )
        return self._finish(state, idempotency_key, result)

    def _finish(
        self,
        state: RunState,
        idempotency_key: str,
        result: PublicResult,
    ) -> PublicResult:
        committed = self._journal.commit_terminal(
            scope_id=state.request.scope_id,
            idempotency_key=idempotency_key,
            expected_revision=state.revision,
            result=result,
        )
        if committed.terminal_result is None:
            raise RuntimeError("terminal journal commit did not store a result")
        return committed.terminal_result

    def _update(self, state: RunState, idempotency_key: str, updated: RunState) -> RunState:
        return self._journal.compare_and_set(
            scope_id=state.request.scope_id,
            idempotency_key=idempotency_key,
            expected_revision=state.revision,
            state=updated,
        )

    def _result(
        self,
        state: RunState,
        *,
        status: PublicStatus,
        started_at: float,
        reasons: tuple[str, ...],
        output: Output | None = None,
        model_alias: ModelAlias | None = None,
        quality: QualitySummary | None = None,
        escalation_status: EscalationStatus = "not_required",
    ) -> PublicResult:
        error = None
        output_statuses = {
            PublicStatus.COMPLETED,
            PublicStatus.DEGRADED,
            PublicStatus.QUALITY_UNMET,
        }
        if status not in output_statuses:
            definition = PUBLIC_REASON_REGISTRY[reasons[0]]
            error = PublicError(
                public_reason_code=reasons[0],
                safe_message=definition.safe_message,
            )
        return PublicResult(
            request_id=state.request.request_id,
            timestamp=self._canonical_timestamp(),
            status=status,
            output=output,
            error=error,
            decision_summary=DecisionSummary(
                model_alias=model_alias,
                policy_version=(
                    state.route_decision.policy_version
                    if state.route_decision is not None
                    else None
                ),
                pricing_version=(
                    state.route_decision.pricing_version
                    if state.route_decision is not None
                    else None
                ),
                budget_action=(
                    state.route_decision.budget_action
                    if state.route_decision is not None
                    else None
                ),
                estimated_cost=(
                    state.route_decision.selected_estimate
                    if state.route_decision is not None
                    else None
                ),
                eligibility_gates=(
                    state.route_decision.eligibility_gates
                    if state.route_decision is not None
                    else ()
                ),
                usage=self._total_usage(state),
                end_to_end_latency_ms=self._elapsed_ms(started_at),
                quality=quality,
                escalation_status=escalation_status,
                public_reason_codes=reasons,
            ),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return min(600_000, max(0, int((self._clock.now() - started_at) * 1_000)))

    def _canonical_timestamp(self) -> str:
        current = self._clock.utc_now()
        if current.utcoffset() != timedelta(0):
            raise ValueError("clock utc_now must return a timezone-aware UTC instant")
        return current.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def _require_success(outcome: ModelOutcome | None) -> ModelOutcome:
        if outcome is None or outcome.status != ModelOutcomeStatus.SUCCEEDED:
            raise RuntimeError("attempt execution did not produce a successful outcome")
        return outcome

    @staticmethod
    def _require_route_decision(state: RunState) -> RouteBudgetDecision:
        if state.route_decision is None:
            raise RuntimeError("run state omitted its frozen route decision")
        return state.route_decision

    @staticmethod
    def _total_usage(state: RunState) -> Usage | None:
        usages = tuple(attempt.usage for attempt in state.attempts if attempt.usage is not None)
        if not usages:
            return None
        total_cost = sum((Decimal(usage.estimated_cost.amount) for usage in usages), Decimal(0))
        amount = format(total_cost, "f").rstrip("0").rstrip(".") if total_cost else "0"
        return Usage(
            input_tokens=sum(usage.input_tokens for usage in usages),
            output_tokens=sum(usage.output_tokens for usage in usages),
            estimated_cost=Money(amount=amount),
            provider_latency_ms=sum(usage.provider_latency_ms for usage in usages),
            tool_call_count=sum(usage.tool_call_count for usage in usages),
        )