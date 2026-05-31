"""Evaluate Cytoplasm invariant expressions against state."""

from __future__ import annotations

from dbse.contracts.domain import Invariant
from dbse.nucleus.errors import NucleusError


def evaluate_invariant(inv: Invariant, state: dict[str, float]) -> float:
    """MVP: return the LHS variable value for 'v < c' style invariants."""
    expr = inv.expression.replace(" ", "")
    if expr.startswith("v<"):
        return state.get("v", state.get("V", 0.0))
    raise NucleusError(f"Unsupported invariant expression: {inv.expression!r}")
