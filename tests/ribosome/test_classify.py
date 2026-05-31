"""L3 unit tests: structural classification."""

from __future__ import annotations

from dbse.ribosome.classify import classify_structure
from dbse.ribosome.compile import compile_membrane


def test_free_fall_and_rc_circuit_both_classify_as_linear_ode_order_1() -> None:
    free_fall = compile_membrane(
        {
            "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
            "quantities": [],
            "relations": [],
            "equations": [
                {"object_ref": "obj_1", "state": "v", "constant": 9.81, "linear_coeff": -0.5},
            ],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "velocity"},
        }
    )
    rc = compile_membrane(
        {
            "objects": [{"id": "obj_1", "type": "circuit", "label": "rc"}],
            "quantities": [],
            "relations": [],
            "equations": [
                # RC dV/dt + V/R = 0  →  dV/dt = -(1/R) * V  (homogeneous)
                {"object_ref": "obj_1", "state": "V", "constant": 0.0, "linear_coeff": -0.2},
            ],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "value"},
        }
    )
    assert classify_structure(free_fall.root) == "LinearODE_Order1"
    assert classify_structure(rc.root) == "LinearODE_Order1"
