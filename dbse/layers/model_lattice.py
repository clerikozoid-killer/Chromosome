"""L2 CONTEXT MODEL LATTICE — P(Model | Context), T_ambig. Stub; logic in Stage 8."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class ModelLattice(PassThroughLayer):
    name: ClassVar[str] = "L2.MODEL_LATTICE"
