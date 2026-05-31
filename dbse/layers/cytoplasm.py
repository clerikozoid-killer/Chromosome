"""L4 CYTOPLASM — epigenetics + domain plugins."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import PipelineContext
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin
from dbse.cytoplasm.plugins.fluid_mechanics import FluidMechanicsPlugin
from dbse.cytoplasm.registry import PluginRegistry


def default_registry() -> PluginRegistry:
    """Built-in plugins shipped with the core (connect/disconnect at runtime)."""
    reg = PluginRegistry()
    reg.register(ClassicalMechanicsPlugin())
    reg.register(FluidMechanicsPlugin())
    return reg


class Cytoplasm:
    """L4 layer: apply domain plugins → constraints, invariants, model selection."""

    name: ClassVar[str] = "L4.CYTOPLASM"

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self._registry = registry if registry is not None else default_registry()

    def process(self, ctx: PipelineContext) -> PipelineContext:
        hint = str(ctx.config.get("domain_hint", "")).strip()
        if not hint:
            ctx.record(self.name, note="skipped:no-domain-hint")
            return ctx
        plugin = self._registry.get(hint)
        if plugin is None:
            ctx.record(self.name, note="skipped:unknown-domain", domain_hint=hint)
            return ctx
        result = self._registry.apply(ctx, domains=[hint])
        if result.errors:
            ctx.record(self.name, note=f"plugin-error:{hint}", errors=result.errors)
            return ctx
        ctx.constraints = result.constraints
        ctx.invariants = result.invariants
        ctx.domain_model = result.domain_model
        ctx.domain_indicators = result.domain_indicators
        ctx.record(
            self.name,
            note="applied",
            domain=hint,
            domain_model=result.domain_model,
            indicators=result.domain_indicators,
        )
        return ctx
