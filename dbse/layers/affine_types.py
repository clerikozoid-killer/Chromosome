"""L1.5 AFFINE TYPES — semantic type checking. Stub; logic in Stage 2."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class AffineTypeChecker(PassThroughLayer):
    name: ClassVar[str] = "L1.5.AFFINE_TYPES"
