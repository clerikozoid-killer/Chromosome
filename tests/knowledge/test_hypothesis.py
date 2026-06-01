"""L11 HypothesisLayer tests."""

from __future__ import annotations

import pytest

from dbse.knowledge.errors import CoreViolationError
from dbse.knowledge.hypothesis import Hypothesis, HypothesisLayer


def test_add_hypothesis_rejects_low_confidence() -> None:
    layer = HypothesisLayer()
    ok = layer.add_hypothesis(
        Hypothesis(id="h1", statement="F = k*x", confidence=0.05),
    )
    assert ok is False
    assert layer.hypotheses == {}


def test_add_hypothesis_accepts_valid_statement() -> None:
    layer = HypothesisLayer()
    ok = layer.add_hypothesis(
        Hypothesis(id="h1", statement="F = k*x", confidence=0.5),
    )
    assert ok is True
    assert layer.hypotheses["h1"].statement == "F = k*x"


def test_add_hypothesis_rejects_crispr_attack() -> None:
    layer = HypothesisLayer()
    with pytest.raises(CoreViolationError, match="newton_2"):
        layer.add_hypothesis(
            Hypothesis(id="evil", statement="F = m * a^2", confidence=0.9),
        )
