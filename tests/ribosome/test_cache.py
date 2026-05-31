"""L3 unit tests: signed semantic cache."""

from __future__ import annotations

import time

from dbse.contracts import AST, ASTNode
from dbse.ribosome.cache import CacheEntry, SemanticCache


def _dummy_ast() -> AST:
    return AST(root=ASTNode(kind="OBJECT", op="obj_1", value="x"))


def test_cache_put_get_round_trip_increments_hits() -> None:
    cache = SemanticCache(secret="test-secret", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(
        ast=_dummy_ast(),
        solution={"value": 42},
        proof_level="P2",
        tinfo=0.1,
    )
    cache.put("abc123", entry, core_version="core-1")
    got = cache.get("abc123", core_version="core-1")
    assert got is not None
    assert got.hits == 1
    assert got.solution == {"value": 42}


def test_cache_rejects_tampered_signature() -> None:
    cache = SemanticCache(secret="test-secret", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(ast=_dummy_ast(), solution={}, proof_level="P2", tinfo=0.0)
    cache.put("deadbeef", entry, core_version="core-1")
    # Simulate poisoning by mutating internal store after put
    raw = cache._store["deadbeef"]  # noqa: SLF001 — intentional adversarial setup
    raw.entry.solution = {"hacked": True}
    assert cache.get("deadbeef", core_version="core-1") is None


def test_cache_expires_after_ttl() -> None:
    cache = SemanticCache(secret="s", ttl_seconds=0, max_entries=10)
    entry = CacheEntry(ast=_dummy_ast(), solution={}, proof_level="P2", tinfo=0.0)
    cache.put("k", entry, core_version="core-1")
    time.sleep(0.01)
    assert cache.get("k", core_version="core-1") is None


def test_cache_invalidates_on_core_version_change() -> None:
    cache = SemanticCache(secret="s", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(ast=_dummy_ast(), solution={}, proof_level="P2", tinfo=0.0)
    cache.put("k", entry, core_version="core-1")
    assert cache.get("k", core_version="core-2") is None
