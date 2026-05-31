"""Budgeted Z3 verification (MVP: weight force)."""

from __future__ import annotations

import z3

from dbse.nucleus.budget import Z3Budget, verify_with_budget

__all__ = ["verify_weight_force", "verify_with_budget"]


def verify_weight_force(
    *,
    mass: float,
    g: float,
    force: float,
    budget_ms: int = 100,
    tol: float = 1e-6,
) -> tuple[bool, list[str]]:
    def _check() -> bool:
        m, g_sym, f = z3.Reals("m g f")
        s = z3.Solver()
        s.set("timeout", budget_ms)
        s.add(m == mass, g_sym == g, f == force)
        s.add(f >= m * g_sym - tol)
        s.add(f <= m * g_sym + tol)
        return bool(s.check() == z3.sat)

    return verify_with_budget(_check, budget=Z3Budget(ms=budget_ms))
