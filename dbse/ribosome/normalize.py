"""Canonical normalization of AST nodes."""

from __future__ import annotations

from dbse.contracts.ast import AST, ASTNode

_COMMUTATIVE = frozenset({"ADD", "MUL"})


def normalize_ast(node: ASTNode) -> ASTNode:
    """Return a normalized copy: rename symbols, sort commutative ops, fold constants."""
    renamed = _rename_symbols(node)
    folded = _fold_constants(renamed)
    return _sort_commutative(folded)


def to_canonical(node: ASTNode) -> str:
    """Stable string form for hashing."""
    if node.kind in {"SYMBOL", "CONST", "QUANTITY"}:
        val = node.value if node.value is not None else ""
        return f"({node.kind}:{node.op}:{val})"
    if node.kind == "OBJECT":
        val = node.value if node.value is not None else ""
        inner = ",".join(to_canonical(c) for c in node.children)
        return f"({node.kind}:{node.op}:{val}[{inner}])"
    if node.kind == "OPERATOR":
        inner = ",".join(to_canonical(c) for c in node.children)
        return f"({node.op}[{inner}])"
    inner = ",".join(to_canonical(c) for c in node.children)
    return f"({node.kind}:{node.op}[{inner}])"


def normalize_ast_tree(ast: AST) -> AST:
    """Normalize the full AST wrapper, preserving metadata slots."""
    root = normalize_ast(ast.root)
    return AST(root=root, structure_class=ast.structure_class, canonical_hash=ast.canonical_hash)


def _rename_symbols(
    node: ASTNode,
    mapping: dict[str, str] | None = None,
    counter: list[int] | None = None,
) -> ASTNode:
    if mapping is None:
        mapping = {}
    if counter is None:
        counter = [0]

    def map_name(name: str) -> str:
        if name not in mapping:
            counter[0] += 1
            mapping[name] = f"x_{counter[0]}"
        return mapping[name]

    if node.kind == "SYMBOL" and isinstance(node.value, str):
        return ASTNode(kind="SYMBOL", value=map_name(node.value))
    children = tuple(_rename_symbols(c, mapping, counter) for c in node.children)
    if children == node.children and node.kind != "SYMBOL":
        return node
    return ASTNode(
        kind=node.kind,
        op=node.op,
        children=children,
        value=node.value,
        affine_type=node.affine_type,
        bindings=node.bindings,
    )


def _fold_constants(node: ASTNode) -> ASTNode:
    children = tuple(_fold_constants(c) for c in node.children)
    if node.kind == "OPERATOR" and node.op == "ADD" and len(children) == 2:
        a, b = children
        if a.kind == "CONST" and b.kind == "CONST":
            return ASTNode(kind="CONST", value=float(a.value) + float(b.value))
    if node.kind == "OPERATOR" and node.op == "MUL" and len(children) == 2:
        a, b = children
        if a.kind == "CONST" and b.kind == "CONST":
            return ASTNode(kind="CONST", value=float(a.value) * float(b.value))
    if children != node.children:
        return ASTNode(
            kind=node.kind,
            op=node.op,
            children=children,
            value=node.value,
            affine_type=node.affine_type,
            bindings=node.bindings,
        )
    return node


def _sort_commutative(node: ASTNode) -> ASTNode:
    children = tuple(_sort_commutative(c) for c in node.children)
    if node.kind == "OPERATOR" and node.op in _COMMUTATIVE and len(children) > 1:
        children = tuple(sorted(children, key=to_canonical))
    if children != node.children:
        return ASTNode(
            kind=node.kind,
            op=node.op,
            children=children,
            value=node.value,
            affine_type=node.affine_type,
            bindings=node.bindings,
        )
    return node
