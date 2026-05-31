"""Structural class labels for normalized AST roots."""

from __future__ import annotations

from dbse.contracts.ast import ASTNode


def classify_structure(root: ASTNode) -> str:
    """Return a coarse structural class string for the AST root."""
    if _contains_linear_ode_1(root):
        return "LinearODE_Order1"
    if _contains_only_quantities(root):
        return "Algebraic_Quantities"
    return "Unknown"


def _contains_linear_ode_1(node: ASTNode) -> bool:
    if (
        node.kind == "OPERATOR"
        and node.op == "EQ"
        and len(node.children) == 2
    ):
        lhs, _rhs = node.children
        if (
            lhs.kind == "OPERATOR"
            and lhs.op == "DERIV"
            and len(lhs.children) == 1
            and lhs.children[0].kind == "SYMBOL"
        ):
            return True
    return any(_contains_linear_ode_1(child) for child in node.children)


def _contains_only_quantities(node: ASTNode) -> bool:
    allowed = {"OBJECT", "QUANTITY"}
    stack = [node]
    while stack:
        cur = stack.pop()
        if cur.kind not in allowed and cur.kind == "OPERATOR":
            return False
        stack.extend(cur.children)
    return True
