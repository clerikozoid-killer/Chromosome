# L5 NUCLEUS (Stage 6) — Algebraic SymPy + Proof Levels + Tinfo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode for this session:** Subagent-Driven — dispatch a fresh subagent per task with two-stage review (spec compliance, then code quality) between tasks.

**Goal:** Build L5 NUCLEUS (part 1) — deterministic algebraic solving via SymPy, structured `Proof`/`ProofLevel` assignment, `compute_tinfo` heuristics, and `numeric_steps` trace output — so the DoD query «сила тяжести на яблоко 100 г» returns symbolic + numeric results with calibrated trust metrics, and repeat solves populate the RIBOSOME cache.

**Architecture:** A new focused package `dbse/nucleus/` with seven modules — `errors` (`NucleusError`), `constants` (SI/CODATA-ish `g`, …), `select_solver` (route by `ast.structure_class`), `quantities` (membrane quantity map in SI), `recipes/weight.py` (MVP: target `force` + known `mass` → `F = m * g`), `solve_algebraic` (dispatcher + SymPy eval), `steps` (`numeric_steps` builder), `tinfo` (`compute_tinfo` + proof-level assignment). The pipeline layer `dbse/layers/nucleus.py` wires solve → proof → cache store on miss; skips when `ctx.solution` already set (RIBOSOME cache hit) or when AST is `LinearODE_Order1` (deferred to Stage 7).

**Tech Stack:** Python 3.11+, **SymPy** (first scientific runtime dep), `pydantic>=2`, `pytest` + `hypothesis`. SciPy stays **dev-only** for differential QA (level 3). Reuses `dbse.contracts.{AST, Proof, ProofLevel, PipelineContext}`, `dbse.ribosome.cache.SemanticCache`, `dbse.cytoplasm.indicators.quantity_value_si`.

---

## Environment notes (read once)

- Activate the venv first, or prefix commands: PowerShell `.\.venv\Scripts\Activate.ps1`.
- All test commands below use `python -m pytest ...`. Run from repo root `c:\Users\Clerikozoid\Desktop\Chromosome`.
- The shell is PowerShell: chain commands with `;`, **not** `&&`.
- Quality gate for every commit: `ruff check . ; mypy ; python -m pytest`.

## Key design decisions (made here, per the spec — note, don't re-litigate)

1. **SymPy is the first scientific runtime dependency.** Added to `[project] dependencies` alongside pydantic. Z3 arrives in Stage 7 — not here.
2. **MVP algebraic scope = recipe dispatch, not arbitrary CAS.** `Algebraic_Quantities` ASTs are quantity leaves only; the first recipe is **weight force**: `target.property == "force"` + known `mass` + `classical_mechanics` domain → `F = m * g`. SymPy handles symbolic form + numeric substitution. General constraint parsing is YAGNI until a second recipe is needed.
3. **ODE deferred to Stage 7.** `structure_class == "LinearODE_Order1"` → layer records `skipped:ode-deferred-stage7` and returns without error (no partial ODE solver).
4. **No Continuous Invariant Monitor yet.** Cytoplasm `invariants` are echoed in trace/proof metadata as `invariants_pending: true`; no runtime evaluation (Stage 7).
5. **Proof levels P0/P1 not reachable in Stage 6.** `required_proof_level` from config is honoured by trace note `z3-deferred-stage7` and a `domain_switch:` tag in `solver_path` (raises `tinfo`). Clean algebraic solves default to **P2** with low `tinfo` (< 0.2).
6. **`compute_tinfo` uses `solver_path` tags** (no new Proof fields): prefixes `heuristic:`, `approx:`, `linearize:`, `domain_switch:` map to spec weights 0.1/0.2/0.3/0.4; result clamped to `[0, 1]`. `confidence = max(0.0, 1.0 - tinfo)`.
7. **Cache write on solve miss.** After a successful solve, NUCLEUS stores `{solution, proof_level, tinfo}` into `SemanticCache` keyed by `ast.canonical_hash` (same secret/TTL/core_version pattern as RIBOSOME).
8. **Scope guard:** no ODE integration, no Z3, no invariant monitor, no narrative/L6 changes.

## L5 output conventions (fixed for all tasks)

| Field on `PipelineContext` | Type | Set by | Notes |
|---|---|---|---|
| `solution` | `dict[str, Any]` | NUCLEUS (or RIBOSOME cache hit) | keys: `value`, `unit`, `symbolic`, `numeric_steps` |
| `proof` | `Proof` | NUCLEUS | `level`, `tinfo`, `confidence`, `solver_path`, empty `z3_steps`/`violations` |

