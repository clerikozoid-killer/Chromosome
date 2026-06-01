"""L11 pipeline guard on cytoplasm constraints."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.affine import AffineType
from dbse.contracts.context import HaltReason, PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.cytoplasm.registry import PluginRegistry
from dbse.layers.cytoplasm import Cytoplasm


class _MaliciousPlugin:
    domain: ClassVar[str] = "malicious_test"
    dimensionless_numbers: ClassVar[list[str]] = []

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        return {}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        return DomainModel(id="evil", label="evil")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [
            Constraint(
                expression="F = m * a^2",
                constraint_type="crispr",
            ),
        ]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return []


def test_malicious_constraint_halts_with_core_violation() -> None:
    registry = PluginRegistry()
    registry.register(_MaliciousPlugin())
    layer = Cytoplasm(registry=registry)
    ctx = PipelineContext(
        query="attack",
        config={"domain_hint": "malicious_test"},
        membrane={"quantities": []},
    )
    out = layer.process(ctx)
    assert out.halted
    assert out.halt_reason == HaltReason.CORE_VIOLATION
    assert out.constraints is None
    assert out.trace[-1].note == "core-violation"
