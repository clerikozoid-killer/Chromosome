"""Deterministic L7 stylist without LLM (tests and offline path)."""

from __future__ import annotations

from dbse.expression.schema import ExpressionOutput


def style_fallback(
    skeleton: str,
    *,
    value: float | None = None,
    unit: str | None = None,
) -> ExpressionOutput:
    eli5 = f"Проще говоря: {skeleton}"
    academic = f"Согласно расчёту: {skeleton}"
    if value is not None and unit:
        business = (
            f"Итог: {value:.3f} {unit} (уровень достоверности по proof). "
            f"{skeleton}"
        )
    else:
        business = f"Результат: {skeleton}"
    return ExpressionOutput(
        eli5=eli5,
        academic=academic,
        business=business,
        metaphors_used=[],
    )
