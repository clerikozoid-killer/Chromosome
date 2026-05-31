"""L1.5 semantic compatibility — stacked on top of L1 dimensional pruning.

The L1 functions ``check_add`` / ``check_subtract`` remain the single source of
*dimensional* truth. This module reuses them for the dimension gate and adds the
*semantic* layer (tag + tensor rank, plus whitelisted fusions) on top. It never
re-implements ``a.dimension == b.dimension``.

Only ``ADD``/``SUBTRACT`` are handled here; ``DOT``/``CROSS`` (Task 4) and
``MULTIPLY``/``DIVIDE`` (Task 5) are added in later tasks.
"""

from __future__ import annotations

from dbse.contracts.affine import AffineType
from dbse.dimensional import DimensionError, check_add, check_subtract
from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import _TAGS, ADDITIVE_FUSIONS


def compatible(a: AffineType, b: AffineType, op: Operator) -> bool:
    """Predicate form of :func:`check_compatible` (swallows both error types)."""
    try:
        check_compatible(a, b, op)
    except (DimensionError, SemanticTypeError):
        return False
    return True


def check_compatible(a: AffineType, b: AffineType, op: Operator) -> AffineType:
    """Validate ``a op b`` and return the resulting :class:`AffineType`.

    Raises :class:`~dbse.dimensional.DimensionError` if the *dimensions* are
    incompatible (the L1 gate), or :class:`SemanticTypeError` if the dimensions
    match but the *semantics* do not (the L1.5 gate).
    """
    if op in (Operator.ADD, Operator.SUBTRACT):
        return _check_additive(a, b, op)
    raise SemanticTypeError(f"Unsupported operator: {op!r}")


def _check_additive(a: AffineType, b: AffineType, op: Operator) -> AffineType:
    # Step 1: L1 dimensional pruning (REUSED, not duplicated).
    dim_gate = check_add if op is Operator.ADD else check_subtract
    dim_gate(a.dimension, b.dimension)  # raises DimensionError on mismatch

    # Step 2: L1.5 semantic layer on top.
    if a.semantic_tag == b.semantic_tag and a.tensor_rank == b.tensor_rank:
        return AffineType(a.dimension, a.semantic_tag, a.tensor_rank, a.frame_of_reference)

    fused = ADDITIVE_FUSIONS.get(frozenset({a.semantic_tag, b.semantic_tag}))
    if fused is not None and a.tensor_rank == b.tensor_rank:
        spec = _TAGS[fused]
        return AffineType(a.dimension, fused, spec.tensor_rank, a.frame_of_reference)

    raise SemanticTypeError(_mismatch_message(a, b, op))


def _additive_suggestion() -> str:
    examples = [
        f"{' + '.join(sorted(pair))} -> {result}"
        for pair, result in ADDITIVE_FUSIONS.items()
    ]
    return "Did you mean: " + "; ".join(examples) + "?"


def _mismatch_message(a: AffineType, b: AffineType, op: Operator) -> str:
    return (
        "Semantic mismatch at L1.5\n"
        f"  Left:  {a}\n"
        f"  Right: {b}\n"
        f"  Operation: {op.name}\n"
        f"  Suggestion: {_additive_suggestion()}"
    )
