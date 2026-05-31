"""L5 unit tests: weight force recipe F = m * g."""

from __future__ import annotations

import pytest

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.recipes.weight import solve_weight_force


def test_weight_force_apple_100g() -> None:
    result = solve_weight_force(mass_kg=0.1, g=STANDARD_GRAVITY)
    assert result.symbolic == "m * g"
    assert result.unit == "N"
    assert result.value == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-9)
    assert "sympy:symbolic" in result.solver_path
    assert "sympy:numeric" in result.solver_path
    assert len(result.numeric_steps) == 3


def test_weight_force_requires_positive_mass() -> None:
    with pytest.raises(NucleusError):
        solve_weight_force(mass_kg=0.0)
