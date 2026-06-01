"""Visualization helpers for API responses."""

from __future__ import annotations

from dbse.contracts.context import PipelineContext


def proof_trace_mermaid(ctx: PipelineContext) -> str:
    lines = ["graph TD"]
    for i, entry in enumerate(ctx.trace):
        nid = f"L{i}"
        lines.append(f'  {nid}["{entry.layer}<br/>{entry.note}"]')
        if i > 0:
            lines.append(f"  L{i - 1} --> {nid}")
    if ctx.ast and ctx.ast.canonical_hash:
        lines.append(f'  HASH["ast_hash={ctx.ast.canonical_hash}"]')
        if ctx.trace:
            lines.append(f"  L{len(ctx.trace) - 1} --> HASH")
    return "\n".join(lines)
