"""L4 metamorphic tests: model selection invariant under unit rescaling."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin
from dbse.cytoplasm.plugins.fluid_mechanics import FluidMechanicsPlugin


def test_classical_mechanics_model_stable_under_velocity_unit_change() -> None:
    plugin = ClassicalMechanicsPlugin()
    si = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 3.6, "unit": "km/h"},
            ]
        },
    )
    native = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 1.0, "unit": "m/s"},
            ]
        },
    )
    model_si = plugin.select_model(plugin.compute_indicators(si))
    model_native = plugin.select_model(plugin.compute_indicators(native))
    assert model_si.id == model_native.id == "linear_friction"


def test_fluid_mechanics_reynolds_stable_under_compatible_units() -> None:
    plugin = FluidMechanicsPlugin()
    ctx_a = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "density", "value": 1000.0, "unit": "kg/m^3"},
                {"ref": "obj_1", "property": "velocity", "value": 1.0, "unit": "m/s"},
                {"ref": "obj_1", "property": "length", "value": 0.01, "unit": "m"},
            ]
        },
        config={"viscosity_pa_s": 0.001},
    )
    ctx_b = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "density", "value": 1000.0, "unit": "kg/m^3"},
                {"ref": "obj_1", "property": "velocity", "value": 3.6, "unit": "km/h"},
                {"ref": "obj_1", "property": "length", "value": 1.0, "unit": "cm"},
            ]
        },
        config={"viscosity_pa_s": 0.001},
    )
    ind_a = plugin.compute_indicators(ctx_a)
    ind_b = plugin.compute_indicators(ctx_b)
    model_a = plugin.select_model(ind_a)
    model_b = plugin.select_model(ind_b)
    assert ind_a["Reynolds"] == ind_b["Reynolds"]
    assert model_a.id == model_b.id
