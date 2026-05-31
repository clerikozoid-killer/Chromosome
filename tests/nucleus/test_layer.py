"""L5 layer integration tests."""

from __future__ import annotations

from typing import Any

import pytest

from dbse.contracts import PipelineContext, ProofLevel
from dbse.layers.nucleus import Nucleus
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.ribosome.cache import SemanticCache


def _apple_membrane() -> dict[str, Any]:
    return {
        "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
        "quantities": [
            {"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"},
        ],
        "relations": [],
        "equations": [],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "force"},
    }


def test_nucleus_solves_apple_weight_with_proof() -> None:
    from dbse.contracts.ast import AST, ASTNode

    layer = Nucleus()
    ctx = PipelineContext(
        query="apple",
        config={"domain_hint": "classical_mechanics"},
        membrane=_apple_membrane(),
        ast=AST(
            root=ASTNode(kind="OBJECT", op="obj_1"),
            structure_class="Algebraic_Quantities",
            canonical_hash="abc123deadbeef01",
        ),
        domain_model="linear_friction",
    )
    out = layer.process(ctx)
    assert out.solution is not None
    assert out.solution["unit"] == "N"
    assert out.solution["value"] == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-9)
    assert out.proof is not None
    assert out.proof.level is ProofLevel.P2
    assert out.proof.tinfo == 0.0
    assert out.trace[-1].layer == "L5.NUCLEUS"
    assert out.trace[-1].note == "solved"


def test_nucleus_skips_when_solution_prefilled() -> None:
    layer = Nucleus()
    ctx = PipelineContext(
        query="cached",
        solution={"value": 1.0, "unit": "N"},
        ast=None,
    )
    out = layer.process(ctx)
    assert out.trace[-1].note == "skipped:already-solved"


def test_nucleus_ode_without_equation_records_solve_error() -> None:
    from dbse.contracts.ast import AST, ASTNode

    layer = Nucleus()
    ctx = PipelineContext(
        query="ode",
        ast=AST(root=ASTNode(kind="OBJECT", op="obj_1"), structure_class="LinearODE_Order1"),
    )
    out = layer.process(ctx)
    assert out.solution is None
    assert out.trace[-1].note == "solve-error"


def test_nucleus_stores_cache_on_miss() -> None:
    from dbse.contracts.ast import AST, ASTNode

    cache = SemanticCache(secret="nuc-test", ttl_seconds=60, max_entries=8)
    layer = Nucleus(cache=cache, cache_secret="nuc-test", core_version="core-nuc")
    digest = "feedface01234567"
    ctx = PipelineContext(
        query="apple",
        membrane=_apple_membrane(),
        ast=AST(
            root=ASTNode(kind="OBJECT", op="obj_1"),
            structure_class="Algebraic_Quantities",
            canonical_hash=digest,
        ),
    )
    layer.process(ctx)
    hit = cache.get(digest, core_version="core-nuc")
    assert hit is not None
    assert hit.solution["unit"] == "N"
