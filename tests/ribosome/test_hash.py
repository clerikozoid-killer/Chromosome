"""L3 unit tests: canonical hashing."""

from __future__ import annotations

from typing import Any

from dbse.ribosome.compile import compile_membrane
from dbse.ribosome.hash import canonical_hash


def _membrane(state: str, constant: float, linear_coeff: float) -> dict[str, Any]:
    return {
        "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
        "quantities": [],
        "relations": [],
        "equations": [
            {
                "object_ref": "obj_1",
                "state": state,
                "constant": constant,
                "linear_coeff": linear_coeff,
            }
        ],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "velocity"},
    }


def test_renamed_state_variable_yields_same_hash() -> None:
    a = compile_membrane(_membrane("v", 9.81, -0.5))
    b = compile_membrane(_membrane("velocity", 9.81, -0.5))
    assert canonical_hash(a) == canonical_hash(b)
    assert len(canonical_hash(a)) == 16


def test_different_coefficients_yield_different_hashes() -> None:
    a = compile_membrane(_membrane("v", 9.81, -0.5))
    b = compile_membrane(_membrane("v", 9.81, -0.6))
    assert canonical_hash(a) != canonical_hash(b)
