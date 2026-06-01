"""L7 expression validator tests."""

from __future__ import annotations

import pytest

from dbse.expression.errors import ExpressionError
from dbse.expression.fallback import style_fallback
from dbse.expression.schema import ExpressionOutput
from dbse.expression.validator import validate_expression
from dbse.expression.whitelist import DEFAULT_METAPHOR_WHITELIST


def test_validator_rejects_forbidden_metaphor() -> None:
    skeleton = "Масса 0.100 kg, сила 0.981 N."
    out = ExpressionOutput(
        eli5="Яблоко хочет упасть.",
        academic="Согласно расчёту: масса 0.100 kg.",
        business="Итог: 0.981 N.",
        metaphors_used=[],
    )
    with pytest.raises(ExpressionError, match="forbidden metaphor"):
        validate_expression(
            skeleton,
            out,
            forbidden={"хочет"},
            whitelist=set(DEFAULT_METAPHOR_WHITELIST),
        )


def test_validator_accepts_clean_fallback() -> None:
    skeleton = "Масса 0.100 kg, сила 0.981 N."
    out = style_fallback(skeleton, value=0.980665, unit="N")
    validate_expression(
        skeleton,
        out,
        forbidden={"хочет", "любит"},
        whitelist=set(DEFAULT_METAPHOR_WHITELIST),
    )


def test_validator_rejects_metaphor_not_in_whitelist() -> None:
    skeleton = "Сила 0.981 N."
    out = ExpressionOutput(
        eli5="Сила 0.981 N.",
        academic="Сила 0.981 N.",
        business="Сила 0.981 N.",
        metaphors_used=["космос"],
    )
    with pytest.raises(ExpressionError, match="not in whitelist"):
        validate_expression(
            skeleton,
            out,
            forbidden=set(),
            whitelist=set(DEFAULT_METAPHOR_WHITELIST),
        )
