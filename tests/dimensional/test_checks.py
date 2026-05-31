"""L1 unit tests: dimensional rules and the DimensionError."""

from __future__ import annotations

import pytest

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional import (
    TRANSCENDENTAL,
    DimensionError,
    check_add,
    check_subtract,
    check_transcendental,
)

_J = Dimension.of(1, 2, -2)
_N = Dimension.of(1, 1, -2)


def test_dimension_error_is_a_value_error() -> None:
    assert issubclass(DimensionError, ValueError)
    with pytest.raises(DimensionError):
        raise DimensionError("boom")


def test_check_add_allows_equal_dimensions() -> None:
    assert check_add(_J, _J) == _J


def test_check_add_rejects_unequal_dimensions() -> None:
    # 1 J + 1 N must be rejected purely on dimensions.
    with pytest.raises(DimensionError):
        check_add(_J, _N)


def test_check_subtract_rejects_unequal_dimensions() -> None:
    with pytest.raises(DimensionError):
        check_subtract(_J, _N)


def test_transcendental_requires_dimensionless_argument() -> None:
    # sin(5 kg) is rejected.
    with pytest.raises(DimensionError):
        check_transcendental("sin", Dimension.of(1))


def test_transcendental_accepts_dimensionless_argument() -> None:
    assert check_transcendental("exp", DIMENSIONLESS) == DIMENSIONLESS


def test_check_subtract_allows_equal_dimensions() -> None:
    assert check_subtract(_J, _J) == _J


def test_transcendental_set_contains_common_functions() -> None:
    assert {"sin", "cos", "exp", "log"} <= TRANSCENDENTAL
