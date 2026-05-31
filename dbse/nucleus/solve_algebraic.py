"""Algebraic solve entry point (Stage 6 MVP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dbse.contracts.context import PipelineContext
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.recipes.weight import RecipeResult, solve_weight_force
from dbse.nucleus.select_solver import SolverKind, select_solver


@dataclass(frozen=True, slots=True)
class AlgebraicResult:
    value: float
    unit: str
    symbolic: str
    numeric_steps: list[dict[str, Any]]
    solver_path: list[str]


def _from_recipe(recipe: RecipeResult) -> AlgebraicResult:
    return AlgebraicResult(
        value=recipe.value,
        unit=recipe.unit,
        symbolic=recipe.symbolic,
        numeric_steps=recipe.numeric_steps,
        solver_path=list(recipe.solver_path),
    )


def solve_algebraic(ctx: PipelineContext) -> AlgebraicResult:
    """Dispatch algebraic solve based on AST class and membrane target."""
    if ctx.ast is None:
        raise NucleusError("AST required for algebraic solve")
    if ctx.membrane is None:
        raise NucleusError("MEMBRANE required for algebraic solve")
    kind = select_solver(ctx.ast)
    if kind is SolverKind.ODE:
        raise NucleusError("ODE solve requires layer ODE path")
    target = ctx.membrane.get("target") or {}
    target_prop = str(target.get("property", ""))
    quantities = membrane_quantities_si(ctx.membrane)
    g = float(ctx.config.get("gravity", STANDARD_GRAVITY))
    if target_prop == "force" and "mass" in quantities:
        return _from_recipe(solve_weight_force(mass_kg=quantities["mass"], g=g))
    raise NucleusError(
        f"No algebraic recipe for target={target_prop!r} with quantities={list(quantities)}"
    )
