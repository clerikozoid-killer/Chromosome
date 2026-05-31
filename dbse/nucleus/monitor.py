"""Continuous invariant monitor for ODE integration steps."""

from __future__ import annotations

from dbse.contracts.domain import Invariant
from dbse.contracts.proof import Severity, Violation
from dbse.nucleus.invariants import evaluate_invariant


class ContinuousInvariantMonitor:
    def __init__(self, invariants: list[Invariant]) -> None:
        self.invariants = invariants
        self.violations: list[Violation] = []

    def check_invariants(self, t: float, state: dict[str, float]) -> bool:
        for inv in self.invariants:
            value = evaluate_invariant(inv, state)
            if not _satisfies(inv, value):
                self.violations.append(
                    Violation(
                        invariant=inv.name,
                        severity=inv.severity,
                        time=t,
                        value=value,
                        threshold=inv.threshold,
                        message=f"{inv.name} violated at t={t}",
                    )
                )
                if inv.severity is Severity.CRITICAL:
                    return False
        return True


def _satisfies(inv: Invariant, value: float) -> bool:
    if inv.threshold is None:
        return True
    return value < inv.threshold
