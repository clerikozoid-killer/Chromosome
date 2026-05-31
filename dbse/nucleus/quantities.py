"""Extract membrane quantities normalized to SI."""

from __future__ import annotations

from typing import Any

from dbse.cytoplasm.indicators import quantity_value_si

_MASS_TO_KG: dict[str, float] = {"kg": 1.0, "g": 0.001}


def membrane_quantities_si(membrane: dict[str, Any]) -> dict[str, float]:
    """Map property name → SI numeric value for known quantities."""
    out: dict[str, float] = {}
    for q in membrane.get("quantities") or []:
        prop = str(q.get("property", ""))
        if prop not in {"mass", "velocity", "force", "distance", "energy", "time"}:
            continue
        if prop == "mass":
            unit = str(q.get("unit", ""))
            factor = _MASS_TO_KG.get(unit)
            if factor is None:
                continue
            out[prop] = float(q["value"]) * factor
            continue
        val = quantity_value_si(membrane, prop)
        if val is not None:
            out[prop] = val
    return out
