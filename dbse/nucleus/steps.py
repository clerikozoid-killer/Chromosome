"""Build numeric_steps trace for API §5."""

from __future__ import annotations

from typing import Any


def build_weight_steps(*, mass_kg: float, g: float, result: float) -> list[dict[str, Any]]:
    return [
        {"step": 1, "expression": "F = m * g"},
        {"step": 2, "expression": f"F = {mass_kg} * {g}"},
        {"step": 3, "expression": f"F ≈ {result:.3f} N"},
    ]
