"""L6 layer integration tests."""

from __future__ import annotations

from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.context import PipelineContext
from dbse.layers.narrative import NarrativeGraph


def _apple_ast() -> AST:
    return AST(
        root=ASTNode(
            kind="OBJECT",
            op="obj_1",
            children=(ASTNode(kind="QUANTITY", op="mass", value=0.1),),
        ),
        structure_class="Algebraic_Quantities",
    )


def test_layer_builds_narrative_skeleton() -> None:
    ctx = PipelineContext(
        query="apple",
        ast=_apple_ast(),
        solution={"value": 0.980665, "unit": "N", "symbolic": "F = m*g"},
    )
    out = NarrativeGraph().process(ctx)
    assert out.narrative is not None
    assert out.narrative["skeleton"]
    assert out.narrative["nodes"]
    assert "хочет" in out.narrative["forbidden_metaphors"]
    assert out.trace[-1].note == "built"


def test_layer_skips_without_solution() -> None:
    ctx = PipelineContext(query="x", ast=_apple_ast())
    out = NarrativeGraph().process(ctx)
    assert out.narrative is None
    assert out.trace[-1].note == "skipped:no-ast-or-solution"
