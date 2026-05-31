"""L1.5 unit tests: semantic compatibility rules and SemanticTypeError."""

from __future__ import annotations

import pytest

from dbse.semantic import Operator, SemanticTypeError


def test_semantic_type_error_is_a_type_error() -> None:
    assert issubclass(SemanticTypeError, TypeError)
    with pytest.raises(SemanticTypeError):
        raise SemanticTypeError("boom")


def test_operator_has_the_six_kinds() -> None:
    names = {op.name for op in Operator}
    assert names == {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "DOT", "CROSS"}
