"""End-to-end Definition-of-Done: spec apple-weight query through L0..L7."""

from __future__ import annotations

import pytest

from dbse.contracts.proof import ProofLevel
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.pipeline import Pipeline

APPLE_QUERY = "С какой силой Земля притягивает яблоко массой 100г?"


def test_e2e_apple_weight_full_pipeline() -> None:
    ctx = Pipeline().run(
        APPLE_QUERY,
        config={"domain_hint": "classical_mechanics", "required_proof_level": "P2"},
    )
    assert not ctx.halted
    assert ctx.solution is not None
    assert ctx.solution["unit"] == "N"
    assert ctx.solution["value"] == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-6)
    assert ctx.proof is not None
    assert ctx.proof.level is ProofLevel.P2
    assert ctx.narrative is not None
    assert ctx.narrative.get("skeleton")
    assert ctx.expression is not None
    assert ctx.expression.get("eli5")
