"""L12 context → API mapper tests."""

from __future__ import annotations

from dbse.api.mapper import context_to_clarify_response, context_to_solve_response
from dbse.contracts.context import HaltReason, PipelineContext
from dbse.contracts.proof import Proof, ProofLevel


def test_context_to_solve_response_includes_proof_and_halt() -> None:
    ctx = PipelineContext(
        query="q",
        solution={"value": 1.0, "unit": "N"},
        proof=Proof(level=ProofLevel.P2, tinfo=0.1, confidence=0.9),
        config={"_visualizations": {"mermaid": "graph TD"}},
    )
    resp = context_to_solve_response(ctx, request_id="req_test")
    assert resp["request_id"] == "req_test"
    assert resp["proof"]["level"] == "P2"
    assert resp["visualizations"]["mermaid"] == "graph TD"
    assert resp["halted"] is False


def test_context_to_clarify_response_uses_lattice_candidates() -> None:
    ctx = PipelineContext(
        query="ambiguous",
        halt_reason=HaltReason.AMBIGUITY_HALT,
        model_lattice={
            "ambiguity_temperature": 0.9,
            "candidates": [{"model": "fruit", "probability": 0.5}],
        },
    )
    resp = context_to_clarify_response(ctx)
    assert resp["status"] == "clarification_needed"
    assert resp["ambiguity_temperature"] == 0.9
    assert len(resp["candidates"]) == 1