Trace note values: `"solved"`, `"skipped:cache-hit"`, `"skipped:no-ast"`, `"skipped:ode-deferred-stage7"`, `"skipped:already-solved"`, `"solve-error"`.

## File Structure

`dbse/nucleus/`:
- Create `dbse/nucleus/__init__.py` — public exports.
- Create `dbse/nucleus/errors.py` — `NucleusError`.
- Create `dbse/nucleus/constants.py` — `STANDARD_GRAVITY`, etc.
- Create `dbse/nucleus/quantities.py` — membrane quantity helpers.
- Create `dbse/nucleus/select_solver.py` — route by `structure_class`.
- Create `dbse/nucleus/recipes/__init__.py` — package marker.
- Create `dbse/nucleus/recipes/weight.py` — `solve_weight_force(...)`.
- Create `dbse/nucleus/solve_algebraic.py` — dispatcher + `AlgebraicResult`.
- Create `dbse/nucleus/steps.py` — `build_numeric_steps(...)`.
- Create `dbse/nucleus/tinfo.py` — `compute_tinfo`, `assign_proof_level`.

Layer wiring:
- Modify `dbse/layers/nucleus.py` — real `Nucleus` layer.
- Modify `pyproject.toml` — add `sympy>=1.12`, dev `scipy>=1.11`.

Tests:
- Create `tests/nucleus/__init__.py`
- Create `tests/nucleus/test_tinfo.py`
- Create `tests/nucleus/test_weight_recipe.py`
- Create `tests/nucleus/test_solve_algebraic.py`
- Create `tests/nucleus/test_differential.py` — QA level 3
- Create `tests/nucleus/test_metamorphic.py` — QA level 4
- Create `tests/nucleus/test_layer.py` — layer wiring + apple DoD

Docs:
- Modify `README.md`, `docs/spec-notes.md`, `dbse/contracts/proof.py` (update module docstring)

---

## Task 0: Baseline is green

**Files:** none (verification only).

- [ ] **Step 1: Confirm Stage 5 is committed and the suite is green**

Run: `git log --oneline -3 ; ruff check . ; mypy ; python -m pytest -q`
Expected: recent commits include Stage 5 work; `All checks passed!`; `Success: no issues found`; all tests pass.

> No commit in this task — smoke check before starting Stage 6.

---

## Task 1: Add SymPy dependency + `NucleusError`

**Files:**
- Modify: `pyproject.toml`
- Create: `dbse/nucleus/errors.py`
- Create: `dbse/nucleus/__init__.py`
- Create: `tests/nucleus/__init__.py`
- Create: `tests/nucleus/test_errors.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_errors.py`:

```python
"""L5 unit tests: NucleusError."""

from __future__ import annotations

import pytest

from dbse.nucleus import NucleusError


def test_nucleus_error_is_a_value_error() -> None:
    assert issubclass(NucleusError, ValueError)
    with pytest.raises(NucleusError):
        raise NucleusError("boom")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.nucleus'`.

- [ ] **Step 3: Add SymPy to dependencies and implement error type**

In `pyproject.toml`, change:

```toml
dependencies = ["pydantic>=2,<3", "sympy>=1.12"]
```

Create `dbse/nucleus/errors.py`:

```python
"""L5 error type."""

from __future__ import annotations


class NucleusError(ValueError):
    """Raised when NUCLEUS cannot solve or verify a problem (L5).

    Examples: unsupported structure class, missing target quantity, or
    SymPy evaluation failure.
    """
```

Create `dbse/nucleus/__init__.py`:

```python
"""L5 NUCLEUS — SymPy algebraic solver + proof assembly (Stage 6)."""

from dbse.nucleus.errors import NucleusError

__all__ = ["NucleusError"]
```

Create empty package markers: `tests/nucleus/__init__.py`.

- [ ] **Step 4: Install deps and run test**

Run: `pip install -e ".[dev]" ; python -m pytest tests/nucleus/test_errors.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml dbse/nucleus/ tests/nucleus/
git commit -m "feat(l5): add nucleus package shell and sympy dependency"
```

---

## Task 2: Physical constants

**Files:**
- Create: `dbse/nucleus/constants.py`
- Create: `tests/nucleus/test_constants.py`
- Modify: `dbse/nucleus/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_constants.py`:

```python
"""L5 unit tests: physical constants."""

from __future__ import annotations

from dbse.nucleus.constants import STANDARD_GRAVITY


def test_standard_gravity_is_positive_si() -> None:
    assert STANDARD_GRAVITY > 9.8
    assert STANDARD_GRAVITY < 9.82
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_constants.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.nucleus.constants'`.

- [ ] **Step 3: Implement constants**

