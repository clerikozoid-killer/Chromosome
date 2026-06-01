# L7 EXPRESSION GENES — Constrained Styling + Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven.

**Goal:** Стилизация L6 skeleton в eli5/academic/business через Pydantic-схему + валидатор; детерминированный fallback без LLM в тестах.

**Prerequisite:** Этап 9.

---

## Task 1: Schema + errors

**Files:** `dbse/expression/schema.py`, `dbse/expression/errors.py`, `tests/expression/test_schema.py`

```python
# schema.py
from pydantic import BaseModel, ConfigDict, Field

class ExpressionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eli5: str
    academic: str
    business: str
    metaphors_used: list[str] = Field(default_factory=list)
```

- [ ] TDD → commit `feat(l7): ExpressionOutput schema`

---

## Task 2: Validator

**Files:** `dbse/expression/validator.py`, `dbse/expression/whitelist.py`, `tests/expression/test_validator.py`

```python
# validator.py
from __future__ import annotations
import re
from dbse.expression.errors import ExpressionError
from dbse.expression.schema import ExpressionOutput

_NUM = re.compile(r"\d+\.?\d*")

def validate_expression(
    skeleton: str,
    output: ExpressionOutput,
    *,
    forbidden: set[str],
    whitelist: set[str],
) -> None:
    nums = set(_NUM.findall(skeleton))
    for field in (output.eli5, output.academic, output.business):
        for bad in forbidden:
            if bad in field.casefold():
                raise ExpressionError(f"forbidden metaphor {bad!r} in styled text")
        for num in nums:
            if num not in field:
                raise ExpressionError(f"missing numeric token {num!r} from skeleton")
    for m in output.metaphors_used:
        if m not in whitelist:
            raise ExpressionError(f"metaphor {m!r} not in whitelist")
```

```python
# whitelist.py
DEFAULT_METAPHOR_WHITELIST: frozenset[str] = frozenset({"примерно", "около"})
```

- [ ] Tests: reject «хочет»; accept clean fallback.

- [ ] **Commit:** `feat(l7): expression validator`

---

## Task 3: Fallback stylist

**Files:** `dbse/expression/fallback.py`, `tests/expression/test_fallback.py`

```python
def style_fallback(
    skeleton: str,
    *,
    value: float | None = None,
    unit: str | None = None,
) -> ExpressionOutput:
    eli5 = f"Проще говоря: {skeleton}"
    academic = f"Согласно расчёту: {skeleton}"
    if value is not None and unit:
        business = f"Итог: {value:.3f} {unit} (уровень достоверности по proof)."
    else:
        business = f"Результат: {skeleton}"
    return ExpressionOutput(eli5=eli5, academic=academic, business=business, metaphors_used=[])
```

- [ ] **Commit:** `feat(l7): fallback stylist`

---

## Task 4: Layer + adversarial

**Files:** `dbse/layers/expression.py`, `tests/expression/test_layer.py`, `tests/expression/test_adversarial.py`

```python
class Expression:
    name: ClassVar[str] = "L7.EXPRESSION"
    def process(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.narrative:
            ctx.record(self.name, note="skipped:no-narrative")
            return ctx
        sk = str(ctx.narrative.get("skeleton", ""))
        val = ctx.solution.get("value") if ctx.solution else None
        unit = ctx.solution.get("unit") if ctx.solution else None
        out = style_fallback(sk, value=float(val) if val is not None else None, unit=str(unit or ""))
        forbidden = set(ctx.narrative.get("forbidden_metaphors", []))
        validate_expression(sk, out, forbidden=forbidden, whitelist=set(DEFAULT_METAPHOR_WHITELIST))
        ctx.expression = out.model_dump()
        ctx.record(self.name, note="styled")
        return ctx
```

- [ ] **Commit:** `feat(l7): wire Expression layer`

---

## Task 5: Docs

- [ ] README Stage 10 + spec-notes.

- [ ] **Commit:** `docs: mark Stage 10 (L7 Expression) complete`

---

## Execution handoff

Subagent-Driven, 6 tasks.
