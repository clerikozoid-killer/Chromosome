"""L5 metamorphic tests: unit rescaling invariance (QA level 4)."""

from __future__ import annotations

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.recipes.weight import solve_weight_force


def test_mass_in_g_vs_kg_gives_same_force() -> None:
    membrane_g = {
        "quantities": [{"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"}]
    }
    membrane_kg = {
        "quantities": [{"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "kg"}]
    }
    m_g = membrane_quantities_si(membrane_g)["mass"]
    m_kg = membrane_quantities_si(membrane_kg)["mass"]
    f_g = solve_weight_force(mass_kg=m_g).value
    f_kg = solve_weight_force(mass_kg=m_kg).value
    assert f_g == f_kg
    assert f_g == 0.1 * STANDARD_GRAVITY


def test_force_scales_linearly_with_mass() -> None:
    f1 = solve_weight_force(mass_kg=0.1).value
    f2 = solve_weight_force(mass_kg=0.2).value
    assert f2 == 2.0 * f1
