"""Mutable Hypothesis layer — proposals gated by Core guard."""

from __future__ import annotations

from dataclasses import dataclass

from dbse.knowledge.guard import assert_no_core_violation


@dataclass
class Hypothesis:
    id: str
    statement: str
    confidence: float
    evidence_count: int = 0
    conflicts_with: list[str] | None = None


class HypothesisLayer:
    def __init__(self) -> None:
        self.hypotheses: dict[str, Hypothesis] = {}

    def add_hypothesis(self, h: Hypothesis) -> bool:
        if h.confidence < 0.1:
            return False
        assert_no_core_violation(h.statement)
        self.hypotheses[h.id] = h
        return True
