"""L7 EXPRESSION GENES — constrained styling (schema, validator, fallback)."""

from dbse.expression.errors import ExpressionError
from dbse.expression.fallback import style_fallback
from dbse.expression.schema import ExpressionOutput
from dbse.expression.validator import validate_expression
from dbse.expression.whitelist import DEFAULT_METAPHOR_WHITELIST

__all__ = [
    "DEFAULT_METAPHOR_WHITELIST",
    "ExpressionError",
    "ExpressionOutput",
    "style_fallback",
    "validate_expression",
]
