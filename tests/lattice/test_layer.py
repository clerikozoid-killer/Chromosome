"""L2 layer integration tests."""

from __future__ import annotations

from dbse.contracts.context import HaltReason
from dbse.pipeline import Pipeline


def test_ambiguous_query_halts_in_pipeline() -> None:
    ctx = Pipeline().run("Сколько стоит яблоко?")
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.AMBIGUITY_HALT
    assert ctx.model_lattice is not None


def test_physics_query_continues() -> None:
    ctx = Pipeline().run(
        "С какой силой Земля притягивает яблоко массой 100г?",
        config={"domain_hint": "classical_mechanics"},
    )
    assert not ctx.halted or ctx.halt_reason.value == "none"
