"""Signed LRU semantic cache for canonical AST hashes."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from dbse.contracts.ast import AST


@dataclass
class CacheEntry:
    """One cached solve result keyed by canonical hash."""

    ast: AST
    solution: dict[str, Any]
    proof_level: str
    tinfo: float
    hits: int = 0


@dataclass
class _StoredEntry:
    entry: CacheEntry
    signature: str
    created_at: float
    core_version: str


class SemanticCache:
    """LRU cache with HMAC integrity, TTL expiry, and core-version invalidation."""

    def __init__(
        self,
        *,
        secret: str,
        ttl_seconds: float = 3600.0,
        max_entries: int = 256,
    ) -> None:
        self._secret = secret.encode()
        self._ttl = ttl_seconds
        self._max = max_entries
        self._store: OrderedDict[str, _StoredEntry] = OrderedDict()

    def put(self, key: str, entry: CacheEntry, *, core_version: str) -> None:
        payload = self._serialize(entry)
        sig = self._sign(payload)
        self._store[key] = _StoredEntry(
            entry=entry,
            signature=sig,
            created_at=time.monotonic(),
            core_version=core_version,
        )
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def get(self, key: str, *, core_version: str) -> CacheEntry | None:
        stored = self._store.get(key)
        if stored is None:
            return None
        if stored.core_version != core_version:
            del self._store[key]
            return None
        if time.monotonic() - stored.created_at > self._ttl:
            del self._store[key]
            return None
        payload = self._serialize(stored.entry)
        if not hmac.compare_digest(self._sign(payload), stored.signature):
            del self._store[key]
            return None
        stored.entry.hits += 1
        self._store.move_to_end(key)
        return stored.entry

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _serialize(entry: CacheEntry) -> str:
        # AST metadata only — full tree serialization via structure_class + hash already on ast.
        data = {
            "structure_class": entry.ast.structure_class,
            "canonical_hash": entry.ast.canonical_hash,
            "solution": entry.solution,
            "proof_level": entry.proof_level,
            "tinfo": entry.tinfo,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
