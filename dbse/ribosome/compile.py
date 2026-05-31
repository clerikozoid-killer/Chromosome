"""Compile validated MEMBRANE output into an AST."""

from __future__ import annotations

from typing import Any

from dbse.contracts.ast import AST, ASTNode
from dbse.ribosome.errors import RibosomeError
from dbse.ribosome.property_map import quantity_affine


def _symbol(name: str) -> ASTNode:
    return ASTNode(kind="SYMBOL", value=name)


def _const(value: float) -> ASTNode:
    return ASTNode(kind="CONST", value=float(value))


def _op(op: str, *children: ASTNode) -> ASTNode:
    return ASTNode(kind="OPERATOR", op=op, children=children)


def _linear_combo(constant: float, linear_coeff: float, state: str) -> ASTNode:
    """Build constant + linear_coeff * state."""
    terms: list[ASTNode] = []
    if constant != 0.0:
        terms.append(_const(constant))
    if linear_coeff != 0.0:
        term: ASTNode
        if linear_coeff == 1.0:
            term = _symbol(state)
        elif linear_coeff == -1.0:
            term = _op("NEG", _symbol(state))
        else:
            term = _op("MUL", _const(linear_coeff), _symbol(state))
        terms.append(term)
    if not terms:
        return _const(0.0)
    if len(terms) == 1:
        return terms[0]
    return _op("ADD", *terms)


def _compile_linear_ode_1(eq: dict[str, Any]) -> ASTNode:
    state = str(eq["state"])
    constant = float(eq.get("constant", 0.0))
    linear_coeff = float(eq.get("linear_coeff", 0.0))
    lhs = _op("DERIV", _symbol(state))
    rhs = _linear_combo(constant, linear_coeff, state)
    return _op("EQ", lhs, rhs)


def compile_membrane(membrane: dict[str, Any]) -> AST:
    """Build an :class:`AST` from a validated membrane dict."""
    objects = membrane.get("objects")
    if not isinstance(objects, list) or not objects:
        raise RibosomeError("MEMBRANE must contain at least one object")
    root_obj = objects[0]
    obj_id = str(root_obj["id"])
    label = str(root_obj.get("label", obj_id))
    quantities = membrane.get("quantities") or []
    qty_nodes: list[ASTNode] = []
    for q in quantities:
        if str(q.get("ref")) != obj_id:
            continue
        prop = str(q["property"])
        unit = str(q["unit"])
        qty_nodes.append(
            ASTNode(
                kind="QUANTITY",
                op=prop,
                value=float(q["value"]),
                affine_type=quantity_affine(prop, unit),
            )
        )
    eq_nodes: list[ASTNode] = []
    for raw_eq in membrane.get("equations") or []:
        eq_nodes.append(_compile_linear_ode_1(raw_eq))
    root = ASTNode(
        kind="OBJECT",
        op=obj_id,
        value=label,
        children=(*qty_nodes, *eq_nodes),
    )
    return AST(root=root)
