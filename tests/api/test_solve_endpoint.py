"""L12 FastAPI solve/clarify endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dbse.api.app import app

pytest.importorskip("httpx")

client = TestClient(app)


def test_solve_apple_query_returns_200() -> None:
    response = client.post(
        "/api/v5/solve",
        json={
            "query": "С какой силой Земля притягивает яблоко массой 100г?",
            "context": {"domain_hint": "classical_mechanics", "precision": "standard"},
            "required_proof_level": "P2",
            "output_formats": ["json"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"].startswith("req_")
    assert data["solution"] is not None
    assert data["visualizations"] is not None
    assert "mermaid" in data["visualizations"]


def test_clarify_ambiguous_query_returns_candidates() -> None:
    response = client.post(
        "/api/v5/clarify",
        json={"query": "Сколько стоит яблоко?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert data["ambiguity_temperature"] >= 0.6
    assert data["candidates"]


def test_clarify_non_ambiguous_returns_400() -> None:
    response = client.post(
        "/api/v5/clarify",
        json={
            "query": "С какой силой Земля притягивает яблоко массой 100г?",
        },
    )
    assert response.status_code == 400
