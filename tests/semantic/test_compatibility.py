"""L1.5 unit tests: semantic compatibility rules and SemanticTypeError."""

from __future__ import annotations

import pytest

from dbse.contracts.affine import AffineType
from dbse.contracts.dimensions import Dimension
from dbse.dimensional import DimensionError
from dbse.semantic import Operator, SemanticTypeError, affine, check_compatible, compatible


def test_semantic_type_error_is_a_type_error() -> None:
    assert issubclass(SemanticTypeError, TypeError)
    with pytest.raises(SemanticTypeError):
        raise SemanticTypeError("boom")


def test_operator_has_the_six_kinds() -> None:
    names = {op.name for op in Operator}
    assert names == {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "DOT", "CROSS"}


def test_add_same_tag_is_compatible_and_returns_that_type() -> None:
    result = check_compatible(affine("Energy"), affine("Energy"), Operator.ADD)
    assert result == affine("Energy")
    assert compatible(affine("Energy"), affine("Energy"), Operator.ADD)


def test_add_energy_and_torque_raises_semantic_type_error() -> None:
    # Same dimension, different tag AND rank -> the L1.5 collision.
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
    assert not compatible(affine("Energy"), affine("Torque"), Operator.ADD)


def test_add_error_message_mentions_operands_and_suggestion() -> None:
    with pytest.raises(SemanticTypeError) as excinfo:
        check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
    message = str(excinfo.value)
    assert "Energy" in message
    assert "Torque" in message
    assert "ADD" in message
    # Suggestion advertises the known fusion.
    assert "Work" in message and "Heat" in message


def test_add_work_and_heat_fuses_to_internal_energy() -> None:
    result = check_compatible(affine("Work"), affine("Heat"), Operator.ADD)
    assert result == affine("InternalEnergy")
    assert compatible(affine("Work"), affine("Heat"), Operator.ADD)


def test_add_unlike_dimension_raises_dimension_error_not_semantic() -> None:
    # Energy [M L^2 T^-2] + Force [M L T^-2] differ in dimension: the L1 gate
    # must fire first (DimensionError), NOT a SemanticTypeError. This proves
    # L1.5 reuses L1 pruning.
    with pytest.raises(DimensionError):
        check_compatible(affine("Energy"), affine("Force"), Operator.ADD)
    assert not compatible(affine("Energy"), affine("Force"), Operator.ADD)


def test_subtract_follows_the_same_rules() -> None:
    assert compatible(affine("Energy"), affine("Energy"), Operator.SUBTRACT)
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Energy"), affine("Torque"), Operator.SUBTRACT)


def test_add_same_dimension_same_tag_different_rank_is_rejected() -> None:
    # Two "Energy"-tagged values that disagree on rank.
    scalar = affine("Energy")
    pseudo = AffineType(Dimension.of(1, 2, -2), "Energy", tensor_rank=1)
    with pytest.raises(SemanticTypeError):
        check_compatible(scalar, pseudo, Operator.ADD)


def test_dot_requires_two_rank_one_equal_dimension_vectors() -> None:
    v = affine("Velocity")  # rank 1
    result = check_compatible(v, v, Operator.DOT)
    assert result.tensor_rank == 0                      # dot of vectors -> scalar
    assert result.semantic_tag == "Scalar"
    assert result.dimension == Dimension.of(0, 2, -2)   # velocity^2
    assert compatible(v, v, Operator.DOT)


def test_dot_rejects_a_scalar_operand() -> None:
    with pytest.raises(SemanticTypeError) as excinfo:
        check_compatible(affine("Energy"), affine("Velocity"), Operator.DOT)
    assert "DOT" in str(excinfo.value)


def test_dot_rejects_unequal_dimension_vectors() -> None:
    assert not compatible(affine("Velocity"), affine("Force"), Operator.DOT)


def test_cross_requires_two_polar_vectors() -> None:
    p = AffineType(Dimension.of(0, 1), "PolarVector", tensor_rank=1)
    result = check_compatible(p, p, Operator.CROSS)
    assert result.tensor_rank == 1                 # cross -> (pseudo)vector
    assert result.semantic_tag == "AxialVector"
    assert compatible(p, p, Operator.CROSS)


def test_cross_rejects_non_polar_vectors() -> None:
    with pytest.raises(SemanticTypeError) as excinfo:
        check_compatible(affine("Velocity"), affine("Velocity"), Operator.CROSS)
    assert "CROSS" in str(excinfo.value)
