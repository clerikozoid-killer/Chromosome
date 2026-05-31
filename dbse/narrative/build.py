from __future__ import annotations

from typing import Any

from dbse.contracts.ast import AST, ASTNode
from dbse.narrative.models import NarrativeGraph, NarrativeNode
from dbse.narrative.templates import template_for_quantity


def build_graph(
    ast: AST,
    solution: dict[str, Any] | None,
    membrane: dict[str, Any] | None,
) -> NarrativeGraph:
    nodes: list[NarrativeNode] = []
    mass_holder: dict[str, str] = {"mass": ""}
    _walk(ast.root, nodes, solution, membrane, mass_holder)
    return NarrativeGraph(nodes=tuple(nodes))


def _walk(
    node: ASTNode,
    out: list[NarrativeNode],
    sol: dict[str, Any] | None,
    mem: dict[str, Any] | None,
    mass_holder: dict[str, str],
) -> None:
    if node.kind == "QUANTITY":
        prop = str(node.op or "value")
        spec = template_for_quantity(prop)
        unit = "N" if prop == "force" and sol else ""
        raw_val = sol.get("value", node.value) if sol and prop == "force" else node.value
        if prop == "mass" and node.value is not None:
            mass_holder["mass"] = f"{node.value} kg"
        if isinstance(raw_val, float):
            val_str = f"{raw_val:.3f}"
        else:
            val_str = str(raw_val) if raw_val is not None else "?"
        sol_unit = (sol or {}).get("unit", "")
        bindings = {
            "property": prop,
            "value": val_str,
            "unit": unit or sol_unit or "?",
            "mass": mass_holder["mass"],
        }
        out.append(
            NarrativeNode(
                node_id=f"q_{prop}_{len(out)}",
                template=spec.template,
                bindings=bindings,
                allowed_verbs=spec.allowed_verbs,
                forbidden_metaphors=spec.forbidden_metaphors,
            )
        )
    for child in node.children:
        _walk(child, out, sol, mem, mass_holder)
