# L2 CONTEXT MODEL LATTICE — Ambiguity Temperature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven — свежий субагент на задачу, двухэтапное ревью между задачами.

**Goal:** Построить L2 MODEL LATTICE — решётку конкурирующих интерпретаций контекста с `T_ambig` и остановкой с кандидатами уточнения при высокой неоднозначности — чтобы «сколько стоит яблоко?» давало `ambiguity_halt`, а не неверный физический ответ.

**Architecture:** Пакет `dbse/lattice/` — `models`, `catalog`, `entropy`, `classify`. Слой `ModelLattice` после L0.5, до L1.

**Tech Stack:** Python 3.11+, stdlib, pytest. Без LLM.

**Prerequisite:** Этап 3 (MEMBRANE + STS). Можно параллельно с 4–7.

---

## Environment notes

- PowerShell: `.\.venv\Scripts\Activate.ps1` ; команды через `;`.
- QA gate: `ruff check . ; mypy ; python -m pytest`.

## Key design decisions

1. Rule-based likelihoods по ключевым словам в запросе.
2. Posterior ∝ prior × likelihood, нормализация.
3. Пороги: `<0.3` continue; `0.3–0.6` top-2 в trace; `≥0.6` → `AMBIGUITY_HALT`.
4. `PHYSICS_COMPUTE` + `domain_hint` → доминирует `classical_gravitation`.

---

## Task 0: Baseline

- [ ] **Step 1:** `ruff check . ; mypy ; python -m pytest -q`

---

## Task 1: Models + entropy

**Files:** `dbse/lattice/models.py`, `dbse/lattice/entropy.py`, `dbse/lattice/__init__.py`, `tests/lattice/__init__.py`, `tests/lattice/test_entropy.py`

- [ ] **Step 1: Failing test** (см. ниже)

- [ ] **Step 2: Run** — `python -m pytest tests/lattice/test_entropy.py -v` → FAIL

- [ ] **Step 3: Implement** models + entropy (код из предыдущей версии плана)

- [ ] **Step 4: Run** → PASS

- [ ] **Step 5: Commit** — `feat(l2): ModelLattice and T_ambig entropy`

---

## Task 2: Catalog + classifier

**Files:** `dbse/lattice/catalog.py`, `dbse/lattice/classify.py`, `tests/lattice/test_classify.py`

- [ ] **Step 1: Failing test**

```python
from dbse.lattice.classify import build_lattice


def test_apple_price_query_high_ambiguity() -> None:
    lat = build_lattice("Сколько стоит яблоко?")
    assert lat.ambiguity_temperature >= 0.6
    assert "fruit_price" in {n.model_id for n in lat.nodes}


def test_physics_query_low_ambiguity() -> None:
    lat = build_lattice(
        "С какой силой Земля притягивает яблоко массой 100г?",
        sts_type="PHYSICS_COMPUTE",
        domain_hint="classical_mechanics",
    )
    assert lat.dominant_model.model_id == "classical_gravitation"
    assert lat.ambiguity_temperature < 0.3
```

- [ ] **Step 2: Run** → FAIL

- [ ] **Step 3: Implement `catalog.py`**

```python
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
    CandidateSpec("fruit_price", 1.0, "Цена за кг яблок в магазине?", ("кг", "магазин", "цена", "стоит")),
    CandidateSpec("stock_price", 1.0, "Котировки акций AAPL?", ("акци", "aapl", "бирж", "котиров")),
    CandidateSpec("company_valuation", 1.0, "Рыночная капитализация Apple Inc.?", ("компан", "капитализац")),
    CandidateSpec(
        "classical_gravitation",
        1.0,
        "",
        ("сил", "масс", "тяжест", "н", "kg", "г", "земл", "притяг"),
    ),
)
```

- [ ] **Step 4: Implement `classify.py`**

```python
"""Build a ModelLattice from query text."""

from __future__ import annotations

from dbse.lattice.catalog import CANDIDATES
from dbse.lattice.entropy import ambiguity_temperature
from dbse.lattice.models import ModelLattice, ModelNode


def _likelihood(query: str, keywords: tuple[str, ...]) -> float:
    q = query.casefold()
    score = 1.0
    for kw in keywords:
        if kw in q:
            score += 2.0
    return score


def build_lattice(
    query: str,
    *,
    sts_type: str | None = None,
    domain_hint: str = "",
) -> ModelLattice:
    nodes: list[ModelNode] = []
    for spec in CANDIDATES:
        like = _likelihood(query, spec.keywords)
        if sts_type == "PHYSICS_COMPUTE" and domain_hint:
            if spec.model_id != "classical_gravitation":
                like *= 0.05
            else:
                like *= 5.0
        nodes.append(
            ModelNode(
                model_id=spec.model_id,
                prior=spec.prior,
                likelihood=like,
                posterior=0.0,
                clarification=spec.clarification,
            )
        )
    total = sum(n.prior * n.likelihood for n in nodes) or 1.0
    normed: list[ModelNode] = []
    for n in nodes:
        post = (n.prior * n.likelihood) / total
        normed.append(
            ModelNode(
                model_id=n.model_id,
                prior=n.prior,
                likelihood=n.likelihood,
                posterior=post,
                clarification=n.clarification,
            )
        )
    dominant = max(normed, key=lambda x: x.posterior)
    lat = ModelLattice(
        nodes=normed,
        total_entropy=0.0,
        dominant_model=dominant,
        ambiguity_temperature=0.0,
    )
    t = ambiguity_temperature(lat)
    return ModelLattice(
        nodes=normed,
        total_entropy=t,
        dominant_model=dominant,
        ambiguity_temperature=t,
    )
```

- [ ] **Step 5: Run** → PASS

- [ ] **Step 6: Commit** — `feat(l2): rule-based model lattice classifier`

---

## Task 3: Wire layer

**Files:** `dbse/layers/model_lattice.py`, `tests/lattice/test_layer.py`

- [ ] **Step 1: Failing test**

```python
from dbse.contracts.context import HaltReason
from dbse.layers.model_lattice import ModelLattice
from dbse.pipeline import Pipeline


def test_ambiguous_query_halts_in_pipeline() -> None:
    ctx = Pipeline().run("Сколько стоит яблоко?")
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.AMBIGUITY_HALT
    assert ctx.model_lattice is not None


def test_physics_query_continues() -> None:
    ctx = Pipeline().run(
        "С какой силой Земля притягивает яблоко массой 100г?",
        config={"domain_hint": "classical_mechanics"},
    )
    assert not ctx.halted or ctx.halt_reason.value == "none"
```

- [ ] **Step 2–4: Implement layer** (полный код `ModelLattice.process` из ROADMAP)

- [ ] **Step 5: Commit** — `feat(l2): wire ModelLattice layer`

---

## Task 4: Adversarial QA

**Files:** `tests/lattice/test_adversarial.py`

- [ ] **Step 1: Corpus test**

```python
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
```

- [ ] **Step 2: Commit** — `test(l2): adversarial ambiguity corpus`

---

## Task 5: Docs

**Files:** `README.md`, `docs/spec-notes.md`

- [ ] Append Stage 8 status + spec-notes section L2.

- [ ] **Commit** — `docs: mark Stage 8 (L2 Model Lattice) complete`

---

## Execution handoff

Subagent-Driven, 6 tasks.
