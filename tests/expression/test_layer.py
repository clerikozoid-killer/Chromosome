"""L7 layer integration tests."""

from __future__ import annotations

from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.context import PipelineContext
from dbse.layers.expression import Expression
from dbse.layers.narrative import NarrativeGraph


def _apple_ctx() -> PipelineContext:
    ctx = PipelineContext(
        query="apple",
        ast=AST(
            root=ASTNode(
                kind="OBJECT",
                op="obj_1",
                children=(ASTNode(kind="QUANTITY", op="mass", value=0.1),),
            ),
            structure_class="Algebraic_Quantities",
        ),
        solution={"value": 0.980665, "unit": "N", "symbolic": "F = m*g"},
    )
    return NarrativeGraph().process(ctx)


def test_layer_styles_narrative_skeleton() -> None:
    ctx = _apple_ctx()
    out = Expression().process(ctx)
    assert out.expression is not None
    assert out.expression["eli5"]
    assert out.expression["academic"]
    assert out.expression["business"]
    assert out.trace[-1].note == "styled"


def test_layer_skips_without_narrative() -> None:
    ctx = PipelineContext(query="x")
    out = Expression().process(ctx)
    assert out.expression is None
    assert out.trace[-1].note == "skipped:no-narrative"
