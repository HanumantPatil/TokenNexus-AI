"""Pure deterministic routing and request-budget policy evaluation."""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal

from tokennexus.contracts import (
    CandidateEstimate,
    EligibilityGate,
    ModelAlias,
    ModelPolicy,
    Money,
    NormalizedRequest,
    PolicySnapshot,
    RouteBudgetDecision,
)

_COST_QUANTUM = Decimal("0.000001")


def pilot_policy() -> PolicySnapshot:
    """Return the frozen local policy that preserves routine economical routing."""
    return PolicySnapshot(
        policy_version="pilot-1",
        pricing_version="pilot-pricing-1",
        models=(
            ModelPolicy(
                alias="economical",
                supported_criticalities=("standard", "high"),
                maximum_supported_quality="4",
                minimum_latency_ms=100,
                input_cost_per_1000_tokens="0.001",
                output_cost_per_1000_tokens="0.002",
            ),
            ModelPolicy(
                alias="capable",
                supported_criticalities=("standard", "high", "critical"),
                maximum_supported_quality="5",
                minimum_latency_ms=300,
                input_cost_per_1000_tokens="0.002",
                output_cost_per_1000_tokens="0.004",
            ),
        ),
    )


class PolicyEvaluator:
    """Choose the lowest-cost eligible path under one frozen policy snapshot."""

    def evaluate(
        self,
        snapshot: PolicySnapshot,
        request: NormalizedRequest,
    ) -> RouteBudgetDecision:
        """Evaluate routing and budget without invoking an external dependency."""
        candidates = tuple(self._candidate(model, request) for model in snapshot.models)
        eligible = tuple(
            candidate
            for candidate in candidates
            if self._passes_non_budget_gates(candidate)
        )
        preferred_alias = self._preferred_alias(snapshot, request)
        preferred = next(
            (candidate for candidate in eligible if candidate.model_alias == preferred_alias),
            None,
        )
        funded = tuple(
            candidate
            for candidate in eligible
            if self._gate_passes(candidate, "budget")
        )

        selected = (
            preferred
            if preferred is not None and self._gate_passes(preferred, "budget")
            else None
        )
        action = "allow"
        if selected is None and funded:
            selected = min(funded, key=self._cost)
            action = (
                "downgrade" if selected.model_alias != preferred_alias else "allow"
            )
        if selected is None:
            action = (
                "approval_required" if snapshot.approval_required_when_unfunded else "block"
            )
            reasons = ("budget.approval_required",) if action == "approval_required" else (
                "budget.limit_exceeded",
            )
            gates = (
                preferred.eligibility_gates
                if preferred is not None
                else self._failed_gates(candidates)
            )
            return RouteBudgetDecision(
                policy_version=snapshot.policy_version,
                pricing_version=snapshot.pricing_version,
                budget_action=action,
                candidate_estimates=candidates,
                eligibility_gates=gates,
                public_reason_codes=reasons,
            )

        route_reason = (
            "route.economical_eligible"
            if selected.model_alias == "economical"
            else "route.capable_required"
        )
        budget_reason = "budget.downgraded" if action == "downgrade" else "budget.within_limit"
        return RouteBudgetDecision(
            policy_version=snapshot.policy_version,
            pricing_version=snapshot.pricing_version,
            selected_model_alias=selected.model_alias,
            budget_action=action,
            candidate_estimates=candidates,
            selected_estimate=selected.estimated_cost,
            eligibility_gates=selected.eligibility_gates,
            public_reason_codes=(budget_reason, route_reason),
        )

    def _candidate(
        self,
        model: ModelPolicy,
        request: NormalizedRequest,
    ) -> CandidateEstimate:
        constraints = request.effective_constraints
        estimate = self._estimate(model, request)
        gates = (
            EligibilityGate(
                gate="availability",
                outcome="passed" if model.enabled else "failed",
            ),
            EligibilityGate(
                gate="budget",
                outcome=(
                    "passed"
                    if Decimal(estimate.amount) <= Decimal(constraints.maximum_budget.amount)
                    else "failed"
                ),
            ),
            EligibilityGate(
                gate="governance",
                outcome=(
                    "passed"
                    if constraints.criticality in model.supported_criticalities
                    else "failed"
                ),
            ),
            EligibilityGate(
                gate="latency",
                outcome=(
                    "passed"
                    if constraints.maximum_latency_ms >= model.minimum_latency_ms
                    else "failed"
                ),
            ),
            EligibilityGate(
                gate="quality",
                outcome=(
                    "passed"
                    if Decimal(constraints.minimum_quality)
                    <= Decimal(model.maximum_supported_quality)
                    else "failed"
                ),
            ),
        )
        return CandidateEstimate(
            model_alias=model.alias,
            estimated_cost=estimate,
            eligibility_gates=gates,
        )

    def _estimate(self, model: ModelPolicy, request: NormalizedRequest) -> Money:
        constraints = request.effective_constraints
        amount = (
            Decimal(constraints.maximum_input_tokens)
            * Decimal(model.input_cost_per_1000_tokens)
            / Decimal(1000)
            + Decimal(constraints.maximum_output_tokens)
            * Decimal(model.output_cost_per_1000_tokens)
            / Decimal(1000)
        ).quantize(_COST_QUANTUM, rounding=ROUND_CEILING)
        canonical = format(amount, "f").rstrip("0").rstrip(".") or "0"
        return Money(amount=canonical)

    @staticmethod
    def _preferred_alias(
        snapshot: PolicySnapshot,
        request: NormalizedRequest,
    ) -> ModelAlias:
        constraints = request.effective_constraints
        if constraints.criticality in snapshot.capable_preferred_criticalities:
            return "capable"
        economical = next(model for model in snapshot.models if model.alias == "economical")
        if Decimal(constraints.minimum_quality) > Decimal(economical.maximum_supported_quality):
            return "capable"
        return "economical"

    @staticmethod
    def _gate_passes(candidate: CandidateEstimate, gate_name: str) -> bool:
        return any(
            gate.gate == gate_name and gate.outcome == "passed"
            for gate in candidate.eligibility_gates
        )

    def _passes_non_budget_gates(self, candidate: CandidateEstimate) -> bool:
        return all(
            gate.outcome == "passed"
            for gate in candidate.eligibility_gates
            if gate.gate != "budget"
        )

    @staticmethod
    def _cost(candidate: CandidateEstimate) -> Decimal:
        return Decimal(candidate.estimated_cost.amount)

    @staticmethod
    def _failed_gates(candidates: tuple[CandidateEstimate, ...]) -> tuple[EligibilityGate, ...]:
        for candidate in candidates:
            if any(gate.outcome == "failed" for gate in candidate.eligibility_gates):
                return candidate.eligibility_gates
        return candidates[0].eligibility_gates