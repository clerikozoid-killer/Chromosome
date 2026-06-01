# Mentor CLI — Curriculum + Verdict Loop (Stage M) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven.

**Goal:** CLI `dbse-mentor` — прогон `cases/*.jsonl`, вердикты с категориями провалов, без записи в Core.

**Prerequisite:** Этапы 6–7 (минимум).

---

## Task 1: Case model + loader

**Files:** `dbse/mentor/cases.py`, `cases/physics/apple_weight.jsonl`, `tests/mentor/test_cases.py`

```jsonl
{"id":"apple_weight","query":"С какой силой Земля притягивает яблоко массой 100г?","domain_hint":"classical_mechanics","expected":{"value":0.980665,"unit":"N","tolerance":0.01},"proof_level":"P2","oracle":"analytic"}
{"id":"falling_ode","query":"dv/dt = g - 0.1 v","domain_hint":"classical_mechanics","expected":{"proof_level":"P2"},"oracle":"metamorphic"}
```

```python
# cases.py
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True, slots=True)
class Case:
    id: str
    query: str
    domain_hint: str
    expected: dict[str, Any]
    proof_level: str
    oracle: str

def load_cases(path: Path) -> list[Case]:
    out: list[Case] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        out.append(Case(
            id=str(raw["id"]),
            query=str(raw["query"]),
            domain_hint=str(raw.get("domain_hint", "")),
            expected=dict(raw.get("expected", {})),
            proof_level=str(raw.get("proof_level", "P2")),
            oracle=str(raw.get("oracle", "analytic")),
        ))
    return out
```

- [ ] **Commit:** `feat(mentor): case loader`

---

## Task 2: Verdict engine

**Files:** `dbse/mentor/verdict.py`, `tests/mentor/test_verdict.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from dbse.contracts.context import HaltReason, PipelineContext
from dbse.mentor.cases import Case

@dataclass(frozen=True, slots=True)
class Verdict:
    case_id: str
    passed: bool
    category: str
    detail: str

def judge(ctx: PipelineContext, case: Case) -> Verdict:
    if ctx.halt_reason is HaltReason.AMBIGUITY_HALT:
        return Verdict(case.id, False, "ambiguity", "unexpected ambiguity halt")
    if ctx.halt_reason is HaltReason.CLARIFICATION:
        return Verdict(case.id, False, "parse", ctx.halt_message)
    if ctx.solution is None:
        return Verdict(case.id, False, "solver", "no solution")
    exp = case.expected
    if "value" in exp:
        val = float(ctx.solution.get("value", 0))
        tol = float(exp.get("tolerance", 1e-6))
        if abs(val - float(exp["value"])) > tol:
            return Verdict(case.id, False, "solver", f"value {val} != {exp['value']}")
    if ctx.proof and case.proof_level:
        lvl = ctx.proof.level.name if hasattr(ctx.proof.level, "name") else str(ctx.proof.level)
        if lvl != case.proof_level and case.proof_level != "P2":
            return Verdict(case.id, False, "solver", f"proof {lvl}")
    return Verdict(case.id, True, "ok", "passed")
```

- [ ] **Commit:** `feat(mentor): verdict engine`

---

## Task 3: Batch run

**Files:** `dbse/mentor/run.py`, `tests/mentor/test_run.py`

```python
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from dbse.mentor.cases import load_cases
from dbse.mentor.verdict import Verdict, judge
from dbse.pipeline import Pipeline

def run_cases(cases_dir: Path, verdicts_dir: Path) -> list[Verdict]:
    pipeline = Pipeline()
    verdicts: list[Verdict] = []
    for path in sorted(cases_dir.rglob("*.jsonl")):
        for case in load_cases(path):
            ctx = pipeline.run(case.query, config={"domain_hint": case.domain_hint})
            verdicts.append(judge(ctx, case))
    out = verdicts_dir / f"{date.today().isoformat()}.jsonl"
    verdicts_dir.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for v in verdicts:
            f.write(json.dumps({"case_id": v.case_id, "passed": v.passed, "category": v.category, "detail": v.detail}) + "\n")
    return verdicts
```

- [ ] **Commit:** `feat(mentor): batch run`

---

## Task 4: CLI

**Files:** `dbse/mentor/cli.py`, `pyproject.toml`

```python
import argparse
from pathlib import Path
from dbse.mentor.run import run_cases

def main() -> None:
    p = argparse.ArgumentParser(prog="dbse-mentor")
    sub = p.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="Run case bank")
    run_p.add_argument("--cases", type=Path, default=Path("cases"))
    run_p.add_argument("--verdicts", type=Path, default=Path("verdicts"))
    args = p.parse_args()
    if args.cmd == "run":
        vs = run_cases(args.cases, args.verdicts)
        passed = sum(1 for v in vs if v.passed)
        print(f"{passed}/{len(vs)} passed")
```

```toml
[project.scripts]
dbse-mentor = "dbse.mentor.cli:main"
```

- [ ] **Commit:** `feat(mentor): CLI entry point`

---

## Task 5: Core guard test

**Files:** `tests/mentor/test_core_guard.py`

```python
def test_mentor_modules_do_not_expose_core_mutator() -> None:
    import dbse.mentor.run as run_mod
    import dbse.mentor.verdict as verdict_mod
    assert not hasattr(run_mod, "mutate_core")
    from dbse.knowledge.core import CORE
    assert CORE.__frozen__ is True
```

- [ ] **Commit:** `test(mentor): core write guard`

---

## Task 6: Docs + seed corpus

- [ ] Update `cases/README.md`, README Stage M, spec-notes.

- [ ] **Commit:** `docs: mark Stage M (Mentor) complete`

---

## Execution handoff

Subagent-Driven, 7 tasks. Запускать после Этапов 6–7.
