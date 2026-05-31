"""Cross-cutting contract: proof levels, violations, Tinfo.

These types travel through the whole pipeline and end up in the API response.
``compute_tinfo`` heuristics arrive in Stage 6; here we only fix the data shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProofLevel(Enum):
    """Confidence/derivation level of a result (see spec §3)."""

    P0 = "AXIOMATIC_PROOF"      # proved by Z3 from Core axioms
    P1 = "VERIFIED_NUMERIC"     # Z3-verified + numeric
    P2 = "NUMERIC_ONLY"         # numeric solution only
    P3 = "MODEL_BREAKDOWN"      # an invariant was violated; model inapplicable
    P4 = "HEURISTIC"            # heuristic, Tinfo > 0.5


class Severity(Enum):
    CRITICAL = "critical"
    SOFT = "soft"


@dataclass(frozen=True, slots=True)
class Violation:
    """A breached invariant, recorded by the Continuous Invariant Monitor (L5)."""

    invariant: str
    severity: Severity
    time: float | None = None
    value: float | None = None
    threshold: float | None = None
    message: str = ""


@dataclass(slots=True)
class Proof:
    """The provenance bundle attached to every solution."""

    level: ProofLevel = ProofLevel.P2
    tinfo: float = 0.0
    confidence: float = 1.0
    solver_path: list[str] = field(default_factory=list)
    z3_steps: list[str] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
