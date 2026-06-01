"""L7 adversarial styling tests (QA level 5)."""

from __future__ import annotations

import pytest

from dbse.expression.errors import ExpressionError
from dbse.expression.schema import ExpressionOutput
from dbse.expression.validator import validate_expression
from dbse.expression.whitelist import DEFAULT_METAPHOR_WHITELIST

FORBIDDEN = frozenset({"хочет", "любит", "думает", "мечтает"})


def test_anthropomorphic_injection_rejected() -> None:
    skeleton = "Масса 0.100 kg, сила 0.981 N."
    poisoned = ExpressionOutput(
        eli5="Яблоко хочет упасть на Землю с силой 0.981 N.",
        academic="Масса 0.100 kg, сила 0.981 N.",
        business="Масса 0.100 kg, сила 0.981 N.",
        metaphors_used=[],
    )
    with pytest.raises(ExpressionError, match="forbidden metaphor"):
        validate_expression(
            skeleton,
            poisoned,
            forbidden=set(FORBIDDEN),
            whitelist=set(DEFAULT_METAPHOR_WHITELIST),
        )
