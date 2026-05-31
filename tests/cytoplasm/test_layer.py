"""L4 layer integration tests."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin
from dbse.cytoplasm.registry import PluginRegistry
from dbse.layers.cytoplasm import Cytoplasm


def test_cytoplasm_applies_classical_mechanics_plugin_by_domain_hint() -> None:
    registry = PluginRegistry()
    registry.register(ClassicalMechanicsPlugin())
    layer = Cytoplasm(registry=registry)
    ctx = PipelineContext(
        query="falling body",
        config={"domain_hint": "classical_mechanics"},
        membrane={
            "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 10.0, "unit": "m/s"},
            ],
            "relations": [],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "velocity"},
        },
        ast=None,
    )
    out = layer.process(ctx)
    assert out.domain_model == "quadratic_friction"
    assert out.invariants is not None
    assert any(inv.name == "v_lt_c" for inv in out.invariants)
    assert out.constraints is not None
    assert out.trace[-1].layer == "L4.CYTOPLASM"
    assert out.trace[-1].note == "applied"


def test_cytoplasm_plugin_disconnect_does_not_require_core_changes() -> None:
    registry = PluginRegistry()
    registry.register(ClassicalMechanicsPlugin())
    layer = Cytoplasm(registry=registry)
    registry.unregister("classical_mechanics")
    ctx = PipelineContext(
        query="q",
        config={"domain_hint": "classical_mechanics"},
        membrane={"quantities": []},
    )
    out = layer.process(ctx)
    assert out.trace[-1].note == "skipped:unknown-domain"
    assert out.invariants is None
