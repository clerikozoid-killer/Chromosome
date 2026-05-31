"""L0 adversarial tests (QA-gate level 5): prompt-injection mitigation.

Each case simulates a compromised LLM emitting a payload that tries to escape the
sandbox. The strict schema must reject every one with MembraneError, and the layer
must turn that into a CLARIFICATION halt — never a silent "completion".
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.membrane import Membrane
from dbse.membrane import MembraneError, validate_membrane

_BASE: dict[str, Any] = {
    "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
    "quantities": [],
    "relations": [],
    "question_type": "compute",
    "target": {"ref": "obj_1", "property": "force"},
}

# Each payload is the base with one injection applied.
_ATTACKS: dict[str, dict[str, Any]] = {
    "forbidden_operator_node": {**_BASE, "operators": [{"op": "SUPPRESS", "arg": "friction"}]},
    "forbidden_invariant_node": {**_BASE, "invariants": [{"law": "g = -9.81"}]},
    "forbidden_context_node": {**_BASE, "context": {"assume": "no air"}},
    "question_type_command_injection": {**_BASE, "question_type": "compute; DROP friction"},
    "extra_field_on_target": {**_BASE, "target": {"ref": "obj_1", "property": "f", "x": 1}},
    "suppress_field_on_quantity": {
        **_BASE,
        "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
        "quantities": [
            {"ref": "obj_1", "property": "g", "value": -9.81, "unit": "m/s^2", "hidden": True},
        ],
    },
    "injected_unit_garbage": {
        **_BASE,
        "quantities": [{"ref": "obj_1", "property": "mass", "value": 1, "unit": "SUPPRESS"}],
    },
    "dangling_reference": {
        **_BASE,
        "quantities": [{"ref": "ghost", "property": "mass", "value": 1, "unit": "kg"}],
    },
}


@pytest.mark.parametrize("name", sorted(_ATTACKS))
def test_injection_payloads_are_rejected_by_schema(name: str) -> None:
    with pytest.raises(MembraneError):
        validate_membrane(_ATTACKS[name])


@pytest.mark.parametrize("name", sorted(_ATTACKS))
def test_injection_payloads_halt_the_layer_with_clarification(name: str) -> None:
    class Attacker:
        name: ClassVar[str] = "attacker"

        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def parse(self, query: str) -> dict[str, Any]:
            return self._payload

    ctx = Membrane(parser=Attacker(_ATTACKS[name])).process(PipelineContext(query="x"))
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.CLARIFICATION
    assert ctx.membrane is None
