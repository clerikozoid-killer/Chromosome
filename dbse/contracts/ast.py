"""L3 contract: the intermediate representation (AST).

A minimal, frozen IR shared by the compiler (L3) and the solver (L5). Nodes carry
an operator/kind, ordered children, an optional literal value, optional binding
metadata and an optional :class:`AffineType` (attached during L1/L1.5 integration).

The canonicalization and hashing logic arrives in Stage 4; this is only the shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dbse.contracts.affine import AffineType


@dataclass(frozen=True, slots=True)
class ASTNode:
    """A single node of the intermediate representation.

    Attributes:
        kind: node category, e.g. ``"OBJECT"``, ``"QUANTITY"``, ``"OPERATOR"``.
        op: operator/label, e.g. ``"ADD"``, ``"mass"``, ``"F"`` (``None`` for leaves).
        children: ordered child nodes.
        value: literal value for leaf nodes (number, symbol name, ...).
        affine_type: semantic type attached during type-checking.
        bindings: free-form metadata used by narrative templates (L6).
    """

    kind: str
    op: str | None = None
    children: tuple[ASTNode, ...] = ()
    value: Any = None
    affine_type: AffineType | None = None
    bindings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AST:
    """Wrapper around a root node plus optional structural metadata."""

    root: ASTNode
    structure_class: str | None = None
    canonical_hash: str | None = None
