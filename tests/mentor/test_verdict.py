"""Mentor verdict engine tests."""

from __future__ import annotations

from dbse.contracts.context import PipelineContext
from dbse.contracts.proof import Proof, ProofLevel
from dbse.mentor.cases import Case
from dbse.mentor.verdict import judge


def test_judge_passes_matching_solution() -> None:
    ctx = PipelineContext(
        query="q",
        solution={"value": 0.980665, "unit": "N"},
        proof=Proof(level=ProofLevel.P2),
    )
    case = Case(
        id="apple_weight",
        query="q",
        domain_hint="classical_mechanics",
        expected={"value": 0.980665, "unit": "N", "tolerance": 0.01},
        proof_level="P2",
        oracle="analytic",
    )
    verdict = judge(ctx, case)
    assert verdict.passed
    assert verdict.category == "ok"


def test_judge_fails_value_mismatch() -> None:
    ctx = PipelineContext(query="q", solution={"value": 1.0, "unit": "N"})
    case = Case(
        id="x",
        query="q",
        domain_hint="",
        expected={"value": 0.5, "tolerance": 0.01},
        proof_level="P2",
        oracle="analytic",
    )
    verdict = judge(ctx, case)
    assert not verdict.passed
    assert verdict.category == "solver"
