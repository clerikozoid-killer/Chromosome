"""The end-to-end conveyor that threads a query through layers L0..L7.

Layers run in a fixed order. ``Early Pruning``: once a layer sets ``ctx.halted``,
the remaining layers are skipped — cheap upstream checks (dimensions, types,
ambiguity) stop the run before expensive downstream work (Z3/SymPy).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dbse.contracts.context import PipelineContext
from dbse.layers import (
    AffineTypeChecker,
    Cytoplasm,
    DimensionalAnalysis,
    Expression,
    Membrane,
    ModelLattice,
    NarrativeGraph,
    Nucleus,
    Ribosome,
    StsTyping,
)
from dbse.layers.base import Layer


def default_layers() -> list[Layer]:
    """The canonical L0..L7 ordering from the spec pipeline."""
    return [
        Membrane(),            # L0
        StsTyping(),           # L0.5
        DimensionalAnalysis(),  # L1
        AffineTypeChecker(),   # L1.5
        ModelLattice(),        # L2
        Ribosome(),            # L3
        Cytoplasm(),           # L4
        Nucleus(),             # L5
        NarrativeGraph(),      # L6
        Expression(),          # L7
    ]


class Pipeline:
    """Assembles ordered layers and runs a query through them."""

    def __init__(self, layers: Sequence[Layer] | None = None) -> None:
        self.layers: list[Layer] = list(layers) if layers is not None else default_layers()

    def run(self, query: str, config: dict[str, Any] | None = None) -> PipelineContext:
        ctx = PipelineContext(query=query, config=config or {})
        for layer in self.layers:
            if ctx.halted:
                break
            ctx = layer.process(ctx)
        return ctx
