"""L1 unit tests: dimensional rules and the DimensionError."""

from __future__ import annotations

import pytest

from dbse.dimensional import DimensionError


def test_dimension_error_is_a_value_error() -> None:
    assert issubclass(DimensionError, ValueError)
    with pytest.raises(DimensionError):
        raise DimensionError("boom")
