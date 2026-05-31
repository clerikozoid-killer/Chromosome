from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NarrativeNode:
    node_id: str
    template: str
    bindings: dict[str, Any]
    allowed_verbs: tuple[str, ...]
    forbidden_metaphors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "template": self.template,
            "bindings": self.bindings,
            "allowed_verbs": list(self.allowed_verbs),
            "forbidden_metaphors": list(self.forbidden_metaphors),
        }


@dataclass(frozen=True, slots=True)
class NarrativeGraph:
    nodes: tuple[NarrativeNode, ...]
