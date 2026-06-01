"""L7 ExpressionOutput schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dbse.expression.schema import ExpressionOutput


def test_expression_output_accepts_three_styles() -> None:
    out = ExpressionOutput(eli5="a", academic="b", business="c")
    assert out.metaphors_used == []


def test_expression_output_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ExpressionOutput(eli5="a", academic="b", business="c", rogue="x")  # type: ignore[call-arg]
