"""Validate styled text against skeleton numbers and metaphor policy."""

from __future__ import annotations

import re

from dbse.expression.errors import ExpressionError
from dbse.expression.schema import ExpressionOutput

_NUM = re.compile(r"\d+\.?\d*")


def validate_expression(
    skeleton: str,
    output: ExpressionOutput,
    *,
    forbidden: set[str],
    whitelist: set[str],
) -> None:
    nums = set(_NUM.findall(skeleton))
    for field in (output.eli5, output.academic, output.business):
        folded = field.casefold()
        for bad in forbidden:
            if bad.casefold() in folded:
                raise ExpressionError(f"forbidden metaphor {bad!r} in styled text")
        for num in nums:
            if num not in field:
                raise ExpressionError(f"missing numeric token {num!r} from skeleton")
    for m in output.metaphors_used:
        if m not in whitelist:
            raise ExpressionError(f"metaphor {m!r} not in whitelist")
