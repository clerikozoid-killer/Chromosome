"""L1 dimensional rules used by the type checker and the solver."""

from __future__ import annotations

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional.errors import DimensionError

TRANSCENDENTAL: frozenset[str] = frozenset(
    {"sin", "cos", "tan", "asin", "acos", "atan",
     "exp", "log", "ln", "sinh", "cosh", "tanh"}
)


def check_add(left: Dimension, right: Dimension) -> Dimension:
    """Addition requires identical dimensions; returns that dimension."""
    if left != right:
        raise DimensionError(
            f"Cannot add quantities of unlike dimension: {left} + {right}"
        )
    return left


def check_subtract(left: Dimension, right: Dimension) -> Dimension:
    """Subtraction requires identical dimensions; returns that dimension."""
    if left != right:
        raise DimensionError(
            f"Cannot subtract quantities of unlike dimension: {left} - {right}"
        )
    return left


def check_transcendental(func: str, arg: Dimension) -> Dimension:
    """A transcendental function requires a dimensionless argument."""
    if not arg.is_dimensionless:
        raise DimensionError(
            f"Argument of {func}() must be dimensionless, got {arg}"
        )
    return DIMENSIONLESS
