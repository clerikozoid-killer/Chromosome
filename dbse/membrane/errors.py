"""L0 error type."""

from __future__ import annotations


class MembraneError(ValueError):
    """Raised when the MEMBRANE output fails strict schema validation (L0).

    A ``MembraneError`` means the parsed payload escaped the allowed shape — an
    off-schema field, a forbidden node type (``INVARIANT``/``CONTEXT``/``OPERATOR``),
    an unknown ``question_type``, an unresolvable unit, or a dangling reference.
    The MEMBRANE layer turns this into a ``HaltReason.CLARIFICATION`` rather than
    silently "completing" the input (the v5.0 prompt-injection mitigation).
    """
