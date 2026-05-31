"""L6 SEMANTIC NARRATIVE GRAPH — deterministic text skeleton."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import PipelineContext
from dbse.narrative.build import build_graph
from dbse.narrative.models import NarrativeGraph as GraphResult
from dbse.narrative.render import to_text


class NarrativeGraph:
    """L6 layer: build narrative graph + skeleton text from AST/solution."""

    name: ClassVar[str] = "L6.NARRATIVE"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.ast is None or ctx.solution is None:
            ctx.record(self.name, note="skipped:no-ast-or-solution")
            return ctx
        graph: GraphResult = build_graph(ctx.ast, ctx.solution, ctx.membrane)
        skeleton = to_text(graph)
        ctx.narrative = {
            "skeleton": skeleton,
            "nodes": [n.to_dict() for n in graph.nodes],
            "forbidden_metaphors": sorted({m for n in graph.nodes for m in n.forbidden_metaphors}),
        }
        ctx.record(self.name, note="built", chars=len(skeleton))
        return ctx
