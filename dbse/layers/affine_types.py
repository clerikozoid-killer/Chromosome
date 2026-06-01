"""L1.5 AFFINE TYPES — semantic compatibility (primitives in ``dbse/semantic/``).

Layer hook is pass-through; affine types attach in RIBOSOME ``compile``.
"""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class AffineTypeChecker(PassThroughLayer):
    name: ClassVar[str] = "L1.5.AFFINE_TYPES"
