"""L5 unit tests: Tinfo heuristics and proof level assignment."""

from __future__ import annotations

from dbse.contracts.proof import Proof, ProofLevel
from dbse.nucleus.tinfo import assign_proof_level, compute_tinfo


def test_compute_tinfo_zero_for_clean_path() -> None:
    proof = Proof(solver_path=["sympy:symbolic", "sympy:numeric"])
    assert compute_tinfo(proof) == 0.0


def test_compute_tinfo_weights_solver_path_tags() -> None:
    proof = Proof(
        solver_path=[
            "heuristic:assume_g",
            "approx:rounding",
            "linearize:small_angle",
            "domain_switch:z3-deferred",
        ]
    )
    assert compute_tinfo(proof) == 1.0


def test_compute_tinfo_clamped_at_one() -> None:
    proof = Proof(
        solver_path=[
            "heuristic:a",
            "approx:a",
            "linearize:a",
            "domain_switch:a",
            "heuristic:b",
            "approx:b",
        ]
    )
    assert compute_tinfo(proof) == 1.0


def test_assign_proof_level_p2_when_tinfo_low() -> None:
    proof = Proof(solver_path=["sympy:numeric"])
    level, confidence = assign_proof_level(proof)
    assert level is ProofLevel.P2
    assert confidence == 1.0


def test_assign_proof_level_p4_when_tinfo_high() -> None:
    proof = Proof(solver_path=["heuristic:guess"] * 6)
    level, _confidence = assign_proof_level(proof)
    assert level is ProofLevel.P4
