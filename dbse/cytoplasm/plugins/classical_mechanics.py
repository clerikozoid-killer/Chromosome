"""Newtonian mechanics domain plugin."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.contracts.proof import Severity
from dbse.cytoplasm.indicators import beta_velocity_ratio, quantity_value_si
from dbse.cytoplasm.plugin import DomainPlugin

_C_LIGHT = 299_792_458.0
_DEFAULT_V_REF = 1.0  # m/s — threshold between linear/quadratic drag regimes


class ClassicalMechanicsPlugin:
    """Epigenetic overlay for non-relativistic Newtonian mechanics."""

    domain: ClassVar[str] = "classical_mechanics"
    dimensionless_numbers: ClassVar[list[str]] = ["beta", "drag_regime"]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        membrane = ctx.membrane or {}
        velocity = quantity_value_si(membrane, "velocity")
        beta = beta_velocity_ratio(velocity) if velocity is not None else 0.0
        drag_regime = (abs(velocity) / _DEFAULT_V_REF) if velocity is not None else 0.0
        return {"beta": beta, "drag_regime": drag_regime}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        drag = indicators.get("drag_regime", 0.0)
        if drag >= 1.0:
            return DomainModel(id="quadratic_friction", label="Quadratic drag (F ∝ v|v|)")
        return DomainModel(id="linear_friction", label="Linear drag (F = -k v)")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [
            Constraint(expression="F = m * a", constraint_type="newton_2"),
        ]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return [
            Invariant(
                name="v_lt_c",
                expression="v < c",
                threshold=_C_LIGHT,
                severity=Severity.CRITICAL,
            ),
            Invariant(
                name="energy_conserved",
                expression="dE/dt = 0",
                severity=Severity.SOFT,
                tolerance=1e-6,
            ),
        ]


def _type_check() -> None:
    _: DomainPlugin = ClassicalMechanicsPlugin()
