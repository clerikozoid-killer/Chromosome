"""L6 property-based tests: skeleton rendering is deterministic."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.contracts.ast import AST, ASTNode
from dbse.narrative.build import build_graph
from dbse.narrative.render import to_text


def _qty(prop: str, value: float) -> ASTNode:
    return ASTNode(kind="QUANTITY", op=prop, value=value)


@st.composite
def apple_like_asts(draw: st.DrawFn) -> AST:
    mass = draw(st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False))
    include_force = draw(st.booleans())
    children: list[ASTNode] = [_qty("mass", mass)]
    if include_force:
        children.append(_qty("force", 0.0))
    root = ASTNode(kind="OBJECT", op="obj_1", children=tuple(children))
    return AST(root=root, structure_class="Algebraic_Quantities")


@st.composite
def weight_solutions(draw: st.DrawFn) -> dict[str, object]:
    value = draw(st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False))
    return {"value": value, "unit": "N", "symbolic": "F = m*g"}


@given(apple_like_asts(), weight_solutions())
def test_property_to_text_is_idempotent(ast: AST, solution: dict[str, object]) -> None:
    graph = build_graph(ast, solution, membrane=None)
    once = to_text(graph)
    twice = to_text(build_graph(ast, solution, membrane=None))
    assert once == twice
