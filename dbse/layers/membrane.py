"""L0 MEMBRANE — parse free text into a strictly-validated entity graph.

The LLM (or, in tests, the deterministic fallback) runs in a sandbox: its output
is validated against the strict Pydantic schema before anything downstream sees
it. A schema violation halts the pipeline with ``CLARIFICATION`` instead of
silently "completing" the input — the v5.0 prompt-injection mitigation.
"""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.membrane import (
    DeterministicParser,
    MembraneError,
    ParserAdapter,
    validate_membrane,
)


class Membrane:
    """L0 layer: parse + strict-validate the query into ``ctx.membrane``."""

    name: ClassVar[str] = "L0.MEMBRANE"

    def __init__(self, parser: ParserAdapter | None = None) -> None:
        self._parser: ParserAdapter = parser if parser is not None else DeterministicParser()

    def process(self, ctx: PipelineContext) -> PipelineContext:
        try:
            raw = self._parser.parse(ctx.query)
            output = validate_membrane(raw)
        except MembraneError as exc:
            ctx.record(self.name, note="schema-violation")
            ctx.halt(HaltReason.CLARIFICATION, str(exc))
            return ctx
        ctx.membrane = output.model_dump(by_alias=True, mode="json")
        ctx.record(self.name, note="parsed", question_type=output.question_type.value)
        return ctx
