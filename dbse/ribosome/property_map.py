"""Map MEMBRANE quantity properties to L1.5 AffineType."""

from __future__ import annotations

from dbse.contracts.affine import AffineType
from dbse.dimensional import parse_unit
from dbse.semantic import affine

_PROPERTY_TAG: dict[str, str] = {
    "mass": "Mass",
    "distance": "Length",
    "velocity": "Velocity",
    "force": "Force",
    "energy": "Energy",
    "time": "Time",
    "value": "Unknown",
}


def quantity_affine(property_name: str, unit: str) -> AffineType:
    """Attach an :class:`AffineType` to a membrane quantity leaf."""
    tag = _PROPERTY_TAG.get(property_name)
    if tag is not None and tag != "Unknown":
        return affine(tag)
    dim = parse_unit(unit)
    return AffineType(dim, "Unknown")
