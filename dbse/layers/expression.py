"""L7 EXPRESSION GENES — constrained styling with deterministic fallback."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import PipelineContext
from dbse.expression.fallback import style_fallback
from dbse.expression.validator import validate_expression
from dbse.expression.whitelist import DEFAULT_METAPHOR_WHITELIST


class Expression:
    """L7 layer: style L6 skeleton into eli5/academic/business variants."""

    name: ClassVar[str] = "L7.EXPRESSION"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.narrative:
            ctx.record(self.name, note="skipped:no-narrative")
            return ctx
        sk = str(ctx.narrative.get("skeleton", ""))
        val = ctx.solution.get("value") if ctx.solution else None
        unit = ctx.solution.get("unit") if ctx.solution else None
        out = style_fallback(
            sk,
            value=float(val) if val is not None else None,
            unit=str(unit) if unit else None,
        )
        forbidden = set(ctx.narrative.get("forbidden_metaphors", []))
        validate_expression(
            sk,
            out,
            forbidden=forbidden,
            whitelist=set(DEFAULT_METAPHOR_WHITELIST),
        )
        ctx.expression = out.model_dump()
        ctx.record(self.name, note="styled")
        return ctx
