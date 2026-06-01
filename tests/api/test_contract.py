"""L12 API contract shape validation (spec §5)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from dbse.api.app import app

SOLVE_RESPONSE_KEYS = frozenset(
    {
        "request_id",
        "timestamp",
        "model_lattice",
        "solution",
        "proof",
        "expression",
        "visualizations",
        "halted",
        "halt_reason",
    },
)

CLARIFY_RESPONSE_KEYS = frozenset(
    {
        "status",
        "ambiguity_temperature",
        "candidates",
    },
)


def test_solve_response_keys_match_contract() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v5/solve",
        json={
            "query": "mass 100 g force",
            "context": {"domain_hint": "classical_mechanics"},
        },
    )
    assert response.status_code == 200
    assert set(response.json().keys()) == SOLVE_RESPONSE_KEYS


def test_clarify_response_keys_match_contract() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v5/clarify",
        json={"query": "Сколько стоит яблоко?"},
    )
    assert response.status_code == 200
    assert set(response.json().keys()) == CLARIFY_RESPONSE_KEYS
