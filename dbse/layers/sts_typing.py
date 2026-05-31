"""L0.5 STS TYPING — classify the query and decide the route.

Runs after L0 MEMBRANE. Stores the query type in ``ctx.sts_type`` and the route
in the trace payload. ``OPINION`` queries are out of scope and halt the pipeline
with ``UNHANDLED``; every other type is recorded and the conveyor continues
(real route-based skipping arrives with the downstream layers).
"""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.sts import ROUTES, QueryType, classify


class StsTyping:
    """L0.5 layer: rule-based query classification + routing."""

    name: ClassVar[str] = "L0.5.STS_TYPING"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        has_quantities = bool(ctx.membrane and ctx.membrane.get("quantities"))
        qtype = classify(ctx.query, has_quantities=has_quantities)
        ctx.sts_type = qtype.value
        ctx.record(self.name, note="classified", route=ROUTES[qtype])
        if qtype is QueryType.OPINION:
            ctx.halt(HaltReason.UNHANDLED, "Opinion queries are out of scope (L0.5).")
        return ctx
