"""L4 unit tests: fluid_mechanics skeleton plugin."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.cytoplasm.plugins.fluid_mechanics import FluidMechanicsPlugin


def test_fluid_mechanics_selects_turbulent_at_high_reynolds() -> None:
    plugin = FluidMechanicsPlugin()
    model = plugin.select_model({"Reynolds": 5000.0, "Mach": 0.01})
    assert model.id == "turbulent_navier_stokes"


def test_fluid_mechanics_selects_compressible_at_high_mach() -> None:
    plugin = FluidMechanicsPlugin()
    model = plugin.select_model({"Reynolds": 100.0, "Mach": 0.5})
    assert model.id == "compressible_navier_stokes"


def test_fluid_mechanics_injects_continuity_constraint() -> None:
    plugin = FluidMechanicsPlugin()
    ctx = PipelineContext(query="q", membrane={"quantities": []})
    types = {c.constraint_type for c in plugin.inject_constraints(ctx)}
    assert "continuity" in types


def test_fluid_mechanics_computes_reynolds_from_membrane_quantities() -> None:
    plugin = FluidMechanicsPlugin()
    ctx = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "density", "value": 1000.0, "unit": "kg/m^3"},
                {"ref": "obj_1", "property": "velocity", "value": 2.0, "unit": "m/s"},
                {"ref": "obj_1", "property": "length", "value": 0.1, "unit": "m"},
            ]
        },
        config={"viscosity_pa_s": 0.001},
    )
    indicators = plugin.compute_indicators(ctx)
    assert indicators["Reynolds"] == 200_000.0
    assert indicators["Mach"] == 0.0  # no speed-of-sound quantity → default 0
