"""L12 API schema tests."""

from __future__ import annotations

from dbse.api.schemas import ClarifyRequest, SolveContext, SolveRequest


def test_solve_request_parses_spec_example() -> None:
    body = SolveRequest(
        query="С какой силой Земля притягивает яблоко массой 100г?",
        context=SolveContext(domain_hint="classical_mechanics", precision="standard"),
        required_proof_level="P2",
        output_formats=["json"],
    )
    assert body.context is not None
    assert body.context.domain_hint == "classical_mechanics"


def test_clarify_request_minimal() -> None:
    body = ClarifyRequest(query="Сколько стоит яблоко?")
    assert body.query.startswith("Сколько")
