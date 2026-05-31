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
