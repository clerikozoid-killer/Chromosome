"""L1 DIMENSIONAL ANALYSIS — SI dimension algebra. Stub; logic in Stage 1."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class DimensionalAnalysis(PassThroughLayer):
    name: ClassVar[str] = "L1.DIMENSIONS"
