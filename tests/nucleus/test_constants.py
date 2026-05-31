"""L5 unit tests: physical constants."""

from __future__ import annotations

from dbse.nucleus.constants import STANDARD_GRAVITY


def test_standard_gravity_is_positive_si() -> None:
    assert STANDARD_GRAVITY > 9.8
    assert STANDARD_GRAVITY < 9.82
