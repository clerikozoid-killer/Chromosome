"""Pluggy-style plugin registry (stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, Invariant
from dbse.cytoplasm.errors import CytoplasmError
from dbse.cytoplasm.plugin import DomainPlugin


@dataclass
class CytoplasmApplyResult:
    """Merged output from one or more domain plugins."""

    domain_model: str | None = None
    domain_indicators: dict[str, float] = field(default_factory=dict)
    constraints: list[Constraint] = field(default_factory=list)
    invariants: list[Invariant] = field(default_factory=list)
    affine_types: list[AffineType] = field(default_factory=list)
    applied_domains: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PluginRegistry:
    """Register domain plugins and apply them to a pipeline context."""

    def __init__(self) -> None:
        self._plugins: dict[str, DomainPlugin] = {}
        self._order: list[str] = []

    def register(self, plugin: DomainPlugin) -> None:
        domain = plugin.domain
        if domain not in self._order:
            self._order.append(domain)
        self._plugins[domain] = plugin

    def unregister(self, domain: str) -> None:
        self._plugins.pop(domain, None)
        if domain in self._order:
            self._order.remove(domain)

    def get(self, domain: str) -> DomainPlugin | None:
        return self._plugins.get(domain)

    def domains(self) -> list[str]:
        return list(self._order)

    def apply(
        self,
        ctx: PipelineContext,
        *,
        domains: list[str] | None = None,
    ) -> CytoplasmApplyResult:
        """Run plugins in registration order; merge outputs; isolate per-plugin errors."""
        target = domains if domains is not None else self._order
        result = CytoplasmApplyResult()
        for domain in target:
            plugin = self._plugins.get(domain)
            if plugin is None:
                continue
            try:
                indicators = plugin.compute_indicators(ctx)
                model = plugin.select_model(indicators)
                result.domain_indicators.update(indicators)
                result.domain_model = model.id
                result.constraints.extend(plugin.inject_constraints(ctx))
                result.invariants.extend(plugin.register_invariants())
                result.affine_types.extend(plugin.register_affine_types())
                result.applied_domains.append(domain)
            except CytoplasmError as exc:
                result.errors.append(f"{domain}:{exc}")
        return result
