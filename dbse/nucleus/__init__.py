"""L5 NUCLEUS — SymPy algebraic solver + proof assembly (Stage 6)."""

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.solve_algebraic import AlgebraicResult, solve_algebraic
from dbse.nucleus.tinfo import assign_proof_level, compute_tinfo

__all__ = [
    "AlgebraicResult",
    "NucleusError",
    "STANDARD_GRAVITY",
    "assign_proof_level",
    "compute_tinfo",
    "solve_algebraic",
]
