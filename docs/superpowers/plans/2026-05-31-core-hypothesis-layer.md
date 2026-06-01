# Core vs Hypothesis Layer (Stage 11) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven.

**Goal:** Frozen Core + mutable Hypothesis; CRISPR-атаки → `CoreViolationError`; `core_version` для инвалидации кэша.

**Prerequisite:** Этап 4 (cache hook).

---

## Task 1: CoreTruthLayer

**Files:** `dbse/knowledge/core.py`, `dbse/knowledge/__init__.py`, `tests/knowledge/test_core.py`

```python
# core.py
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType

@dataclass(frozen=True, slots=True)
class Axiom:
    statement: str
    domain: str

_AXIOMS: dict[str, Axiom] = {
    "newton_2": Axiom("F = m*a", "classical_mechanics"),
    "conservation_energy": Axiom("dE/dt = 0", "closed_system"),
    "excluded_middle": Axiom("P or not P", "logic"),
}

class CoreTruthLayer:
    __frozen__ = True
    axioms: MappingProxyType[str, Axiom] = MappingProxyType(_AXIOMS)

    @classmethod
    def version_token(cls) -> str:
        payload = {k: {"statement": v.statement, "domain": v.domain} for k, v in cls.axioms.items()}
        raw = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()[:8]

CORE = CoreTruthLayer()
```

- [ ] TDD immutability tests → commit

---

## Task 2: HypothesisLayer

**Files:** `dbse/knowledge/hypothesis.py`, `tests/knowledge/test_hypothesis.py`

```python
@dataclass
class Hypothesis:
    id: str
    statement: str
    confidence: float
    evidence_count: int = 0
    conflicts_with: list[str] | None = None

class HypothesisLayer:
    def __init__(self) -> None:
        self.hypotheses: dict[str, Hypothesis] = {}

    def add_hypothesis(self, h: Hypothesis) -> bool:
        if h.confidence < 0.1:
            return False
        from dbse.knowledge.guard import assert_no_core_violation
        assert_no_core_violation(h.statement)
        self.hypotheses[h.id] = h
        return True
```

- [ ] **Commit:** `feat(knowledge): HypothesisLayer`

---

## Task 3: Guard + CRISPR adversarial

**Files:** `dbse/knowledge/errors.py`, `dbse/knowledge/guard.py`, `tests/knowledge/test_guard.py`, `tests/knowledge/test_adversarial.py`

```python
# errors.py
class CoreViolationError(RuntimeError):
    """Attempt to mutate or contradict Core axioms."""

# guard.py
import re
from dbse.knowledge.core import CORE
from dbse.knowledge.errors import CoreViolationError

_CRISPR = re.compile(r"F\s*=\s*m\s*\*\s*a\s*\^?\s*2", re.I)

def assert_no_core_violation(text: str) -> None:
    if _CRISPR.search(text.replace(" ", "")):
        raise CoreViolationError("Hypothesis contradicts newton_2 Core axiom")
    lowered = text.casefold()
    for ax in CORE.axioms.values():
        if "contradict" in lowered and ax.statement.replace(" ", "").casefold() in lowered:
            raise CoreViolationError(f"Explicit contradiction of {ax.statement}")
```

- [ ] **Commit:** `feat(knowledge): CoreViolationError guard`

---

## Task 4: Pipeline guard on constraints

**Files:** `dbse/layers/cytoplasm.py` or `dbse/pipeline.py`, `tests/knowledge/test_pipeline_guard.py`

- [ ] Before applying plugin constraints, `assert_no_core_violation(c.expression)` for each constraint.

- [ ] Malicious constraint `F = m*a^2` → `HaltReason.CORE_VIOLATION`.

- [ ] **Commit:** `feat(knowledge): pipeline Core guard on constraints`

---

## Task 5: Wire core_version to Ribosome/Nucleus defaults

- [ ] `Ribosome(core_version=CORE.version_token())` in factory or default_layers.

- [ ] Test: change axiom hash conceptually stable across runs.

- [ ] **Commit:** `feat(knowledge): core_version wired to cache`

---

## Task 6: Docs

- [ ] README Stage 11 + spec-notes.

- [ ] **Commit:** `docs: mark Stage 11 complete`

---

## Execution handoff

Subagent-Driven, 7 tasks.
