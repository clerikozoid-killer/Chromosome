"""L5 error type."""

from __future__ import annotations


class NucleusError(ValueError):
    """Raised when NUCLEUS cannot solve or verify a problem (L5).

    Examples: unsupported structure class, missing target quantity, or
    SymPy evaluation failure.
    """
