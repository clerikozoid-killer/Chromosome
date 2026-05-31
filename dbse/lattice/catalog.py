"""Seed model candidates and keyword boosts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    model_id: str
    prior: float
    clarification: str
    keywords: tuple[str, ...]


CANDIDATES: tuple[CandidateSpec, ...] = (
    CandidateSpec(
        "fruit_price",
        1.0,
        "Цена за кг яблок в магазине?",
        ("кг", "магазин", "цена", "стоит"),
    ),
    CandidateSpec(
        "stock_price",
        1.0,
        "Котировки акций AAPL?",
        ("акци", "aapl", "бирж", "котиров"),
    ),
    CandidateSpec(
        "company_valuation",
        1.0,
        "Рыночная капитализация Apple Inc.?",
        ("компан", "капитализац"),
    ),
    CandidateSpec(
        "classical_gravitation",
        1.0,
        "",
        ("сил", "масс", "тяжест", "н", "kg", "г", "земл", "притяг"),
    ),
)