Create `dbse/nucleus/constants.py`:

```python
"""CODATA-ish constants for deterministic numeric evaluation."""

from __future__ import annotations

# Standard acceleration due to gravity (m/s^2) — NIST conventional value.
STANDARD_GRAVITY: float = 9.80665
```

Update `dbse/nucleus/__init__.py`:

```python
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError

__all__ = ["NucleusError", "STANDARD_GRAVITY"]
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/nucleus/test_constants.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/constants.py dbse/nucleus/__init__.py tests/nucleus/test_constants.py
git commit -m "feat(l5): add STANDARD_GRAVITY constant"
```

---

## Task 3: `compute_tinfo` + proof level assignment

**Files:**
- Create: `dbse/nucleus/tinfo.py`
- Create: `tests/nucleus/test_tinfo.py`
- Modify: `dbse/nucleus/__init__.py`
- Modify: `dbse/contracts/proof.py` (docstring only)

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_tinfo.py`:

```python
"""L5 unit tests: Tinfo heuristics and proof level assignment."""

from __future__ import annotations

from dbse.contracts.proof import Proof, ProofLevel
from dbse.nucleus.tinfo import assign_proof_level, compute_tinfo


def test_compute_tinfo_zero_for_clean_path() -> None:
    proof = Proof(solver_path=["sympy:symbolic", "sympy:numeric"])
    assert compute_tinfo(proof) == 0.0


def test_compute_tinfo_weights_solver_path_tags() -> None:
    proof = Proof(
        solver_path=[
            "heuristic:assume_g",
            "approx:rounding",
            "linearize:small_angle",
            "domain_switch:z3-deferred",
        ]
    )
    # 0.1 + 0.2 + 0.3 + 0.4 = 1.0
    assert compute_tinfo(proof) == 1.0


def test_compute_tinfo_clamped_at_one() -> None:
    proof = Proof(solver_path=["heuristic:a", "heuristic:b", "approx:a", "approx:b"])
    assert compute_tinfo(proof) == 1.0


def test_assign_proof_level_p2_when_tinfo_low() -> None:
    proof = Proof(solver_path=["sympy:numeric"])
    level, confidence = assign_proof_level(proof)
    assert level is ProofLevel.P2
    assert confidence == 1.0


def test_assign_proof_level_p4_when_tinfo_high() -> None:
    proof = Proof(solver_path=["heuristic:guess"] * 6)
    level, _confidence = assign_proof_level(proof)
    assert level is ProofLevel.P4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_tinfo.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement tinfo module**

Create `dbse/nucleus/tinfo.py`:

```python
"""Tinfo heuristics and proof-level assignment (spec §3)."""

from __future__ import annotations

from dbse.contracts.proof import Proof, ProofLevel

_TAG_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("heuristic:", 0.1),
    ("approx:", 0.2),
    ("linearize:", 0.3),
    ("domain_switch:", 0.4),
)


def compute_tinfo(proof: Proof) -> float:
    """Return information temperature in [0, 1] from solver_path tags."""
    total = 0.0
    for step in proof.solver_path:
        for prefix, weight in _TAG_WEIGHTS:
            if step.startswith(prefix):
                total += weight
                break
    return min(total, 1.0)


def assign_proof_level(proof: Proof) -> tuple[ProofLevel, float]:
    """Derive ProofLevel and confidence from the current proof bundle."""
    if proof.violations:
        return ProofLevel.P3, 0.0
    tinfo = compute_tinfo(proof)
    if tinfo >= 0.5:
        return ProofLevel.P4, max(0.0, 1.0 - tinfo)
    # P0/P1 require Z3 (Stage 7). Stage 6 algebraic solves land at P2.
    return ProofLevel.P2, max(0.0, 1.0 - tinfo)
```

Update `dbse/nucleus/__init__.py` exports:

```python
from dbse.nucleus.tinfo import assign_proof_level, compute_tinfo
__all__ = [..., "assign_proof_level", "compute_tinfo"]
```

In `dbse/contracts/proof.py`, replace line 4 docstring:

```python
"""Cross-cutting contract: proof levels, violations, Tinfo.

These types travel through the whole pipeline and end up in the API response.
``compute_tinfo`` is implemented in ``dbse.nucleus.tinfo`` (Stage 6).
"""
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/nucleus/test_tinfo.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/tinfo.py dbse/nucleus/__init__.py dbse/contracts/proof.py tests/nucleus/test_tinfo.py
git commit -m "feat(l5): add compute_tinfo and proof level assignment"
```

---

## Task 4: Solver selection + quantity map

