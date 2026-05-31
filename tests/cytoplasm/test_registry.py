"""L4 unit tests: plugin registry."""

from __future__ import annotations

from typing import ClassVar

import pytest

from dbse.contracts import AffineType, Constraint, DomainModel, Invariant, PipelineContext
from dbse.cytoplasm import CytoplasmError
from dbse.cytoplasm.plugin import DomainPlugin


def test_cytoplasm_error_is_a_value_error() -> None:
    assert issubclass(CytoplasmError, ValueError)
    with pytest.raises(CytoplasmError):
        raise CytoplasmError("boom")


class _EchoPlugin:
    domain: ClassVar[str] = "echo"
    dimensionless_numbers: ClassVar[list[str]] = ["beta"]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        return {"beta": float(ctx.config.get("beta", 0.0))}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        return DomainModel(id="echo_model", label="Echo")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [Constraint(expression="x = x", constraint_type="identity")]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return []


def test_domain_plugin_protocol_accepts_concrete_class() -> None:
    plugin: DomainPlugin = _EchoPlugin()
    assert plugin.domain == "echo"
    assert plugin.dimensionless_numbers == ["beta"]
