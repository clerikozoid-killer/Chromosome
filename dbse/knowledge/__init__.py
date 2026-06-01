"""Core vs Hypothesis knowledge layers (Stage 11)."""

from dbse.knowledge.core import CORE, Axiom, CoreTruthLayer
from dbse.knowledge.errors import CoreViolationError
from dbse.knowledge.guard import assert_no_core_violation
from dbse.knowledge.hypothesis import Hypothesis, HypothesisLayer

__all__ = [
    "CORE",
    "Axiom",
    "CoreTruthLayer",
    "CoreViolationError",
    "Hypothesis",
    "HypothesisLayer",
    "assert_no_core_violation",
]
