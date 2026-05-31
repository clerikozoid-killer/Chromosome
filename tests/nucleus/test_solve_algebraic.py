"""L5 unit tests: algebraic solve dispatcher."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.context import PipelineContext
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.solve_algebraic import solve_algebraic


def _apple_ctx() -> PipelineContext:
    return PipelineContext(
        query="weight",
        config={"domain_hint": "classical_mechanics"},
        membrane={
            "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
            "quantities": [
                {"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"},
            ],
            "relations": [],
            "equations": [],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "force"},
        },
        ast=AST(
            root=ASTNode(kind="OBJECT", op="obj_1", children=()),
            structure_class="Algebraic_Quantities",
        ),
        domain_model="linear_friction",
    )


def test_solve_algebraic_apple_weight() -> None:
    result = solve_algebraic(_apple_ctx())
    assert result.unit == "N"
    assert result.value == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-9)
    assert result.symbolic == "m * g"


def test_solve_algebraic_missing_mass_raises() -> None:
    ctx = _apple_ctx()
    ctx.membrane = dict(ctx.membrane or {})
    ctx.membrane["quantities"] = []
    with pytest.raises(NucleusError):
        solve_algebraic(ctx)
