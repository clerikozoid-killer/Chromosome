# L6 SEMANTIC NARRATIVE GRAPH — Deterministic Text Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven.

**Goal:** Детерминированный narrative graph из AST + skeleton-текст без LLM — запрещённые метафоры структурно невозможны.

**Prerequisite:** Этапы 4, 6/7.

---

## Task 1: Models + templates

**Files:** `dbse/narrative/models.py`, `dbse/narrative/templates.py`, `tests/narrative/test_templates.py`

- [ ] **Step 1: Failing test** (force template)

- [ ] **Step 3: Implement `TemplateSpec` + registry**

```python
# dbse/narrative/templates.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class TemplateSpec:
    template: str
    allowed_verbs: tuple[str, ...]
    forbidden_metaphors: tuple[str, ...]

_QUANTITY: dict[str, TemplateSpec] = {
    "force": TemplateSpec(
        "Гравитационная сила {value} {unit} действует на тело массой {mass}.",
        ("действует", "составляет"),
        ("хочет", "пытается", "любит", "стремится"),
    ),
    "mass": TemplateSpec(
        "Масса тела {value} {unit}.",
        ("равна", "составляет"),
        ("хочет", "тяжелеет от желания"),
    ),
}

def template_for_quantity(property_name: str) -> TemplateSpec:
    return _QUANTITY.get(property_name, TemplateSpec(
        "{property} = {value} {unit}",
        ("равно",),
        ("хочет",),
    ))
```

```python
# dbse/narrative/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class NarrativeNode:
    node_id: str
    template: str
    bindings: dict[str, Any]
    allowed_verbs: tuple[str, ...]
    forbidden_metaphors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "template": self.template,
            "bindings": self.bindings,
            "allowed_verbs": list(self.allowed_verbs),
            "forbidden_metaphors": list(self.forbidden_metaphors),
        }

@dataclass(frozen=True, slots=True)
class NarrativeGraph:
    nodes: tuple[NarrativeNode, ...]
```

- [ ] **Commit:** `feat(l6): narrative models and template registry`

---

## Task 2: build_graph

**Files:** `dbse/narrative/build.py`, `tests/narrative/test_build.py`

- [ ] **Step 1: Failing test** — apple AST + solution → ≥1 node

- [ ] **Step 3: Implement**

```python
from __future__ import annotations
from typing import Any
from dbse.contracts.ast import AST, ASTNode
from dbse.narrative.models import NarrativeGraph, NarrativeNode
from dbse.narrative.templates import template_for_quantity

def build_graph(ast: AST, solution: dict[str, Any] | None, membrane: dict[str, Any] | None) -> NarrativeGraph:
    nodes: list[NarrativeNode] = []
    mass_str = ""
    _walk(ast.root, nodes, solution, membrane, mass_holder := {"mass": ""})
    return NarrativeGraph(nodes=tuple(nodes))

def _walk(node: ASTNode, out: list[NarrativeNode], sol: dict[str, Any] | None, mem: dict[str, Any] | None, mass_holder: dict[str, str]) -> None:
    if node.kind == "QUANTITY":
        spec = template_for_quantity(str(node.op or "value"))
        unit = "N" if node.op == "force" and sol else ""
        val = sol.get("value", node.value) if sol and node.op == "force" else node.value
        if node.op == "mass":
            mass_holder["mass"] = f"{node.value} kg"
        bindings = {"property": node.op, "value": f"{val:.3f}" if isinstance(val, float) else val, "unit": unit or "?", "mass": mass_holder["mass"]}
        out.append(NarrativeNode(
            node_id=f"q_{node.op}_{len(out)}",
            template=spec.template,
            bindings=bindings,
            allowed_verbs=spec.allowed_verbs,
            forbidden_metaphors=spec.forbidden_metaphors,
        ))
    for child in node.children:
        _walk(child, out, sol, mem, mass_holder)
```

- [ ] **Commit:** `feat(l6): build narrative graph from AST`

---

## Task 3: render + layer

**Files:** `dbse/narrative/render.py`, `dbse/layers/narrative.py`, `tests/narrative/test_render.py`, `tests/narrative/test_layer.py`

- [ ] **Implement `to_text(graph)`** — `template.format(**bindings)` per node, join with space.

- [ ] **Layer:**

```python
class NarrativeGraph:
    name: ClassVar[str] = "L6.NARRATIVE"
    def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.ast is None or ctx.solution is None:
            ctx.record(self.name, note="skipped:no-ast-or-solution")
            return ctx
        graph = build_graph(ctx.ast, ctx.solution, ctx.membrane)
        skeleton = to_text(graph)
        ctx.narrative = {
            "skeleton": skeleton,
            "nodes": [n.to_dict() for n in graph.nodes],
            "forbidden_metaphors": sorted({m for n in graph.nodes for m in n.forbidden_metaphors}),
        }
        ctx.record(self.name, note="built", chars=len(skeleton))
        return ctx
```

- [ ] **Commit:** `feat(l6): wire Narrative layer`

---

## Task 4: Property determinism + docs

**Files:** `tests/narrative/test_properties.py`, `README.md`, `docs/spec-notes.md`

- [ ] Hypothesis: `to_text(build_graph(...))` idempotent.

- [ ] **Commit:** `docs: mark Stage 9 (L6 Narrative) complete`

---

## Execution handoff

Subagent-Driven, 5 tasks.
