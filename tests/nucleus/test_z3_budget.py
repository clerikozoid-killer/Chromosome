"""Z3 budget tests."""

from __future__ import annotations

from dbse.nucleus.budget import Z3Budget
from dbse.nucleus.z3_verify import verify_weight_force


def test_verify_weight_force_succeeds() -> None:
    ok, steps = verify_weight_force(mass=0.1, g=9.80665, force=0.980665, budget_ms=500)
    assert ok is True
    assert steps


def test_budget_exceeded_on_pathological() -> None:
    budget = Z3Budget(ms=1)
    from dbse.nucleus.z3_verify import verify_with_budget

    def slow() -> bool:
        import time

        time.sleep(0.05)
        return True

    ok, _ = verify_with_budget(slow, budget=budget)
    assert ok is False
