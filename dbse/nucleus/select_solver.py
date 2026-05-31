"""Route AST structure classes to solver backends."""

from __future__ import annotations

from enum import Enum

from dbse.contracts.ast import AST
from dbse.nucleus.errors import NucleusError


class SolverKind(Enum):
    ALGEBRAIC = "algebraic"
    ODE = "ode"


def select_solver(ast: AST) -> SolverKind:
    """Pick the solver kind for ``ast.structure_class``."""
    cls = ast.structure_class or "Unknown"
    if cls == "Algebraic_Quantities":
        return SolverKind.ALGEBRAIC
    if cls == "LinearODE_Order1":
        return SolverKind.ODE
    raise NucleusError(f"Unsupported structure class: {cls!r}")