**Files:**
- Create: `dbse/nucleus/select_solver.py`
- Create: `dbse/nucleus/quantities.py`
- Create: `tests/nucleus/test_select_solver.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_select_solver.py`:

```python
"""L5 unit tests: solver routing and quantity extraction."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.select_solver import SolverKind, select_solver


def test_select_solver_algebraic_quantities() -> None:
    ast = AST(root=ASTNode(kind="OBJECT", op="obj_1", children=()))
    ast = AST(root=ast.root, structure_class="Algebraic_Quantities")
    assert select_solver(ast) is SolverKind.ALGEBRAIC


def test_select_solver_ode_deferred() -> None:
    ast = AST(root=ASTNode(kind="OBJECT", op="obj_1"), structure_class="LinearODE_Order1")
    assert select_solver(ast) is SolverKind.ODE_DEFERRED


def test_select_solver_unknown_raises() -> None:
    ast = AST(root=ASTNode(kind="OBJECT", op="obj_1"), structure_class="Unknown")
    with pytest.raises(NucleusError):
        select_solver(ast)


def test_membrane_quantities_si_converts_mass() -> None:
    membrane = {
        "quantities": [
            {"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"},
        ]
    }
    q = membrane_quantities_si(membrane)
    assert q["mass"] == pytest.approx(0.1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_select_solver.py -v`
Expected: FAIL — import errors.

- [ ] **Step 3: Implement selection + quantities**

Create `dbse/nucleus/select_solver.py`:

```python
"""Route AST structure classes to solver backends."""

from __future__ import annotations

from enum import Enum

from dbse.contracts.ast import AST
from dbse.nucleus.errors import NucleusError


class SolverKind(Enum):
    ALGEBRAIC = "algebraic"
    ODE_DEFERRED = "ode_deferred"


def select_solver(ast: AST) -> SolverKind:
    """Pick the solver kind for ``ast.structure_class``."""
    cls = ast.structure_class or "Unknown"
    if cls == "Algebraic_Quantities":
        return SolverKind.ALGEBRAIC
    if cls == "LinearODE_Order1":
        return SolverKind.ODE_DEFERRED
    raise NucleusError(f"Unsupported structure class: {cls!r}")
```

Create `dbse/nucleus/quantities.py`:

```python
"""Extract membrane quantities normalized to SI."""

from __future__ import annotations

from typing import Any

from dbse.cytoplasm.indicators import quantity_value_si


def membrane_quantities_si(membrane: dict[str, Any]) -> dict[str, float]:
    """Map property name → SI numeric value for known quantities."""
    out: dict[str, float] = {}
    for prop in ("mass", "velocity", "force", "distance", "energy", "time"):
        val = quantity_value_si(membrane, prop)
        if val is not None:
            out[prop] = val
    return out
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/nucleus/test_select_solver.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/select_solver.py dbse/nucleus/quantities.py tests/nucleus/test_select_solver.py
git commit -m "feat(l5): add solver selection and SI quantity map"
```

---

## Task 5: Weight-force recipe (`F = m * g`)

**Files:**
- Create: `dbse/nucleus/recipes/__init__.py`
- Create: `dbse/nucleus/recipes/weight.py`
- Create: `tests/nucleus/test_weight_recipe.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_weight_recipe.py`:

