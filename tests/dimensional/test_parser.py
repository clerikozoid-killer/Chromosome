"""L1 unit tests: the unit-expression parser."""

from __future__ import annotations

import pytest

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional import DimensionError, parse_unit

PARSE_TABLE: list[tuple[str, Dimension]] = [
    ("", DIMENSIONLESS),
    ("1", DIMENSIONLESS),
    ("kg", Dimension.of(1)),
    ("m/s", Dimension.of(0, 1, -1)),
    ("m/s^2", Dimension.of(0, 1, -2)),
    ("m*s^-2", Dimension.of(0, 1, -2)),
    ("kg*m/s^2", Dimension.of(1, 1, -2)),       # == N
    ("kg m / s^2", Dimension.of(1, 1, -2)),      # implicit multiplication
    ("m^3", Dimension.of(0, 3)),
    ("1/s", Dimension.of(0, 0, -1)),             # == Hz
    ("N*m", Dimension.of(1, 2, -2)),             # == J
    ("kg*m^2/s^2", Dimension.of(1, 2, -2)),      # == J
]


@pytest.mark.parametrize(("text", "expected"), PARSE_TABLE)
def test_parse_unit_expressions(text: str, expected: Dimension) -> None:
    assert parse_unit(text) == expected


def test_named_unit_equals_its_composition() -> None:
    assert parse_unit("N") == parse_unit("kg*m/s^2")
    assert parse_unit("J") == parse_unit("N*m")
    assert parse_unit("Pa") == parse_unit("N/m^2")


def test_caret_without_exponent_raises() -> None:
    with pytest.raises(DimensionError):
        parse_unit("m^")


def test_unknown_unit_in_expression_raises() -> None:
    with pytest.raises(DimensionError):
        parse_unit("kg*zorp")
