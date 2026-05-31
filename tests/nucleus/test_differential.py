"""L5 differential tests: SymPy vs independent numeric paths (QA level 3)."""

from __future__ import annotations

import sympy as sp
from scipy.constants import g as scipy_g

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.recipes.weight import solve_weight_force


def test_weight_force_sympy_matches_direct_float() -> None:
    mass = 0.1
    direct = mass * STANDARD_GRAVITY
    recipe = solve_weight_force(mass_kg=mass)
    assert recipe.value == direct


def test_weight_force_sympy_matches_scipy_constant() -> None:
    mass = 0.25
    m, g = sp.symbols("m g")
    expr = (m * g).subs({m: mass, g: scipy_g})
    recipe = solve_weight_force(mass_kg=mass, g=float(scipy_g))
    assert float(expr) == recipe.value
