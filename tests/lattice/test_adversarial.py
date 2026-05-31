"""Adversarial ambiguity corpus (QA level 5)."""

from __future__ import annotations

AMBIGUOUS = [
    "Сколько стоит яблоко?",
    "Apple price today?",
    "Цена яблок?",
]
UNAMBIGUOUS = [
    "С какой силой Земля притягивает яблоко массой 100г?",
    "dv/dt = g - k v",
]


def test_ambiguous_set_halts() -> None:
    from dbse.lattice.classify import build_lattice
    for q in AMBIGUOUS:
        assert build_lattice(q).ambiguity_temperature >= 0.6


def test_unambiguous_physics_low_temp() -> None:
    from dbse.lattice.classify import build_lattice
    for q in UNAMBIGUOUS:
        lat = build_lattice(q, sts_type="PHYSICS_COMPUTE", domain_hint="classical_mechanics")
        assert lat.ambiguity_temperature < 0.6
