"""SI conversion helpers for dimensionless indicator computation."""

from __future__ import annotations

from typing import Any

# SI conversion factors relative to base SI units used in membrane quantities.
_LENGTH_TO_M: dict[str, float] = {"m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001}
_VELOCITY_TO_M_S: dict[str, float] = {"m/s": 1.0, "km/h": 1.0 / 3.6, "km/s": 1000.0}
_DENSITY_TO_KG_M3: dict[str, float] = {"kg/m^3": 1.0, "g/cm^3": 1000.0}


def quantity_value_si(membrane: dict[str, Any], property_name: str) -> float | None:
    """Return the first quantity with ``property_name`` converted to SI base."""
    for q in membrane.get("quantities") or []:
        if str(q.get("property")) != property_name:
            continue
        value = float(q["value"])
        unit = str(q.get("unit", ""))
        if property_name == "velocity":
            factor = _VELOCITY_TO_M_S.get(unit)
            if factor is None:
                return None
            return value * factor
        if property_name in {"distance", "length", "radius"}:
            factor = _LENGTH_TO_M.get(unit)
            if factor is None:
                return None
            return value * factor
        if property_name == "density":
            factor = _DENSITY_TO_KG_M3.get(unit)
            if factor is None:
                return None
            return value * factor
        # mass, force, time, etc. — assume already SI when unit matches L1 registry
        return value
    return None


def reynolds(rho: float, velocity: float, length: float, viscosity: float) -> float:
    """Re = ρ v L / μ."""
    if viscosity == 0.0:
        return float("inf")
    return rho * velocity * length / viscosity


def beta_velocity_ratio(velocity_m_s: float, c: float = 299_792_458.0) -> float:
    """β = v/c — non-relativistic indicator."""
    return abs(velocity_m_s) / c
