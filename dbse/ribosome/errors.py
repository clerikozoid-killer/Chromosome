"""L3 error type."""

from __future__ import annotations


class RibosomeError(ValueError):
    """Raised when MEMBRANE output cannot be compiled into a valid AST."""