```python
"""L5 unit tests: weight force recipe F = m * g."""

from __future__ import annotations

import pytest

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.recipes.weight import solve_weight_force


def test_weight_force_apple_100g() -> None:
    result = solve_weight_force(mass_kg=0.1, g=STANDARD_GRAVITY)
    assert result.symbolic == "m * g"
    assert result.unit == "N"
    assert result.value == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-9)
    assert "sympy:symbolic" in result.solver_path
    assert "sympy:numeric" in result.solver_path
    assert len(result.numeric_steps) == 3


def test_weight_force_requires_positive_mass() -> None:
    with pytest.raises(NucleusError):
        solve_weight_force(mass_kg=0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_weight_recipe.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Implement recipe**

Create `dbse/nucleus/recipes/__init__.py` (empty).

Create `dbse/nucleus/recipes/weight.py`:

```python
"""Weight force: F = m * g near Earth's surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.steps import build_weight_steps


@dataclass(frozen=True, slots=True)
class RecipeResult:
    value: float
    unit: str
    symbolic: str
    numeric_steps: list[dict[str, Any]]
    solver_path: list[str]


def solve_weight_force(*, mass_kg: float, g: float = STANDARD_GRAVITY) -> RecipeResult:
    """Compute gravitational force on a body of known mass."""
    if mass_kg <= 0.0:
        raise NucleusError("mass must be positive for weight force")
    m_sym, g_sym = sp.symbols("m g")
    expr = m_sym * g_sym
    numeric = float(expr.subs({m_sym: mass_kg, g_sym: g}))
    steps = build_weight_steps(mass_kg=mass_kg, g=g, result=numeric)
    return RecipeResult(
        value=numeric,
        unit="N",
        symbolic="m * g",
        numeric_steps=steps,
        solver_path=["recipe:weight_force", "sympy:symbolic", "sympy:numeric"],
    )
```

Create `dbse/nucleus/steps.py`:

```python
"""Build numeric_steps trace for API §5."""

from __future__ import annotations

from typing import Any


def build_weight_steps(*, mass_kg: float, g: float, result: float) -> list[dict[str, Any]]:
    return [
        {"step": 1, "expression": "F = m * g"},
        {"step": 2, "expression": f"F = {mass_kg} * {g}"},
        {"step": 3, "expression": f"F ≈ {result:.3f} N"},
    ]
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/nucleus/test_weight_recipe.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/recipes/ dbse/nucleus/steps.py tests/nucleus/test_weight_recipe.py
git commit -m "feat(l5): add weight force recipe F = m * g with numeric steps"
```

---

## Task 6: `solve_algebraic` dispatcher

**Files:**
- Create: `dbse/nucleus/solve_algebraic.py`
- Create: `tests/nucleus/test_solve_algebraic.py`
- Modify: `dbse/nucleus/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_solve_algebraic.py`:

```python
"""L5 unit tests: algebraic solve dispatcher."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.context import PipelineContext
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.solve_algebraic import solve_algebraic


def _apple_ctx() -> PipelineContext:
    return PipelineContext(
        query="weight",
        config={"domain_hint": "classical_mechanics"},
        membrane={
            "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
            "quantities": [
                {"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"},
            ],
            "relations": [],
            "equations": [],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "force"},
        },
        ast=AST(
            root=ASTNode(kind="OBJECT", op="obj_1", children=()),
            structure_class="Algebraic_Quantities",
        ),
        domain_model="linear_friction",
    )


def test_solve_algebraic_apple_weight() -> None:
    result = solve_algebraic(_apple_ctx())
    assert result.unit == "N"
    assert result.value == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-9)
    assert result.symbolic == "m * g"


def test_solve_algebraic_missing_mass_raises() -> None:
    ctx = _apple_ctx()
    ctx.membrane = dict(ctx.membrane or {})
    ctx.membrane["quantities"] = []
    with pytest.raises(NucleusError):
        solve_algebraic(ctx)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_solve_algebraic.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Implement dispatcher**

Create `dbse/nucleus/solve_algebraic.py`:

```python
"""Algebraic solve entry point (Stage 6 MVP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dbse.contracts.context import PipelineContext
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.recipes.weight import RecipeResult, solve_weight_force
from dbse.nucleus.select_solver import SolverKind, select_solver


@dataclass(frozen=True, slots=True)
class AlgebraicResult:
    value: float
    unit: str
    symbolic: str
    numeric_steps: list[dict[str, Any]]
    solver_path: list[str]


def _from_recipe(recipe: RecipeResult) -> AlgebraicResult:
    return AlgebraicResult(
        value=recipe.value,
        unit=recipe.unit,
        symbolic=recipe.symbolic,
        numeric_steps=recipe.numeric_steps,
        solver_path=list(recipe.solver_path),
    )


def solve_algebraic(ctx: PipelineContext) -> AlgebraicResult:
    """Dispatch algebraic solve based on AST class and membrane target."""
    if ctx.ast is None:
        raise NucleusError("AST required for algebraic solve")
    if ctx.membrane is None:
        raise NucleusError("MEMBRANE required for algebraic solve")
    kind = select_solver(ctx.ast)
    if kind is SolverKind.ODE_DEFERRED:
        raise NucleusError("ODE solve deferred to Stage 7")
    target = ctx.membrane.get("target") or {}
    target_prop = str(target.get("property", ""))
    quantities = membrane_quantities_si(ctx.membrane)
    g = float(ctx.config.get("gravity", STANDARD_GRAVITY))
    if target_prop == "force" and "mass" in quantities:
        return _from_recipe(solve_weight_force(mass_kg=quantities["mass"], g=g))
    raise NucleusError(
        f"No algebraic recipe for target={target_prop!r} with quantities={list(quantities)}"
    )
```

Update `dbse/nucleus/__init__.py`:

