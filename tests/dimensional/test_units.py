"""L1 unit tests: named-unit registry and SI-prefix resolution."""

from __future__ import annotations

import pytest

from dbse.contracts.dimensions import Dimension
from dbse.dimensional import DimensionError, resolve

# (symbol, expected dimension) — magnitude is irrelevant at L1.
RESOLVE_TABLE: list[tuple[str, Dimension]] = [
    ("kg", Dimension.of(1)),
    ("g", Dimension.of(1)),
    ("m", Dimension.of(0, 1)),
    ("s", Dimension.of(0, 0, 1)),
    ("A", Dimension.of(0, 0, 0, 1)),
    ("K", Dimension.of(0, 0, 0, 0, 1)),
    ("mol", Dimension.of(0, 0, 0, 0, 0, 1)),
    ("cd", Dimension.of(0, 0, 0, 0, 0, 0, 1)),
    ("N", Dimension.of(1, 1, -2)),
    ("J", Dimension.of(1, 2, -2)),
    ("W", Dimension.of(1, 2, -3)),
    ("Pa", Dimension.of(1, -1, -2)),
    ("Hz", Dimension.of(0, 0, -1)),
    ("C", Dimension.of(0, 0, 1, 1)),
    ("V", Dimension.of(1, 2, -3, -1)),
    ("ohm", Dimension.of(1, 2, -3, -2)),
    ("Ω", Dimension.of(1, 2, -3, -2)),
    # prefixes do not change the dimension:
    ("km", Dimension.of(0, 1)),
    ("mm", Dimension.of(0, 1)),
    ("mg", Dimension.of(1)),
    ("kN", Dimension.of(1, 1, -2)),
    ("MHz", Dimension.of(0, 0, -1)),
    ("kPa", Dimension.of(1, -1, -2)),
    ("µm", Dimension.of(0, 1)),
]


@pytest.mark.parametrize(("symbol", "expected"), RESOLVE_TABLE)
def test_resolve_known_symbols(symbol: str, expected: Dimension) -> None:
    assert resolve(symbol) == expected


def test_resolve_unknown_symbol_raises() -> None:
    with pytest.raises(DimensionError):
        resolve("zorp")


def test_registry_has_at_least_30_named_units() -> None:
    from dbse.dimensional.units import _UNITS

    assert len(_UNITS) >= 30
