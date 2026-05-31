"""L3 property-based tests: normalization idempotence and hash invariance."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.contracts import AST, ASTNode
from dbse.ribosome.hash import canonical_hash
from dbse.ribosome.normalize import normalize_ast, to_canonical


def _sym(name: str) -> ASTNode:
    return ASTNode(kind="SYMBOL", value=name)


def _c(value: float) -> ASTNode:
    return ASTNode(kind="CONST", value=value)


def _op(op: str, *kids: ASTNode) -> ASTNode:
    return ASTNode(kind="OPERATOR", op=op, children=kids)


@st.composite
def symbol_names(draw: st.DrawFn) -> str:
    return draw(st.sampled_from(["a", "b", "v", "x", "velocity", "state"]))


@st.composite
def small_trees(draw: st.DrawFn) -> ASTNode:
    a = _sym(draw(symbol_names()))
    b = _sym(draw(symbol_names()))
    return draw(
        st.one_of(
            st.just(_op("ADD", a, b)),
            st.just(_op("MUL", a, b)),
            st.just(_op("EQ", _op("DERIV", a), b)),
        )
    )


@given(small_trees())
def test_property_normalization_is_idempotent(tree: ASTNode) -> None:
    once = normalize_ast(tree)
    twice = normalize_ast(once)
    assert to_canonical(once) == to_canonical(twice)


@given(small_trees(), symbol_names(), symbol_names())
def test_property_renamed_symbols_do_not_change_hash_when_isomorphic(
    tree: ASTNode, n1: str, n2: str
) -> None:
    if n1 == n2:
        return
    # Build two trees that differ only by symbol spelling if both appear.
    def repl(node: ASTNode, src: str, dst: str) -> ASTNode:
        if node.kind == "SYMBOL" and node.value == src:
            return ASTNode(kind="SYMBOL", value=dst)
        kids = tuple(repl(c, src, dst) for c in node.children)
        return ASTNode(kind=node.kind, op=node.op, children=kids, value=node.value)

    if not any(n.value == n1 for n in _walk(tree)):
        return
    a = AST(root=tree)
    b = AST(root=repl(tree, n1, n2))
    if to_canonical(normalize_ast(a.root)) == to_canonical(normalize_ast(b.root)):
        assert canonical_hash(a) == canonical_hash(b)


def _walk(node: ASTNode) -> list[ASTNode]:
    out = [node]
    for ch in node.children:
        out.extend(_walk(ch))
    return out
