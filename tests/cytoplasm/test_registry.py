"""L4 unit tests: plugin registry."""

from __future__ import annotations

from typing import ClassVar

import pytest

from dbse.contracts import AffineType, Constraint, DomainModel, Invariant, PipelineContext
from dbse.cytoplasm import CytoplasmError
from dbse.cytoplasm.plugin import DomainPlugin
from dbse.cytoplasm.registry import PluginRegistry


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


def test_registry_resolves_plugin_by_domain_hint() -> None:
    reg = PluginRegistry()
    reg.register(_EchoPlugin())
    got = reg.get("echo")
    assert got is not None
    assert got.domain == "echo"


def test_registry_unregister_removes_plugin() -> None:
    reg = PluginRegistry()
    reg.register(_EchoPlugin())
    reg.unregister("echo")
    assert reg.get("echo") is None


def test_registry_apply_merges_plugin_outputs() -> None:
    reg = PluginRegistry()
    reg.register(_EchoPlugin())
    ctx = PipelineContext(query="q", config={"domain_hint": "echo", "beta": 0.5})
    result = reg.apply(ctx, domains=["echo"])
    assert result.domain_model == "echo_model"
    assert result.domain_indicators == {"beta": 0.5}
    assert len(result.constraints) == 1
