"""The layer protocol and a pass-through base implementation.

Every processing stage L0..L7 implements :class:`Layer`. In Stage 0 all layers
are pass-through stubs that only record a trace entry; real logic is added per
``ROADMAP.md``. Keeping the interface tiny (``process(ctx) -> ctx``) lets the
pipeline be assembled from a simple ordered list.
"""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from dbse.contracts.context import PipelineContext


@runtime_checkable
class Layer(Protocol):
    """A single stage of the conveyor."""

    name: ClassVar[str]

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """Transform the context and return it (may set ``ctx.halted``)."""
        ...


class PassThroughLayer:
    """Base stub: records a trace entry and returns the context unchanged.

    Concrete stages override :meth:`process` once their stage from the roadmap
    is implemented. Until then they behave as identity, so the full pipeline runs
    end-to-end from day one.
    """

    name: ClassVar[str] = "layer"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        ctx.record(self.name, note="stub:pass-through")
        return ctx
