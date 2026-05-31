"""Domain plugin protocol (L4)."""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant


@runtime_checkable
class DomainPlugin(Protocol):
    """Hook surface for domain-specific epigenetic overlays."""

    domain: ClassVar[str]
    dimensionless_numbers: ClassVar[list[str]]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]: ...

    def select_model(self, indicators: dict[str, float]) -> DomainModel: ...

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]: ...

    def register_affine_types(self) -> list[AffineType]: ...

    def register_invariants(self) -> list[Invariant]: ...
