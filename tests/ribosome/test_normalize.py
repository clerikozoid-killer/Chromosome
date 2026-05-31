"""L3 unit tests: AST normalization and canonical serialization."""

from __future__ import annotations

from dbse.contracts import ASTNode
from dbse.ribosome.normalize import normalize_ast, to_canonical


def _sym(name: str) -> ASTNode:
    return ASTNode(kind="SYMBOL", value=name)


def _c(value: float) -> ASTNode:
    return ASTNode(kind="CONST", value=value)


def _op(op: str, *kids: ASTNode) -> ASTNode:
    return ASTNode(kind="OPERATOR", op=op, children=kids)


def test_normalize_renames_symbols_to_x_i() -> None:
    tree = _op("EQ", _op("DERIV", _sym("v")), _sym("v"))
    out = normalize_ast(tree)
    syms = [n.value for n in _walk(out) if n.kind == "SYMBOL"]
    assert syms == ["x_1", "x_1"]


def test_normalize_sorts_commutative_add_children() -> None:
    tree = _op("ADD", _sym("b"), _sym("a"))
    out = normalize_ast(tree)
    add = out
    keys = [to_canonical(c) for c in add.children]
    assert keys == sorted(keys)


def test_normalize_folds_numeric_add() -> None:
    tree = _op("ADD", _c(2.0), _c(3.0))
    out = normalize_ast(tree)
    assert out.kind == "CONST"
    assert out.value == 5.0


def _walk(node: ASTNode) -> list[ASTNode]:
    out = [node]
    for ch in node.children:
        out.extend(_walk(ch))
    return out
