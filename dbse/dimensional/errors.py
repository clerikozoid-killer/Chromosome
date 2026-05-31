"""L1 error type."""

from __future__ import annotations


class DimensionError(ValueError):
    """Raised when a dimensional rule is violated (L1).

    Examples: adding quantities of unlike dimension, passing a dimensionful
    argument to a transcendental function, or parsing an unknown unit.
    """
