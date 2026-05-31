"""L1.5 adversarial tests (QA-gate level 5): same-dimension semantic collisions."""

from __future__ import annotations

import pytest

from dbse.semantic import Operator, SemanticTypeError, affine, check_compatible

# Pairs that share a dimension but must NOT be addable.
_COLLISIONS = [
    ("Energy", "Torque"),
    ("Torque", "Energy"),
    ("Heat", "Torque"),
    ("Work", "Torque"),
    ("InternalEnergy", "Torque"),
]


@pytest.mark.parametrize(("left", "right"), _COLLISIONS)
def test_same_dimension_collisions_are_rejected(left: str, right: str) -> None:
    assert affine(left).dimension == affine(right).dimension  # same dimension
    with pytest.raises(SemanticTypeError):
        check_compatible(affine(left), affine(right), Operator.ADD)


def test_the_canonical_energy_plus_torque_attack() -> None:
    # The vulnerability the whole stage exists to close.
    with pytest.raises(SemanticTypeError) as excinfo:
        check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
    assert "Semantic mismatch at L1.5" in str(excinfo.value)
