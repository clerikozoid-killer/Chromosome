"""L3 adversarial tests: cache poisoning mitigation (vulnerability #9)."""

from __future__ import annotations

from dbse.contracts import AST, ASTNode
from dbse.ribosome.cache import CacheEntry, SemanticCache, _StoredEntry


def test_forged_entry_without_valid_hmac_is_rejected() -> None:
    cache = SemanticCache(secret="production-secret", ttl_seconds=3600, max_entries=16)
    cache._store["evil"] = _StoredEntry(  # noqa: SLF001
        entry=CacheEntry(
            ast=AST(root=ASTNode(kind="OBJECT", op="x", value="poison")),
            solution={"answer": "WRONG"},
            proof_level="P0",
            tinfo=0.0,
        ),
        signature="deadbeef" * 8,
        created_at=0.0,
        core_version="core-1",
    )
    assert cache.get("evil", core_version="core-1") is None
    assert "evil" not in cache._store  # noqa: SLF001 — evicted
