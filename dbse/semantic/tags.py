"""L1.5 semantic-tag registry and tag-combination rules.

A *semantic tag* names the physical meaning of a quantity that a bare dimension
cannot distinguish (``Energy`` vs ``Torque`` both being ``[M L^2 T^-2]``). The
registry maps each known tag to its dimension and default tensor rank, and the
fusion tables encode how tags combine under ``+``/``-`` and ``×``/``÷``.

Ambiguity (e.g. ``Force × Length`` could be ``Work`` *or* ``Torque``) is encoded
directly in the ``semantic_tag`` string as a sorted, pipe-joined value
(``"Torque|Work"``) because :class:`~dbse.contracts.affine.AffineType` is a frozen
contract with a ``str`` tag field — L2 (Stage 8) resolves the ambiguity later.
"""

from __future__ import annotations

from dataclasses import dataclass

from dbse.contracts.affine import AffineType
from dbse.contracts.dimensions import Dimension
from dbse.semantic.errors import SemanticTypeError

# Reserved separator for ambiguous tags. No registered tag in ``_TAGS`` may
# contain it, or ``is_ambiguous`` would misfire (enforced by tests).
_AMBIGUOUS_SEP = "|"


@dataclass(frozen=True, slots=True)
class TagSpec:
    """The dimension and default tensor rank of a known semantic tag."""

    dimension: Dimension
    tensor_rank: int = 0


# Known physical semantic tags. Many share a dimension on purpose.
_TAGS: dict[str, TagSpec] = {
    # [M L^2 T^-2] — the energy/torque collision family.
    "Energy": TagSpec(Dimension.of(1, 2, -2), 0),
    "Work": TagSpec(Dimension.of(1, 2, -2), 0),
    "Heat": TagSpec(Dimension.of(1, 2, -2), 0),
    "InternalEnergy": TagSpec(Dimension.of(1, 2, -2), 0),
    "Torque": TagSpec(Dimension.of(1, 2, -2), 1),  # pseudovector
    # mechanical
    "Force": TagSpec(Dimension.of(1, 1, -2), 1),
    "Momentum": TagSpec(Dimension.of(1, 1, -1), 1),
    "Power": TagSpec(Dimension.of(1, 2, -3), 0),
    "Velocity": TagSpec(Dimension.of(0, 1, -1), 1),
    "Length": TagSpec(Dimension.of(0, 1), 0),
    "Mass": TagSpec(Dimension.of(1), 0),
    "Time": TagSpec(Dimension.of(0, 0, 1), 0),
}

# Whitelisted additive fusions: unlike tags (same dimension) that MAY be added,
# producing a named result. Keyed by an unordered pair of tags.
ADDITIVE_FUSIONS: dict[frozenset[str], str] = {
    frozenset({"Work", "Heat"}): "InternalEnergy",
}

# Tag results of multiplication, keyed by an unordered pair. A tuple of length
# > 1 means the result is ambiguous (flagged for L2).
MULTIPLICATIVE_FUSIONS: dict[frozenset[str], tuple[str, ...]] = {
    frozenset({"Force", "Length"}): ("Torque", "Work"),
    frozenset({"Force", "Velocity"}): ("Power",),
    frozenset({"Mass", "Velocity"}): ("Momentum",),
}

# Tag results of division. Division is NOT commutative for tags, so the key is an
# ordered ``(numerator, denominator)`` pair.
DIVISIVE_FUSIONS: dict[tuple[str, str], str] = {
    ("Energy", "Time"): "Power",
    ("Work", "Time"): "Power",
    ("Momentum", "Time"): "Force",
}


def affine(tag: str, *, frame: str | None = None) -> AffineType:
    """Build an :class:`AffineType` for a known semantic tag from the registry."""
    spec = _TAGS.get(tag)
    if spec is None:
        raise SemanticTypeError(f"Unknown semantic tag: {tag!r}")
    return AffineType(spec.dimension, tag, spec.tensor_rank, frame)


def ambiguous_tag(*tags: str) -> str:
    """Encode an ambiguous result as a sorted, pipe-joined tag string."""
    return _AMBIGUOUS_SEP.join(sorted(set(tags)))


def is_ambiguous(tag: str) -> bool:
    """True if ``tag`` encodes more than one candidate semantic tag."""
    return _AMBIGUOUS_SEP in tag
