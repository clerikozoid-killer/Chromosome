"""L3 unit tests: MEMBRANE → AST compilation."""

from __future__ import annotations

import pytest

from dbse.contracts import AST, ASTNode
from dbse.ribosome import RibosomeError
from dbse.ribosome.compile import compile_membrane


def test_ribosome_error_is_a_value_error() -> None:
    assert issubclass(RibosomeError, ValueError)
    with pytest.raises(RibosomeError):
        raise RibosomeError("boom")


def test_compile_minimal_membrane_produces_object_and_quantity_leaves() -> None:
    membrane = {
        "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
        "quantities": [
            {"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "kg"},
        ],
        "relations": [],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "mass"},
    }
    ast = compile_membrane(membrane)
    assert isinstance(ast, AST)
    assert ast.root.kind == "OBJECT"
    assert ast.root.op == "obj_1"
    assert len(ast.root.children) == 1
    qty = ast.root.children[0]
    assert qty.kind == "QUANTITY"
    assert qty.op == "mass"
    assert qty.value == 0.1
    assert qty.affine_type is not None
    assert qty.affine_type.semantic_tag == "Mass"


def _find_operator(root: ASTNode, op: str) -> ASTNode | None:
    if root.kind == "OPERATOR" and root.op == op:
        return root
    for child in root.children:
        found = _find_operator(child, op)
        if found is not None:
            return found
    return None


def test_compile_linear_ode_1_builds_derivative_equation_tree() -> None:
    membrane = {
        "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
        "quantities": [],
        "relations": [],
        "equations": [
            {"object_ref": "obj_1", "state": "v", "constant": 9.81, "linear_coeff": -0.5},
        ],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "velocity"},
    }
    ast = compile_membrane(membrane)
    eq = _find_operator(ast.root, "EQ")
    assert eq is not None
    deriv = _find_operator(ast.root, "DERIV")
    assert deriv is not None
    assert deriv.children[0].kind == "SYMBOL"
    assert deriv.children[0].value == "v"
