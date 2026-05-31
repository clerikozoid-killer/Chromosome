"""L0 unit tests: the MEMBRANE output schema and MembraneError."""

from __future__ import annotations

import pytest

from dbse.membrane import MembraneError


def test_membrane_error_is_a_value_error() -> None:
    assert issubclass(MembraneError, ValueError)
    with pytest.raises(MembraneError):
        raise MembraneError("boom")
