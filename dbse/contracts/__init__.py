"""Core data contracts shared by all layers (fixed early, Stage 0)."""

from dbse.contracts.affine import AffineType
from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.context import HaltReason, PipelineContext, TraceEntry
from dbse.contracts.dimensions import BASIS, DIMENSIONLESS, Dimension
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.contracts.proof import Proof, ProofLevel, Severity, Violation

__all__ = [
    "AST",
    "BASIS",
    "DIMENSIONLESS",
    "ASTNode",
    "AffineType",
    "Constraint",
    "Dimension",
    "DomainModel",
    "HaltReason",
    "Invariant",
    "PipelineContext",
    "Proof",
    "ProofLevel",
    "Severity",
    "TraceEntry",
    "Violation",
]
