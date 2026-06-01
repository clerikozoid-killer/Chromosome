"""Frozen Core truth layer — axioms and version token for cache invalidation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Axiom:
    statement: str
    domain: str


_AXIOMS: dict[str, Axiom] = {
    "newton_2": Axiom("F = m*a", "classical_mechanics"),
    "conservation_energy": Axiom("dE/dt = 0", "closed_system"),
    "excluded_middle": Axiom("P or not P", "logic"),
}


class CoreTruthLayer:
    __frozen__ = True
    axioms: MappingProxyType[str, Axiom] = MappingProxyType(_AXIOMS)

    @classmethod
    def version_token(cls) -> str:
        payload = {
            k: {"statement": v.statement, "domain": v.domain}
            for k, v in cls.axioms.items()
        }
        raw = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()[:8]


CORE = CoreTruthLayer()