```python
from dbse.nucleus.solve_algebraic import AlgebraicResult, solve_algebraic
__all__ = [..., "AlgebraicResult", "solve_algebraic"]
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/nucleus/test_solve_algebraic.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/solve_algebraic.py dbse/nucleus/__init__.py tests/nucleus/test_solve_algebraic.py
git commit -m "feat(l5): add algebraic solve dispatcher with weight recipe"
```

---

## Task 7: Wire the `Nucleus` pipeline layer

**Files:**
- Modify: `dbse/layers/nucleus.py`
- Create: `tests/nucleus/test_layer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_layer.py`:

```python
"""L5 layer integration tests."""

from __future__ import annotations

import pytest

from dbse.contracts import PipelineContext, ProofLevel
from dbse.layers.nucleus import Nucleus
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.ribosome.cache import SemanticCache


def _apple_membrane() -> dict:
    return {
        "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
        "quantities": [
            {"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"},
        ],
        "relations": [],
        "equations": [],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "force"},
    }


def test_nucleus_solves_apple_weight_with_proof() -> None:
    from dbse.contracts.ast import AST, ASTNode

    layer = Nucleus()
    ctx = PipelineContext(
        query="apple",
        config={"domain_hint": "classical_mechanics"},
        membrane=_apple_membrane(),
        ast=AST(
            root=ASTNode(kind="OBJECT", op="obj_1"),
            structure_class="Algebraic_Quantities",
            canonical_hash="abc123deadbeef01",
        ),
        domain_model="linear_friction",
    )
    out = layer.process(ctx)
    assert out.solution is not None
    assert out.solution["unit"] == "N"
    assert out.solution["value"] == pytest.approx(0.1 * STANDARD_GRAVITY, rel=1e-9)
    assert out.proof is not None
    assert out.proof.level is ProofLevel.P2
    assert out.proof.tinfo == 0.0
    assert out.trace[-1].layer == "L5.NUCLEUS"
    assert out.trace[-1].note == "solved"


def test_nucleus_skips_when_solution_prefilled() -> None:
    layer = Nucleus()
    ctx = PipelineContext(
        query="cached",
        solution={"value": 1.0, "unit": "N"},
        ast=None,
    )
    out = layer.process(ctx)
    assert out.trace[-1].note == "skipped:already-solved"


def test_nucleus_skips_ode_ast() -> None:
    from dbse.contracts.ast import AST, ASTNode

    layer = Nucleus()
    ctx = PipelineContext(
        query="ode",
        ast=AST(root=ASTNode(kind="OBJECT", op="obj_1"), structure_class="LinearODE_Order1"),
    )
    out = layer.process(ctx)
    assert out.solution is None
    assert out.trace[-1].note == "skipped:ode-deferred-stage7"


def test_nucleus_stores_cache_on_miss() -> None:
    from dbse.contracts.ast import AST, ASTNode

    cache = SemanticCache(secret="nuc-test", ttl_seconds=60, max_entries=8)
    layer = Nucleus(cache=cache, cache_secret="nuc-test", core_version="core-nuc")
    digest = "feedface01234567"
    ctx = PipelineContext(
        query="apple",
        membrane=_apple_membrane(),
        ast=AST(
            root=ASTNode(kind="OBJECT", op="obj_1"),
            structure_class="Algebraic_Quantities",
            canonical_hash=digest,
        ),
    )
    layer.process(ctx)
    hit = cache.get(digest, core_version="core-nuc")
    assert hit is not None
    assert hit.solution["unit"] == "N"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/nucleus/test_layer.py -v`
Expected: FAIL — layer still pass-through stub.

- [ ] **Step 3: Implement layer**

Replace `dbse/layers/nucleus.py`:

