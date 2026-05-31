"""L3 layer integration tests."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.layers.ribosome import Ribosome
from dbse.ribosome.cache import CacheEntry, SemanticCache


def test_ribosome_compiles_membrane_into_annotated_ast() -> None:
    layer = Ribosome()
    ctx = PipelineContext(
        query="ignored",
        membrane={
            "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
            "quantities": [
                {"ref": "obj_1", "property": "mass", "value": 1.0, "unit": "kg"},
            ],
            "relations": [],
            "equations": [],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "mass"},
        },
    )
    out = layer.process(ctx)
    assert out.ast is not None
    assert out.ast.structure_class == "Algebraic_Quantities"
    assert out.ast.canonical_hash is not None
    assert len(out.ast.canonical_hash) == 16
    assert out.trace[-1].layer == "L3.RIBOSOME"
    assert out.trace[-1].note == "compiled"


def test_ribosome_cache_hit_skips_recompute_and_prefills_solution() -> None:
    cache = SemanticCache(secret="layer-test", ttl_seconds=60, max_entries=8)
    layer = Ribosome(cache=cache, cache_secret="layer-test", core_version="core-test")
    membrane = {
        "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
        "quantities": [],
        "relations": [],
        "equations": [
            {"object_ref": "obj_1", "state": "v", "constant": 1.0, "linear_coeff": -0.1},
        ],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "velocity"},
    }
    ctx1 = PipelineContext(query="q1", membrane=membrane, config={"cache_secret": "layer-test"})
    out1 = layer.process(ctx1)
    assert out1.solution is None
    assert out1.ast is not None
    digest = out1.ast.canonical_hash
    assert digest is not None

    cache.put(
        digest,
        CacheEntry(
            ast=out1.ast,
            solution={"status": "solved", "via": "nucleus"},
            proof_level="P2",
            tinfo=0.05,
        ),
        core_version="core-test",
    )

    ctx2 = PipelineContext(query="q2", membrane=membrane, config={"cache_secret": "layer-test"})
    out2 = layer.process(ctx2)
    assert out2.solution == {"status": "solved", "via": "nucleus"}
    assert out2.trace[-1].note == "cache-hit"
