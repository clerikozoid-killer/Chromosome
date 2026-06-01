"""L11 knowledge errors."""

from __future__ import annotations


class CoreViolationError(RuntimeError):
    """Attempt to mutate or contradict Core axioms."""
