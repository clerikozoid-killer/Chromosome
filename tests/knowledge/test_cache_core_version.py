"""L11 core_version wiring to semantic cache."""

from __future__ import annotations

from dbse.contracts import AST, ASTNode
from dbse.knowledge.core import CORE
from dbse.layers.nucleus import Nucleus
from dbse.layers.ribosome import Ribosome
from dbse.pipeline import default_layers
from dbse.ribosome.cache import CacheEntry, SemanticCache


def _dummy_ast() -> AST:
    return AST(root=ASTNode(kind="OBJECT", op="obj_1", value="x"))


def test_default_layers_use_core_version_token() -> None:
    layers = default_layers()
    ribosome = next(layer for layer in layers if isinstance(layer, Ribosome))
    nucleus = next(layer for layer in layers if isinstance(layer, Nucleus))
    token = CORE.version_token()
    assert ribosome._core_version == token  # noqa: SLF001
    assert nucleus._core_version == token  # noqa: SLF001
    assert ribosome._cache is nucleus._cache  # noqa: SLF001


def test_cache_entry_invalidates_when_core_version_changes() -> None:
    cache = SemanticCache(secret="s", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(
        ast=_dummy_ast(),
        solution={"value": 1},
        proof_level="P2",
        tinfo=0.0,
    )
    v1 = CORE.version_token()
    cache.put("k", entry, core_version=v1)
    assert cache.get("k", core_version=v1) is not None
    assert cache.get("k", core_version="stale-core") is None
