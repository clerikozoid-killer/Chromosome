"""L1.5 error type."""

from __future__ import annotations


class SemanticTypeError(TypeError):
    """Raised when two affine types are semantically incompatible (L1.5).

    Distinct from :class:`dbse.dimensional.DimensionError`: a ``SemanticTypeError``
    means the *dimensions matched* but the *semantics* did not — e.g. adding
    ``Energy`` to ``Torque``. Subclasses :class:`TypeError` per the v5.0 spec
    ("Semantic mismatch at L1.5").
    """
