"""L1.5 semantic compatibility — stacked on top of L1 dimensional pruning.

The L1 functions ``check_add`` / ``check_subtract`` remain the single source of
*dimensional* truth. This module reuses them for the dimension gate and adds the
*semantic* layer (tag + tensor rank, plus whitelisted fusions) on top. It never
re-implements ``a.dimension == b.dimension``.

``ADD``/``SUBTRACT``, ``DOT`` and ``CROSS`` are handled here; ``MULTIPLY``/``DIVIDE``
(Task 5) are added in a later task.
"""

from __future__ import annotations

from dbse.contracts.affine import AffineType
from dbse.dimensional import DimensionError, check_add, check_subtract
from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import _TAGS, ADDITIVE_FUSIONS

# Structural (non-registry) tags used by tensor operators.
_SCALAR = "Scalar"
_POLAR_VECTOR = "PolarVector"
_AXIAL_VECTOR = "AxialVector"


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
    if op is Operator.DOT:
        return _check_dot(a, b)
    if op is Operator.CROSS:
        return _check_cross(a, b)
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

    raise SemanticTypeError(_mismatch_message(a, b, op, _additive_suggestion()))


def _check_dot(a: AffineType, b: AffineType) -> AffineType:
    if a.tensor_rank == 1 and b.tensor_rank == 1 and a.dimension == b.dimension:
        return AffineType(a.dimension * b.dimension, _SCALAR, tensor_rank=0)
    raise SemanticTypeError(
        _mismatch_message(a, b, Operator.DOT, "DOT requires two rank-1 vectors of equal dimension.")
    )


def _check_cross(a: AffineType, b: AffineType) -> AffineType:
    if a.semantic_tag == b.semantic_tag == _POLAR_VECTOR:
        return AffineType(a.dimension * b.dimension, _AXIAL_VECTOR, tensor_rank=1)
    raise SemanticTypeError(
        _mismatch_message(a, b, Operator.CROSS, "CROSS requires two PolarVector operands.")
    )


def _additive_suggestion() -> str:
    examples = [
        f"{' + '.join(sorted(pair))} -> {result}"
        for pair, result in ADDITIVE_FUSIONS.items()
    ]
    return "Did you mean: " + "; ".join(examples) + "?"


def _mismatch_message(a: AffineType, b: AffineType, op: Operator, suggestion: str) -> str:
    return (
        "Semantic mismatch at L1.5\n"
        f"  Left:  {a}\n"
        f"  Right: {b}\n"
        f"  Operation: {op.name}\n"
        f"  Suggestion: {suggestion}"
    )
