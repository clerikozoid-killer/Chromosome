"""L3 unit tests: MEMBRANE → AST compilation."""

from __future__ import annotations

import pytest

from dbse.ribosome import RibosomeError


def test_ribosome_error_is_a_value_error() -> None:
    assert issubclass(RibosomeError, ValueError)
    with pytest.raises(RibosomeError):
        raise RibosomeError("boom")
