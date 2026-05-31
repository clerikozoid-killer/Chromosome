"""Render narrative graph to deterministic skeleton text."""

from __future__ import annotations

from dbse.narrative.models import NarrativeGraph


def to_text(graph: NarrativeGraph) -> str:
    parts: list[str] = []
    for node in graph.nodes:
        parts.append(node.template.format(**node.bindings))
    return " ".join(parts)
