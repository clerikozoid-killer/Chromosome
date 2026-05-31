"""Compile validated MEMBRANE output into an AST."""

from __future__ import annotations

from typing import Any

from dbse.contracts.ast import AST, ASTNode
from dbse.ribosome.errors import RibosomeError
from dbse.ribosome.property_map import quantity_affine


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
    root = ASTNode(
        kind="OBJECT",
        op=obj_id,
        value=label,
        children=tuple(qty_nodes),
    )
    return AST(root=root)
