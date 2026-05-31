"""L1 property-based laws (QA-gate level 2)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.dimensional import parse_unit, resolve

_BASE_SYMBOLS = ["kg", "m", "s", "A", "K", "mol", "cd"]


@given(st.sampled_from(_BASE_SYMBOLS), st.integers(min_value=1, max_value=5))
def test_power_equals_repeated_multiplication(symbol: str, power: int) -> None:
    # "m^3" == "m*m*m"
    via_power = parse_unit(f"{symbol}^{power}")
    via_product = parse_unit("*".join([symbol] * power))
    assert via_power == via_product


@given(st.sampled_from(_BASE_SYMBOLS))
def test_multiply_then_divide_is_identity(symbol: str) -> None:
    # "kg*m/m" == "kg"
    assert parse_unit(f"kg*{symbol}/{symbol}") == resolve("kg")


@given(st.sampled_from(["k", "m", "M", "µ", "n"]), st.sampled_from(["m", "s", "g", "N", "Pa"]))
def test_prefix_does_not_change_dimension(prefix: str, unit: str) -> None:
    # A prefixed unit has the same dimension as the bare unit (magnitude aside).
    assert resolve(prefix + unit) == resolve(unit)
