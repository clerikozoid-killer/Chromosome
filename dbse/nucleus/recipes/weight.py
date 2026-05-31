"""Weight force: F = m * g near Earth's surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.steps import build_weight_steps


@dataclass(frozen=True, slots=True)
class RecipeResult:
    value: float
    unit: str
    symbolic: str
    numeric_steps: list[dict[str, Any]]
    solver_path: list[str]


def solve_weight_force(*, mass_kg: float, g: float = STANDARD_GRAVITY) -> RecipeResult:
    """Compute gravitational force on a body of known mass."""
    if mass_kg <= 0.0:
        raise NucleusError("mass must be positive for weight force")
    m_sym, g_sym = sp.symbols("m g")
    expr = m_sym * g_sym
    numeric = float(expr.subs({m_sym: mass_kg, g_sym: g}))
    steps = build_weight_steps(mass_kg=mass_kg, g=g, result=numeric)
    return RecipeResult(
        value=numeric,
        unit="N",
        symbolic="m * g",
        numeric_steps=steps,
        solver_path=["recipe:weight_force", "sympy:symbolic", "sympy:numeric"],
    )
