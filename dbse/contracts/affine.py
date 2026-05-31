"""L1.5 contract: affine (semantic) types.

The architectural core of «Chromosome». A bare dimension is *necessary* but not
*sufficient*: Energy and Torque share ``[M L^2 T^-2]`` yet must never be added.
An :class:`AffineType` augments a :class:`Dimension` with a semantic tag, a tensor
rank and an optional frame of reference.

Only the type lives here. Compatibility rules (``compatible(a, b, op)``) and the
semantic-tag registry are implemented in Stage 2.
"""

from __future__ import annotations

from dataclasses import dataclass

from dbse.contracts.dimensions import Dimension


@dataclass(frozen=True, slots=True)
class AffineType:
    """A dimension enriched with semantics.

    Attributes:
        dimension: SI dimensional signature.
        semantic_tag: physical meaning, e.g. ``"Energy"``, ``"Torque"``, ``"Work"``.
        tensor_rank: 0 = scalar, 1 = vector, 2 = tensor (pseudovectors flagged via tag).
        frame_of_reference: optional frame, e.g. ``"lab"``, ``"comoving"``.
    """

    dimension: Dimension
    semantic_tag: str
    tensor_rank: int = 0
    frame_of_reference: str | None = None

    def __str__(self) -> str:
        frame = f"@{self.frame_of_reference}" if self.frame_of_reference else ""
        return f"{self.semantic_tag}{self.dimension}r{self.tensor_rank}{frame}"
