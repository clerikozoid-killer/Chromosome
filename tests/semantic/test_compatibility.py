"""L1.5 unit tests: semantic compatibility rules and SemanticTypeError."""

from __future__ import annotations

import pytest

from dbse.contracts.affine import AffineType
from dbse.contracts.dimensions import Dimension
from dbse.dimensional import DimensionError
from dbse.semantic import (
    Operator,
    SemanticTypeError,
    affine,
    check_compatible,
    combine,
    compatible,
    is_ambiguous,
)


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


def test_subtract_work_and_heat_does_not_fuse() -> None:
    # Fusion (Work + Heat -> InternalEnergy) is an additive identity; subtraction
    # of unlike tags must be rejected, not fused.
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Work"), affine("Heat"), Operator.SUBTRACT)
    assert not compatible(affine("Work"), affine("Heat"), Operator.SUBTRACT)


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


def test_cross_rejects_rank_zero_polar_vector() -> None:
    # A "PolarVector"-tagged scalar must not pass CROSS.
    scalar_polar = AffineType(Dimension.of(0, 1), "PolarVector", tensor_rank=0)
    with pytest.raises(SemanticTypeError):
        check_compatible(scalar_polar, scalar_polar, Operator.CROSS)


def test_multiply_unambiguous_tag_force_times_velocity_is_power() -> None:
    result = combine(affine("Force"), affine("Velocity"), Operator.MULTIPLY)
    assert result.dimension == Dimension.of(1, 2, -3)   # power dimension
    assert result.semantic_tag == "Power"
    assert not is_ambiguous(result.semantic_tag)


def test_multiply_force_times_length_is_ambiguous_work_or_torque() -> None:
    result = combine(affine("Force"), affine("Length"), Operator.MULTIPLY)
    assert result.dimension == Dimension.of(1, 2, -2)
    assert is_ambiguous(result.semantic_tag)
    assert set(result.semantic_tag.split("|")) == {"Torque", "Work"}


def test_multiply_is_commutative_for_dimension_and_tag() -> None:
    ab = combine(affine("Force"), affine("Length"), Operator.MULTIPLY)
    ba = combine(affine("Length"), affine("Force"), Operator.MULTIPLY)
    assert ab.dimension == ba.dimension
    assert ab.semantic_tag == ba.semantic_tag


def test_multiply_or_divide_is_always_compatible() -> None:
    # Per the v5.0 spec, x/div never fail the semantic gate.
    assert compatible(affine("Energy"), affine("Torque"), Operator.MULTIPLY)
    assert compatible(affine("Energy"), affine("Torque"), Operator.DIVIDE)


def test_divide_energy_by_time_is_power() -> None:
    result = combine(affine("Energy"), affine("Time"), Operator.DIVIDE)
    assert result.dimension == Dimension.of(1, 2, -3)
    assert result.semantic_tag == "Power"


def test_divide_is_not_commutative_for_tag() -> None:
    # The ordered key matters: Energy/Time is Power, but Time/Energy is unknown.
    assert combine(affine("Energy"), affine("Time"), Operator.DIVIDE).semantic_tag == "Power"
    assert combine(affine("Time"), affine("Energy"), Operator.DIVIDE).semantic_tag == "Unknown"


def test_combine_resolved_tag_takes_its_registry_rank() -> None:
    # Force(r1) x Velocity(r1) -> Power, a scalar (rank 0 from the registry).
    power = combine(affine("Force"), affine("Velocity"), Operator.MULTIPLY)
    assert power.semantic_tag == "Power"
    assert power.tensor_rank == 0
    # Mass(r0) x Velocity(r1) -> Momentum, a rank-1 vector (from the registry).
    momentum = combine(affine("Mass"), affine("Velocity"), Operator.MULTIPLY)
    assert momentum.semantic_tag == "Momentum"
    assert momentum.tensor_rank == 1


def test_unknown_product_yields_unknown_tag() -> None:
    result = combine(affine("Heat"), affine("Length"), Operator.MULTIPLY)
    assert result.semantic_tag == "Unknown"
    assert result.dimension == Dimension.of(1, 3, -2)
