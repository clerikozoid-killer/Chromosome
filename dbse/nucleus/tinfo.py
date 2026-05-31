"""Tinfo heuristics and proof-level assignment (spec §3)."""

from __future__ import annotations

from dbse.contracts.proof import Proof, ProofLevel

_TAG_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("heuristic:", 0.1),
    ("approx:", 0.2),
    ("linearize:", 0.3),
    ("domain_switch:", 0.4),
)


def compute_tinfo(proof: Proof) -> float:
    """Return information temperature in [0, 1] from solver_path tags."""
    total = 0.0
    for step in proof.solver_path:
        for prefix, weight in _TAG_WEIGHTS:
            if step.startswith(prefix):
                total += weight
                break
    return min(total, 1.0)


def assign_proof_level(proof: Proof) -> tuple[ProofLevel, float]:
    """Derive ProofLevel and confidence from the current proof bundle."""
    if proof.violations:
        return ProofLevel.P3, 0.0
    tinfo = compute_tinfo(proof)
    if tinfo >= 0.5:
        return ProofLevel.P4, max(0.0, 1.0 - tinfo)
    return ProofLevel.P2, max(0.0, 1.0 - tinfo)
