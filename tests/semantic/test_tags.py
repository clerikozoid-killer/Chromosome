"""L1.5 unit tests: the semantic-tag registry and helpers."""

from __future__ import annotations

import pytest

from dbse.contracts.affine import AffineType
from dbse.contracts.dimensions import Dimension
from dbse.semantic import SemanticTypeError, affine, ambiguous_tag, is_ambiguous

_ENERGY_DIM = Dimension.of(1, 2, -2)
_FORCE_DIM = Dimension.of(1, 1, -2)


def test_affine_builds_energy_from_registry() -> None:
    energy = affine("Energy")
    assert energy == AffineType(_ENERGY_DIM, "Energy", tensor_rank=0)


def test_affine_marks_torque_as_rank_one_pseudovector() -> None:
    torque = affine("Torque")
    assert torque.dimension == _ENERGY_DIM
    assert torque.semantic_tag == "Torque"
    assert torque.tensor_rank == 1


def test_affine_marks_force_as_rank_one() -> None:
    force = affine("Force")
    assert force == AffineType(_FORCE_DIM, "Force", tensor_rank=1)


def test_affine_carries_frame_of_reference() -> None:
    v = affine("Velocity", frame="lab")
    assert v.frame_of_reference == "lab"


def test_affine_unknown_tag_raises() -> None:
    with pytest.raises(SemanticTypeError):
        affine("Zorp")


def test_energy_and_torque_share_dimension_but_differ() -> None:
    # The whole reason L1.5 exists.
    assert affine("Energy").dimension == affine("Torque").dimension
    assert affine("Energy") != affine("Torque")


def test_ambiguous_tag_is_sorted_and_pipe_joined() -> None:
    assert ambiguous_tag("Work", "Torque") == "Torque|Work"
    assert ambiguous_tag("Torque", "Work") == "Torque|Work"  # order-independent


def test_is_ambiguous_detects_the_pipe() -> None:
    assert is_ambiguous("Torque|Work")
    assert not is_ambiguous("Energy")


def test_registry_has_at_least_ten_tags() -> None:
    from dbse.semantic.tags import _TAGS

    assert len(_TAGS) >= 10


def test_registry_contains_the_load_bearing_tags() -> None:
    from dbse.semantic.tags import _TAGS

    # Tags that downstream tasks (compatibility, combine, adversarial) depend on.
    assert {"Energy", "Torque", "Work", "Heat", "Force"} <= _TAGS.keys()


def test_no_registered_tag_contains_the_ambiguity_separator() -> None:
    # Otherwise is_ambiguous() would report a false positive for a real tag.
    from dbse.semantic.tags import _AMBIGUOUS_SEP, _TAGS

    assert all(_AMBIGUOUS_SEP not in tag for tag in _TAGS)