```python
"""L5 NUCLEUS — SymPy/Z3 + Continuous Invariant Monitor."""

from __future__ import annotations

from typing import Any, ClassVar

from dbse.contracts.context import PipelineContext
from dbse.contracts.proof import Proof
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.select_solver import SolverKind, select_solver
from dbse.nucleus.solve_algebraic import solve_algebraic
from dbse.nucleus.tinfo import assign_proof_level, compute_tinfo
from dbse.ribosome.cache import CacheEntry, SemanticCache


class Nucleus:
    """L5 layer: algebraic solve, proof assembly, cache store on miss."""

    name: ClassVar[str] = "L5.NUCLEUS"

    def __init__(
        self,
        cache: SemanticCache | None = None,
        *,
        cache_secret: str = "dev-cache-secret",
        core_version: str = "core-dev",
    ) -> None:
        self._cache = cache or SemanticCache(secret=cache_secret)
        self._cache_secret = cache_secret
        self._core_version = core_version

    def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.solution is not None:
            ctx.record(self.name, note="skipped:already-solved")
            return ctx
        if ctx.ast is None:
            ctx.record(self.name, note="skipped:no-ast")
            return ctx
        try:
            kind = select_solver(ctx.ast)
        except NucleusError as exc:
            ctx.record(self.name, note="solve-error", error=str(exc))
            ctx.halt_message = str(exc)
            return ctx
        if kind is SolverKind.ODE_DEFERRED:
            ctx.record(self.name, note="skipped:ode-deferred-stage7")
            return ctx
        solver_path: list[str] = []
        required = str(ctx.config.get("required_proof_level", "P2"))
        if required in ("P0", "P1", "AXIOMATIC_PROOF", "VERIFIED_NUMERIC"):
            solver_path.append("domain_switch:z3-deferred-stage7")
        try:
            result = solve_algebraic(ctx)
        except NucleusError as exc:
            ctx.record(self.name, note="solve-error", error=str(exc))
            ctx.halt_message = str(exc)
            return ctx
        solver_path.extend(result.solver_path)
        proof = Proof(solver_path=solver_path)
        level, confidence = assign_proof_level(proof)
        tinfo = compute_tinfo(proof)
        proof.level = level
        proof.tinfo = tinfo
        proof.confidence = confidence
        ctx.solution = {
            "value": result.value,
            "unit": result.unit,
            "symbolic": result.symbolic,
            "numeric_steps": result.numeric_steps,
        }
        ctx.proof = proof
        digest = ctx.ast.canonical_hash
        if digest is not None:
            self._cache.put(
                digest,
                CacheEntry(
                    ast=ctx.ast,
                    solution=ctx.solution,
                    proof_level=level.value,
                    tinfo=tinfo,
                ),
                core_version=self._core_version,
            )
        ctx.record(
            self.name,
            note="solved",
            proof_level=level.value,
            tinfo=tinfo,
            invariants_pending=bool(ctx.invariants),
        )
        return ctx
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/nucleus/test_layer.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/layers/nucleus.py tests/nucleus/test_layer.py
git commit -m "feat(l5): wire Nucleus layer with proof, tinfo, and cache store"
```

---

## Task 8: Differential QA (level 3)

**Files:**
- Modify: `pyproject.toml` (add scipy to dev deps)
- Create: `tests/nucleus/test_differential.py`

- [ ] **Step 1: Write the failing test**

Add to `pyproject.toml` under `[project.optional-dependencies] dev`:

```toml
"scipy>=1.11",
```

Create `tests/nucleus/test_differential.py`:

```python
"""L5 differential tests: SymPy vs independent numeric paths (QA level 3)."""

from __future__ import annotations

import sympy as sp
from scipy.constants import g as scipy_g

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.recipes.weight import solve_weight_force


def test_weight_force_sympy_matches_direct_float() -> None:
    mass = 0.1
    direct = mass * STANDARD_GRAVITY
    recipe = solve_weight_force(mass_kg=mass)
    assert recipe.value == direct


def test_weight_force_sympy_matches_scipy_constant() -> None:
    mass = 0.25
    m, g = sp.symbols("m g")
    expr = (m * g).subs({m: mass, g: scipy_g})
    recipe = solve_weight_force(mass_kg=mass, g=float(scipy_g))
    assert float(expr) == recipe.value
```

- [ ] **Step 2: Run test**

Run: `pip install -e ".[dev]" ; python -m pytest tests/nucleus/test_differential.py -v`
Expected: PASS (2 tests).

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml tests/nucleus/test_differential.py
git commit -m "test(l5): differential oracle for weight force recipe"
```

---

## Task 9: Metamorphic QA (level 4)

**Files:**
- Create: `tests/nucleus/test_metamorphic.py`

- [ ] **Step 1: Write the failing test**

Create `tests/nucleus/test_metamorphic.py`:

```python
"""L5 metamorphic tests: unit rescaling invariance (QA level 4)."""

from __future__ import annotations

from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.recipes.weight import solve_weight_force


