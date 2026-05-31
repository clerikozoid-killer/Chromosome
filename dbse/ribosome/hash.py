"""Canonical AST hashing."""

from __future__ import annotations

import hashlib

from dbse.contracts.ast import AST
from dbse.ribosome.classify import classify_structure
from dbse.ribosome.normalize import normalize_ast_tree, to_canonical


def canonical_hash(ast: AST) -> str:
    """Return a 16-hex-char structural hash: sha256(class + canonical form)[:16]."""
    normalized = normalize_ast_tree(ast)
    structure_class = classify_structure(normalized.root)
    normalized = AST(
        root=normalized.root,
        structure_class=structure_class,
        canonical_hash=normalized.canonical_hash,
    )
    payload = f"{structure_class}:{to_canonical(normalized.root)}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def annotate_ast(ast: AST) -> AST:
    """Normalize, classify, and attach metadata fields on the AST wrapper."""
    normalized = normalize_ast_tree(ast)
    structure_class = classify_structure(normalized.root)
    digest = canonical_hash(
        AST(root=normalized.root, structure_class=structure_class)
    )
    return AST(root=normalized.root, structure_class=structure_class, canonical_hash=digest)
