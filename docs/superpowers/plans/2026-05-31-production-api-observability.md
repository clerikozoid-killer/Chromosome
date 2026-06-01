# Production API + Observability (Stage 12) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven.

**Goal:** FastAPI `POST /api/v5/solve` и `/api/v5/clarify` по спеке §5, Mermaid trace, OpenAPI.

**Prerequisite:** Этапы 3–11.

---

## Task 1: Schemas

**Files:** `dbse/api/schemas.py`, `tests/api/test_schemas.py`

```python
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class SolveContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain_hint: str | None = None
    precision: str = "standard"

class SolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    context: SolveContext | None = None
    required_proof_level: str = "P2"
    output_formats: list[str] = Field(default_factory=lambda: ["json"])

class ClarifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
```

- [ ] TDD parse spec example → commit

---

## Task 2: Mapper

**Files:** `dbse/api/mapper.py`, `tests/api/test_mapper.py`

```python
from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
from dbse.contracts.context import HaltReason, PipelineContext

def _ts() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")

def context_to_solve_response(ctx: PipelineContext, *, request_id: str) -> dict[str, Any]:
    proof = ctx.proof
    return {
        "request_id": request_id,
        "timestamp": _ts(),
        "model_lattice": ctx.model_lattice,
        "solution": ctx.solution,
        "proof": None if proof is None else {
            "level": proof.level.name if hasattr(proof.level, "name") else str(proof.level),
            "tinfo": proof.tinfo,
            "confidence": proof.confidence,
            "solver_path": proof.solver_path,
            "violations": [
                {"invariant": v.invariant, "time": v.time, "value": v.value}
                for v in proof.violations
            ],
        },
        "expression": ctx.expression,
        "visualizations": ctx.config.get("_visualizations"),
        "halted": ctx.halted,
        "halt_reason": ctx.halt_reason.value,
    }

def context_to_clarify_response(ctx: PipelineContext) -> dict[str, Any]:
    entry = next((e for e in ctx.trace if e.note == "ambiguity_halt"), None)
    candidates = entry.payload.get("candidates", []) if entry else []
    return {
        "status": "clarification_needed",
        "ambiguity_temperature": (ctx.model_lattice or {}).get("ambiguity_temperature", 1.0),
        "candidates": candidates,
    }
```

- [ ] **Commit:** `feat(api): context mappers`

---

## Task 3: Mermaid

**Files:** `dbse/api/visualizations.py`, `tests/api/test_visualizations.py`

```python
def proof_trace_mermaid(ctx: PipelineContext) -> str:
    lines = ["graph TD"]
    for i, e in enumerate(ctx.trace):
        nid = f"L{i}"
        label = e.layer.replace(".", "_")
        lines.append(f'  {nid}["{e.layer}<br/>{e.note}"]')
        if i > 0:
            lines.append(f"  L{i-1} --> {nid}")
    if ctx.ast and ctx.ast.canonical_hash:
        lines.append(f'  HASH["ast_hash={ctx.ast.canonical_hash}"]')
        if ctx.trace:
            lines.append(f"  L{len(ctx.trace)-1} --> HASH")
    return "\n".join(lines)
```

- [ ] **Commit:** `feat(api): mermaid proof trace`

---

## Task 4: FastAPI app

**Files:** `dbse/api/app.py`, `pyproject.toml`, `tests/api/test_solve_endpoint.py`

Add deps: `fastapi`, dev: `uvicorn`, `httpx`.

```python
import uuid
from fastapi import FastAPI, HTTPException
from dbse.api.mapper import context_to_clarify_response, context_to_solve_response
from dbse.api.schemas import ClarifyRequest, SolveRequest
from dbse.api.visualizations import proof_trace_mermaid
from dbse.contracts.context import HaltReason
from dbse.pipeline import Pipeline

app = FastAPI(title="DBSE v5.0 Chromosome", version="5.0.0")

@app.post("/api/v5/solve")
def solve(body: SolveRequest) -> dict:
    config = body.context.model_dump() if body.context else {}
    config["required_proof_level"] = body.required_proof_level
    ctx = Pipeline().run(body.query, config=config)
    viz = {"mermaid": proof_trace_mermaid(ctx)}
    if ctx.ast and ctx.ast.canonical_hash:
        viz["ast_hash"] = ctx.ast.canonical_hash
    config["_visualizations"] = viz  # attach for mapper
    ctx.config = config
    rid = f"req_{uuid.uuid4().hex[:12]}"
    return context_to_solve_response(ctx, request_id=rid)

@app.post("/api/v5/clarify")
def clarify(body: ClarifyRequest) -> dict:
    ctx = Pipeline().run(body.query)
    if ctx.halt_reason is not HaltReason.AMBIGUITY_HALT:
        raise HTTPException(status_code=400, detail="Query is not ambiguous")
    return context_to_clarify_response(ctx)
```

```toml
[project.scripts]
dbse-api = "dbse.api.app:main"

# app.py bottom:
def main() -> None:
    import uvicorn
    uvicorn.run("dbse.api.app:app", host="0.0.0.0", port=8000, reload=False)
```

- [ ] httpx ASGI test apple query → 200.

- [ ] **Commit:** `feat(api): solve and clarify endpoints`

---

## Task 5: Contract QA

**Files:** `tests/api/test_contract.py`

- [ ] Validate response keys against expected set from spec §5.

- [ ] **Commit:** `test(api): contract shape validation`

---

## Task 6: Docs

- [ ] README: `dbse-api` / uvicorn dev command.

- [ ] **Commit:** `docs: mark Stage 12 complete`

---

## Execution handoff

Subagent-Driven, 7 tasks.
