"""L5 unit tests: NucleusError."""

from __future__ import annotations

import pytest

from dbse.nucleus import NucleusError


def test_nucleus_error_is_a_value_error() -> None:
    assert issubclass(NucleusError, ValueError)
    with pytest.raises(NucleusError):
        raise NucleusError("boom")
