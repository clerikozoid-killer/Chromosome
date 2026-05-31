"""L4 unit tests: plugin registry."""

from __future__ import annotations

import pytest

from dbse.cytoplasm import CytoplasmError


def test_cytoplasm_error_is_a_value_error() -> None:
    assert issubclass(CytoplasmError, ValueError)
    with pytest.raises(CytoplasmError):
        raise CytoplasmError("boom")
