"""JSONL case bank loader for Mentor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    query: str
    domain_hint: str
    expected: dict[str, Any]
    proof_level: str
    oracle: str


def load_cases(path: Path) -> list[Case]:
    out: list[Case] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        if "id" not in raw or "query" not in raw:
            continue
        out.append(
            Case(
                id=str(raw["id"]),
                query=str(raw["query"]),
                domain_hint=str(raw.get("domain_hint", "")),
                expected=dict(raw.get("expected", {})),
                proof_level=str(raw.get("proof_level", "P2")),
                oracle=str(raw.get("oracle", "analytic")),
            ),
        )
    return out
