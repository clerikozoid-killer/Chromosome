"""L1 DIMENSIONAL ANALYSIS — SI dimension algebra (primitives in ``dbse/dimensional/``).

Layer hook is pass-through; dimensional checks run in MEMBRANE validation and RIBOSOME compile.
"""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class DimensionalAnalysis(PassThroughLayer):
    name: ClassVar[str] = "L1.DIMENSIONS"
