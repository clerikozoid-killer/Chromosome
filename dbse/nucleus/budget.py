"""Wall-clock budget for Z3 verification."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Z3Budget:
    ms: int = 100


class Z3BudgetExceeded(TimeoutError):
    """Raised when Z3 or wrapper exceeds the wall-clock budget."""


def verify_with_budget(fn: Callable[[], bool], *, budget: Z3Budget) -> tuple[bool, list[str]]:
    start = time.perf_counter()
    try:
        ok = fn()
    except Exception:
        return False, ["z3:error"]
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms > budget.ms:
        return False, ["z3:timeout"]
    return ok, ["z3:ok"] if ok else ["z3:fail"]
