"""L3 unit tests: property/unit → AffineType mapping."""

from __future__ import annotations

from dbse.contracts import AffineType
from dbse.ribosome.property_map import quantity_affine


def test_mass_maps_to_mass_tag() -> None:
    aff = quantity_affine("mass", "kg")
    assert isinstance(aff, AffineType)
    assert aff.semantic_tag == "Mass"
    assert aff.tensor_rank == 0


def test_unknown_property_uses_dimension_from_unit() -> None:
    aff = quantity_affine("gravitational_force", "N")
    assert aff.semantic_tag == "Unknown"
    assert str(aff.dimension) == str(quantity_affine("force", "N").dimension)
