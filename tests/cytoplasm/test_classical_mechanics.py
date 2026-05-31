"""L4 unit tests: classical_mechanics domain plugin."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.contracts.proof import Severity
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin


def test_classical_mechanics_registers_non_relativistic_invariant() -> None:
    plugin = ClassicalMechanicsPlugin()
    names = {inv.name for inv in plugin.register_invariants()}
    assert "v_lt_c" in names
    inv = next(i for i in plugin.register_invariants() if i.name == "v_lt_c")
    assert inv.severity is Severity.CRITICAL
    assert inv.threshold == 299_792_458.0


def test_classical_mechanics_injects_newton_2_constraint() -> None:
    plugin = ClassicalMechanicsPlugin()
    ctx = PipelineContext(query="q", membrane={"quantities": []})
    types = {c.constraint_type for c in plugin.inject_constraints(ctx)}
    assert "newton_2" in types


def test_low_velocity_selects_linear_friction_model() -> None:
    plugin = ClassicalMechanicsPlugin()
    ctx = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 0.5, "unit": "m/s"},
            ]
        },
    )
    indicators = plugin.compute_indicators(ctx)
    model = plugin.select_model(indicators)
    assert model.id == "linear_friction"


def test_high_velocity_selects_quadratic_friction_model() -> None:
    plugin = ClassicalMechanicsPlugin()
    ctx = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 50.0, "unit": "m/s"},
            ]
        },
    )
    indicators = plugin.compute_indicators(ctx)
    model = plugin.select_model(indicators)
    assert model.id == "quadratic_friction"
