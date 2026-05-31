"""Fluid mechanics domain plugin (skeleton / reference implementation)."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.cytoplasm.indicators import quantity_value_si, reynolds
from dbse.cytoplasm.plugin import DomainPlugin


class FluidMechanicsPlugin:
    """Reynolds/Mach/Froude → laminar/turbulent/compressible model selection."""

    domain: ClassVar[str] = "fluid_mechanics"
    dimensionless_numbers: ClassVar[list[str]] = ["Reynolds", "Mach", "Froude"]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        membrane = ctx.membrane or {}
        rho = quantity_value_si(membrane, "density") or 1.0
        velocity = quantity_value_si(membrane, "velocity") or 0.0
        length = quantity_value_si(membrane, "length")
        if length is None:
            length = quantity_value_si(membrane, "distance") or 1.0
        viscosity = float(ctx.config.get("viscosity_pa_s", 0.001))
        re = reynolds(rho, velocity, length, viscosity)
        a_sound = quantity_value_si(membrane, "speed_of_sound")
        mach = abs(velocity) / a_sound if velocity and a_sound is not None else 0.0
        # Froude skeleton: V / sqrt(g L) — g fixed for MVP
        g = 9.81
        froude = abs(velocity) / (g * length) ** 0.5 if length > 0 else 0.0
        return {"Reynolds": re, "Mach": mach, "Froude": froude}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        ma = indicators.get("Mach", 0.0)
        re = indicators.get("Reynolds", 0.0)
        if ma > 0.3:
            return DomainModel(id="compressible_navier_stokes", label="Compressible Navier-Stokes")
        if re > 2300:
            return DomainModel(id="turbulent_navier_stokes", label="Turbulent (k-ε)")
        if re > 1:
            return DomainModel(id="laminar_navier_stokes", label="Laminar Navier-Stokes")
        return DomainModel(id="stokes_flow", label="Stokes (creeping flow)")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [
            Constraint(expression="div(v) = 0", constraint_type="continuity"),
            Constraint(expression="v = 0", constraint_type="no_slip", boundary="walls"),
        ]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return []


def _type_check() -> None:
    _: DomainPlugin = FluidMechanicsPlugin()
