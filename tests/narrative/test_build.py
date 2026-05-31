"""L6 build_graph tests."""

from __future__ import annotations

from dbse.contracts.ast import AST, ASTNode
from dbse.narrative.build import build_graph


def test_build_graph_apple_ast_with_solution() -> None:
    ast = AST(
        root=ASTNode(
            kind="OBJECT",
            op="obj_1",
            children=(
                ASTNode(kind="QUANTITY", op="mass", value=0.1),
            ),
        ),
        structure_class="Algebraic_Quantities",
    )
    solution = {"value": 0.980665, "unit": "N", "symbolic": "F = m*g"}
    graph = build_graph(ast, solution, membrane=None)
    assert len(graph.nodes) >= 1
    assert graph.nodes[0].bindings["property"] == "mass"


def test_build_graph_force_quantity_uses_solution_value() -> None:
    ast = AST(
        root=ASTNode(
            kind="OBJECT",
            op="obj_1",
            children=(
                ASTNode(kind="QUANTITY", op="mass", value=0.1),
                ASTNode(kind="QUANTITY", op="force", value=None),
            ),
        ),
    )
    solution = {"value": 0.980665, "unit": "N"}
    graph = build_graph(ast, solution, membrane=None)
    force_nodes = [n for n in graph.nodes if n.bindings.get("property") == "force"]
    assert len(force_nodes) == 1
    assert force_nodes[0].bindings["unit"] == "N"
    assert "0.981" in force_nodes[0].bindings["value"]