def test_mass_in_g_vs_kg_gives_same_force() -> None:
    membrane_g = {
        "quantities": [{"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"}]
    }
    membrane_kg = {
        "quantities": [{"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "kg"}]
    }
    m_g = membrane_quantities_si(membrane_g)["mass"]
    m_kg = membrane_quantities_si(membrane_kg)["mass"]
    f_g = solve_weight_force(mass_kg=m_g).value
    f_kg = solve_weight_force(mass_kg=m_kg).value
    assert f_g == f_kg
    assert f_g == 0.1 * STANDARD_GRAVITY


def test_force_scales_linearly_with_mass() -> None:
    f1 = solve_weight_force(mass_kg=0.1).value
    f2 = solve_weight_force(mass_kg=0.2).value
    assert f2 == 2.0 * f1
```

- [ ] **Step 2: Run test**

Run: `python -m pytest tests/nucleus/test_metamorphic.py -v`
Expected: PASS (2 tests).

- [ ] **Step 3: Commit**

```bash
git add tests/nucleus/test_metamorphic.py
git commit -m "test(l5): metamorphic mass scaling invariance"
```

---

## Task 10: Full quality gate + pipeline skeleton

**Files:** none (verification only).

- [ ] **Step 1: Run the full QA gate**

Run: `ruff check . ; mypy ; python -m pytest -q`
Expected: `All checks passed!`; `Success: no issues found`; all tests pass including `tests/test_pipeline_skeleton.py`.

- [ ] **Step 2: Commit if any fixups were needed**

Only if fixups were required in Step 1.

---

## Task 11: Update status docs

**Files:**
- Modify: `README.md`
- Modify: `docs/spec-notes.md`

- [ ] **Step 1: Update README status**

Append to `README.md` "Статус":

```markdown
- Этап 6 — L5 NUCLEUS (часть 1): ✅ алгебраический SymPy-решатель (`F = m * g`),
  `Proof`/`ProofLevel`, `compute_tinfo`, `numeric_steps` (`dbse/nucleus/`).
  Слой `L5.NUCLEUS` подключён: cache miss → solve + cache store; ODE/Z3 —
  Этап 7. **QA:** уровни 1 + 3 (differential) + 4 (metamorphic).
```

- [ ] **Step 2: Record Stage 6 decisions in spec-notes**

Append to `docs/spec-notes.md`:

```markdown
## L5 (Stage 6) — принятые решения
- **SymPy — первая научная runtime-зависимость.** Z3, ODE, Continuous Invariant
  Monitor — Этап 7.
- **MVP algebraic = recipe dispatch.** Первый рецепт: `target.force` + `mass` →
  `F = m * g` (`dbse/nucleus/recipes/weight.py`). SymPy для символики и подстановки.
- **ODE (`LinearODE_Order1`) — pass-through** с trace `skipped:ode-deferred-stage7`.
- **P0/P1 недостижимы без Z3.** `required_proof_level` P0/P1 → tag
  `domain_switch:z3-deferred-stage7` в `solver_path`, повышение `tinfo`.
- **`compute_tinfo`** в `dbse/nucleus/tinfo.py` — веса по префиксам `solver_path`
  (spec §3). Чистый алгебраический solve → `P2`, `tinfo < 0.2`.
- **Cache write on miss** — NUCLEUS кладёт результат в `SemanticCache` по
  `canonical_hash` (согласовано с RIBOSOME Stage 4).
- **Инварианты Cytoplasm** пока только в trace (`invariants_pending`); runtime
  monitor — Этап 7.
- **QA-гейт:** уровни 1 (юнит + layer), 3 (`test_differential.py`), 4
  (`test_metamorphic.py`).
```

- [ ] **Step 3: Commit**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 6 (L5 NUCLEUS algebra + proof + tinfo) complete"
```

---

## Self-review (controller checklist)

**Spec coverage (ROADMAP Stage 6):**
- Выбор решателя по сложности AST → Task 4 `select_solver` ✅
- `solve_algebraic` через SymPy → Tasks 5–6 ✅
- `ProofLevel` P0–P4 как состояния → Task 3 `assign_proof_level` (P3/P4 paths; P0/P1 deferred) ✅
- `Proof` bundle → Task 7 layer ✅
- `compute_tinfo` эвристики → Task 3 ✅
- `numeric_steps` → Tasks 5, 7 ✅
- DoD apple 100g → Tasks 6–7 tests ✅
- QA 1+3+4 → Tasks 8–9 ✅

**Placeholder scan:** no TBD/TODO/similar-to tasks — each task has complete code.

**Type consistency:** `AlgebraicResult`/`RecipeResult` fields match layer `ctx.solution` keys; `Proof.level` uses existing `ProofLevel` enum; cache `proof_level=str(level.value)`.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-31-l5-nucleus-algebra-sympy-proof-tinfo.md`.

**Selected execution mode: Subagent-Driven.** To begin, invoke superpowers:subagent-driven-development:
1. Read this plan once; extract all 12 tasks into TodoWrite.
2. Dispatch a fresh implementer subagent per task with full task text + scene-setting context.
3. After each task: spec compliance review → code quality review → mark complete.
4. After Task 11: dispatch final code reviewer, then superpowers:finishing-a-development-branch.

**Note:** The deprecated `/write-plan` Cursor command should not be used going forward — use the superpowers **writing-plans** skill instead.
