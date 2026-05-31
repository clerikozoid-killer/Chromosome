"""L0.5 unit tests: the rule-based query classifier and routing."""

from __future__ import annotations

import pytest

from dbse.sts import ROUTES, QueryType, classify


def test_physics_compute_when_quantities_present() -> None:
    assert classify("the force on a 0.1 kg apple", has_quantities=True) is QueryType.PHYSICS_COMPUTE


def test_physics_compute_detects_inline_quantity_without_flag() -> None:
    # A bare number+unit in the text is enough.
    assert classify("how fast after 5 s") is QueryType.PHYSICS_COMPUTE


def test_math_prove() -> None:
    assert classify("prove that sqrt(2) is irrational") is QueryType.MATH_PROVE


def test_definition() -> None:
    assert classify("what is entropy") is QueryType.DEFINITION


def test_opinion() -> None:
    assert classify("what is the best programming language?") is QueryType.OPINION


def test_opinion_beats_definition_when_both_markers_present() -> None:
    # "what is" (definition) AND "best" (opinion) -> opinion wins (checked first).
    assert classify("what is the most beautiful equation?") is QueryType.OPINION


def test_ambiguous_when_no_signal() -> None:
    assert classify("apple") is QueryType.AMBIGUOUS


def test_routes_cover_every_query_type() -> None:
    assert set(ROUTES) == set(QueryType)
    assert ROUTES[QueryType.PHYSICS_COMPUTE] == "full_pipeline"
    assert ROUTES[QueryType.MATH_PROVE] == "nucleus_only"
    assert ROUTES[QueryType.DEFINITION] == "expression_only"
    assert ROUTES[QueryType.OPINION] == "unhandled"
    assert ROUTES[QueryType.AMBIGUOUS] == "model_lattice"


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("compute the force on a 2 kg mass", QueryType.PHYSICS_COMPUTE),
        ("prove the theorem", QueryType.MATH_PROVE),
        ("define momentum", QueryType.DEFINITION),
        ("which is the best phone", QueryType.OPINION),
        ("banana", QueryType.AMBIGUOUS),
    ],
)
def test_reference_queries_route_correctly(query: str, expected: QueryType) -> None:
    assert classify(query) is expected
