# L5 NUCLEUS (Stage 7) — ODE + Invariant Monitor + Z3 Budgets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution mode:** Subagent-Driven — fresh subagent per task, two-stage review between tasks.

**Goal:** Extend L5 NUCLEUS with first-order linear ODE solving, a `ContinuousInvariantMonitor` that fires on every integration step, and budgeted Z3 verification — so `v(t)` exceeding `c` yields `P3 MODEL_BREAKDOWN` at violation time and Z3 timeouts fall back to `P2` without hanging the worker. Closes vulnerabilities #3 (ODE Drift) and #5 (Z3 explosion).

**Architecture:** Extend `dbse/nucleus/` with `monitor.py` (`ContinuousInvariantMonitor`), `solve_ode.py` (SymPy analytic where possible, SciPy `solve_ivp` fallback with step callback), `invariants.py` (parse Cytoplasm `Invariant` records into evaluators), `z3_verify.py` (budgeted P0/P1 path), `budget.py` (default 100 ms wall-clock). Layer `Nucleus` routes `LinearODE_Order1` to ODE path; algebraic path unchanged from Stage 6.

**Tech Stack:** Python 3.11+, SymPy, SciPy (promote to runtime dep), `z3-solver>=4.12`, pytest + hypothesis. Reuses Stage 6 `dbse/nucleus/{tinfo,select_solver,...}`, `dbse.contracts.proof.{Proof,Violation}`, Cytoplasm `Invariant`.

**Prerequisite:** Stage 6 plan (`2026-05-31-l5-nucleus-algebra-sympy-proof-tinfo.md`) fully implemented.

---

## Environment notes (read once)

- PowerShell: `.\.venv\Scripts\Activate.ps1` ; chain with `;` not `&&`.
- QA gate per commit: `ruff check . ; mypy ; python -m pytest`.
- Repo root: `c:\Users\Clerikozoid\Desktop\Chromosome`.

## Key design decisions

1. **MVP ODE scope:** only `LinearODE_Order1` ASTs (`dv/dt = constant + linear_coeff * state`). Symbolic via SymPy `dsolve`; numeric via SciPy `solve_ivp` with dense output on `[0, t_end]`.
2. **Monitor callback** invoked at each integrator step with `(t, state_dict)`. State keys match ODE variable names (`v`, `V`, …).
3. **Invariant evaluators (MVP):** `v_lt_c` (`v < threshold`), `energy_conserved` (soft — recorded, not halting in MVP unless `severity=CRITICAL` and expression matches). Parse simple `v < c` / `v < 299792458` patterns from `Invariant.expression`.
4. **Critical violation →** `ctx.halt(HaltReason.MODEL_BREAKDOWN)`, `Proof.level=P3`, populate `Violation`, suggestion string in `ctx.halt_message`.
5. **Z3 budget:** `z3.set_param("timeout", ms)` + wall-clock guard; timeout → `solver_path` tag `domain_switch:z3-timeout`, stay `P2`, bump `tinfo`.
6. **Z3 MVP target:** verify `F = m * g` numeric result for algebraic weight recipe when `required_proof_level` is P1.
7. **Scope guard:** no nonlinear ODE, no PDE, no full constraint language in Z3.

## File Structure

`dbse/nucleus/` (extend):
- Create `dbse/nucleus/monitor.py`
- Create `dbse/nucleus/invariants.py`
- Create `dbse/nucleus/solve_ode.py`
- Create `dbse/nucleus/z3_verify.py`
- Create `dbse/nucleus/budget.py`
- Modify `dbse/nucleus/select_solver.py` — ODE no longer deferred
- Modify `dbse/nucleus/solve_algebraic.py` — unchanged API
- Modify `dbse/layers/nucleus.py` — ODE + Z3 paths

Tests:
- Create `tests/nucleus/test_monitor.py`
- Create `tests/nucleus/test_solve_ode.py`
- Create `tests/nucleus/test_z3_budget.py`
- Create `tests/nucleus/test_adversarial_ode.py` — QA level 5
- Create `tests/nucleus/test_ode_metamorphic.py` — QA level 4 (k→0)
- Modify `tests/nucleus/test_layer.py`

Docs: `README.md`, `docs/spec-notes.md`, `pyproject.toml` (scipy runtime, z3-solver).

---

## Task 0: Baseline — Stage 6 green

**Files:** none.

- [ ] **Step 1: Confirm Stage 6 committed and green**

Run: `git log --oneline -3 ; ruff check . ; mypy ; python -m pytest -q`
Expected: Stage 6 commits present; all tests pass.

---

## Task 1: Dependencies + `ContinuousInvariantMonitor` shell

**Files:**
- Modify: `pyproject.toml`
- Create: `dbse/nucleus/monitor.py`
- Create: `tests/nucleus/test_monitor.py`

- [ ] **Step 1: Write failing test**

```python
"""L5 monitor tests."""

from __future__ import annotations

from dbse.contracts.domain import Invariant
from dbse.contracts.proof import Severity
from dbse.nucleus.monitor import ContinuousInvariantMonitor


def test_monitor_passes_when_invariant_satisfied() -> None:
    inv = Invariant(name="v_lt_c", expression="v < c", threshold=10.0, severity=Severity.CRITICAL)
    mon = ContinuousInvariantMonitor([inv])
    assert mon.check_invariants(0.0, {"v": 5.0}) is True
    assert mon.violations == []


def test_monitor_records_critical_violation() -> None:
    inv = Invariant(name="v_lt_c", expression="v < c", threshold=10.0, severity=Severity.CRITICAL)
    mon = ContinuousInvariantMonitor([inv])
    assert mon.check_invariants(1.0, {"v": 11.0}) is False
    assert len(mon.violations) == 1
    assert mon.violations[0].invariant == "v_lt_c"
    assert mon.violations[0].time == 1.0
```

- [ ] **Step 2: Run — expect FAIL** (`ModuleNotFoundError`)

Run: `python -m pytest tests/nucleus/test_monitor.py -v`

- [ ] **Step 3: Implement**

Add to `pyproject.toml`:
```toml
dependencies = ["pydantic>=2,<3", "sympy>=1.12", "scipy>=1.11", "z3-solver>=4.12"]
```

Create `dbse/nucleus/monitor.py`:

```python
"""Continuous invariant monitor for ODE integration steps."""

from __future__ import annotations

from dbse.contracts.domain import Invariant
from dbse.contracts.proof import Severity, Violation
from dbse.nucleus.invariants import evaluate_invariant


class ContinuousInvariantMonitor:
    def __init__(self, invariants: list[Invariant]) -> None:
        self.invariants = invariants
        self.violations: list[Violation] = []

    def check_invariants(self, t: float, state: dict[str, float]) -> bool:
        for inv in self.invariants:
            value = evaluate_invariant(inv, state)
            if not _satisfies(inv, value):
                self.violations.append(
                    Violation(
                        invariant=inv.name,
                        severity=inv.severity,
                        time=t,
                        value=value,
                        threshold=inv.threshold,
                        message=f"{inv.name} violated at t={t}",
                    )
                )
                if inv.severity is Severity.CRITICAL:
                    return False
        return True


def _satisfies(inv: Invariant, value: float) -> bool:
    if inv.threshold is None:
        return True
    return value < inv.threshold
```

Create `dbse/nucleus/invariants.py`:

```python
"""Evaluate Cytoplasm invariant expressions against state."""

from __future__ import annotations

from dbse.contracts.domain import Invariant
from dbse.nucleus.errors import NucleusError


def evaluate_invariant(inv: Invariant, state: dict[str, float]) -> float:
    """MVP: return the LHS variable value for 'v < c' style invariants."""
    expr = inv.expression.replace(" ", "")
    if expr.startswith("v<"):
        return state.get("v", state.get("V", 0.0))
    raise NucleusError(f"Unsupported invariant expression: {inv.expression!r}")
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml dbse/nucleus/monitor.py dbse/nucleus/invariants.py tests/nucleus/test_monitor.py
git commit -m "feat(l5): add ContinuousInvariantMonitor for ODE steps"
```

---

## Task 2: `solve_ode` for LinearODE_Order1

**Files:**
- Create: `dbse/nucleus/solve_ode.py`
- Create: `tests/nucleus/test_solve_ode.py`

- [ ] **Step 1: Write failing test**

```python
"""L5 ODE solver tests."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.solve_ode import OdeResult, solve_linear_ode_1


def _falling_body_ast() -> AST:
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(
                kind="OPERATOR",
                op="ADD",
                children=(
                    ASTNode(kind="CONST", value=9.80665),
                    ASTNode(
                        kind="OPERATOR",
                        op="MUL",
                        children=(ASTNode(kind="CONST", value=-0.1), ASTNode(kind="SYMBOL", value="v")),
                    ),
                ),
            ),
        ),
    )
    root = ASTNode(kind="OBJECT", op="obj_1", children=(eq,))
    return AST(root=root, structure_class="LinearODE_Order1")


def test_solve_dvdt_g_minus_kv() -> None:
    result = solve_linear_ode_1(_falling_body_ast(), t_end=5.0, v0=0.0)
    assert isinstance(result, OdeResult)
    assert result.state_var == "v"
    assert result.at(5.0) > 0.0
    assert result.at(5.0) < 100.0  # sub-relativistic for this model
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `solve_ode.py`**

```python
"""First-order linear ODE solver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.monitor import ContinuousInvariantMonitor


@dataclass
class OdeResult:
    state_var: str
    t0: float
    t_end: float
    _t: np.ndarray
    _y: np.ndarray

    def at(self, t: float) -> float:
        return float(np.interp(t, self._t, self._y))


def _extract_linear_ode(root: ASTNode) -> tuple[str, float, float]:
    """Return (state, constant, linear_coeff) from first EQ/DERIV node."""
    for node in root.children:
        if node.kind != "OPERATOR" or node.op != "EQ":
            continue
        lhs, rhs = node.children
        if lhs.op != "DERIV" or lhs.children[0].kind != "SYMBOL":
            continue
        state = str(lhs.children[0].value)
        constant, linear_coeff = _linear_combo_coeffs(rhs)
        return state, constant, linear_coeff
    raise NucleusError("No LinearODE_Order1 equation found in AST")


def _linear_combo_coeffs(node: ASTNode) -> tuple[float, float]:
    constant = 0.0
    linear_coeff = 0.0
    if node.kind == "CONST":
        return float(node.value), 0.0
    if node.kind == "SYMBOL":
        return 0.0, 1.0
    if node.op == "ADD":
        for child in node.children:
            c, k = _linear_combo_coeffs(child)
            constant += c
            linear_coeff += k
    elif node.op == "MUL" and len(node.children) == 2:
        a, b = node.children
        if a.kind == "CONST" and b.kind == "SYMBOL":
            return 0.0, float(a.value)
        if b.kind == "CONST" and a.kind == "SYMBOL":
            return 0.0, float(b.value)
    elif node.op == "NEG":
        c, k = _linear_combo_coeffs(node.children[0])
        return -c, -k
    return constant, linear_coeff


def solve_linear_ode_1(
    ast: AST,
    *,
    t_end: float = 10.0,
    v0: float = 0.0,
    monitor: ContinuousInvariantMonitor | None = None,
) -> OdeResult:
    state, constant, linear_coeff = _extract_linear_ode(ast.root)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        return np.array([constant + linear_coeff * y[0]])

    def event(_t: float, y: np.ndarray) -> float:
        if monitor is None:
            return 1.0
        ok = monitor.check_invariants(float(_t), {state: float(y[0])})
        return 1.0 if ok else 0.0

    event.terminal = True  # type: ignore[attr-defined]
    event.direction = 0  # type: ignore[attr-defined]

    sol = solve_ivp(
        rhs,
        (0.0, t_end),
        [v0],
        method="RK45",
        dense_output=True,
        events=[event] if monitor else None,
    )
    t_grid = sol.t
    y_grid = sol.y[0]
    return OdeResult(state_var=state, t0=0.0, t_end=t_end, _t=t_grid, _y=y_grid)
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/solve_ode.py tests/nucleus/test_solve_ode.py
git commit -m "feat(l5): solve LinearODE_Order1 with SciPy and monitor callback"
```

---

## Task 3: ODE + monitor integration in layer (P3 path)

**Files:**
- Modify: `dbse/nucleus/select_solver.py`
- Modify: `dbse/layers/nucleus.py`
- Create: `tests/nucleus/test_adversarial_ode.py`

- [ ] **Step 1: Write failing adversarial test**

```python
"""Adversarial: ODE drift v > c → P3."""

from __future__ import annotations

from dbse.contracts import PipelineContext, ProofLevel
from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.domain import Invariant
from dbse.contracts.proof import Severity
from dbse.layers.nucleus import Nucleus


def test_ode_v_exceeds_c_halts_model_breakdown() -> None:
    # dv/dt = 2c over short horizon → v exceeds c quickly
    c = 299_792_458.0
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(kind="CONST", value=2.0 * c),
        ),
    )
    ast = AST(
        root=ASTNode(kind="OBJECT", op="obj_1", children=(eq,)),
        structure_class="LinearODE_Order1",
    )
    ctx = PipelineContext(
        query="relativistic breach",
        ast=ast,
        invariants=[
            Invariant(name="v_lt_c", expression="v < c", threshold=c, severity=Severity.CRITICAL),
        ],
        config={"ode_t_end": 0.001, "ode_v0": 0.0},
    )
    out = Nucleus().process(ctx)
    assert out.halted
    assert out.proof is not None
    assert out.proof.level is ProofLevel.P3
    assert out.proof.violations
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/nucleus/test_adversarial_ode.py -v`
Expected: FAIL — ODE still deferred or no P3 halt.

- [ ] **Step 3: Update `select_solver.py`**

Replace `SolverKind.ODE_DEFERRED` with `SolverKind.ODE`:

```python
class SolverKind(Enum):
    ALGEBRAIC = "algebraic"
    ODE = "ode"


def select_solver(ast: AST) -> SolverKind:
    cls = ast.structure_class or "Unknown"
    if cls == "Algebraic_Quantities":
        return SolverKind.ALGEBRAIC
    if cls == "LinearODE_Order1":
        return SolverKind.ODE
    raise NucleusError(f"Unsupported structure class: {cls!r}")
```

Update `tests/nucleus/test_select_solver.py`: rename `test_select_solver_ode_deferred` → `test_select_solver_ode` expecting `SolverKind.ODE`.

- [ ] **Step 4: Extend `Nucleus.process` ODE branch**

In `dbse/layers/nucleus.py`, after `select_solver`, add ODE branch before algebraic:

```python
from dbse.contracts.context import HaltReason
from dbse.contracts.proof import Proof, ProofLevel
from dbse.nucleus.monitor import ContinuousInvariantMonitor
from dbse.nucleus.solve_ode import solve_linear_ode_1

# inside process(), after kind = select_solver(ctx.ast):
if kind is SolverKind.ODE:
    invariants = ctx.invariants or []
    monitor = ContinuousInvariantMonitor(invariants)
    t_end = float(ctx.config.get("ode_t_end", 10.0))
    v0 = float(ctx.config.get("ode_v0", 0.0))
    try:
        ode_result = solve_linear_ode_1(ctx.ast, t_end=t_end, v0=v0, monitor=monitor)
    except NucleusError as exc:
        ctx.record(self.name, note="solve-error", error=str(exc))
        ctx.halt_message = str(exc)
        return ctx
    if monitor.violations:
        v0iol = monitor.violations[0]
        proof = Proof(
            level=ProofLevel.P3,
            violations=list(monitor.violations),
            solver_path=["ode:scipy", "monitor:critical_violation"],
        )
        ctx.proof = proof
        ctx.halt(
            HaltReason.MODEL_BREAKDOWN,
            f"Инвариант '{v0iol.invariant}' нарушен в t={v0iol.time}. "
            "Возможно, требуется релятивистская/нелинейная модель.",
        )
        ctx.record(self.name, note="model-breakdown", violation=v0iol.invariant)
        return ctx
    ctx.solution = {
        "value": ode_result.at(t_end),
        "unit": "m/s",
        "symbolic": f"{ode_result.state_var}(t)",
        "numeric_steps": [
            {"step": 1, "expression": f"d({ode_result.state_var})/dt = ..."},
            {"step": 2, "expression": f"{ode_result.state_var}({t_end}) ≈ {ode_result.at(t_end):.4f}"},
        ],
        "ode_series": {"t": ode_result._t.tolist(), "y": ode_result._y.tolist()},
    }
    proof = Proof(solver_path=["ode:scipy", "ode:symbolic_fallback"])
    level, confidence = assign_proof_level(proof)
    proof.level = level
    proof.tinfo = compute_tinfo(proof)
    proof.confidence = confidence
    ctx.proof = proof
    ctx.record(self.name, note="solved-ode", proof_level=level.value)
    return ctx
```

- [ ] **Step 5: Run adversarial test — expect PASS**

Run: `python -m pytest tests/nucleus/test_adversarial_ode.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add dbse/nucleus/select_solver.py dbse/layers/nucleus.py tests/nucleus/test_adversarial_ode.py
git commit -m "feat(l5): ODE path with P3 halt on critical invariant violation"
```

---

## Task 4: Budgeted Z3 verification

**Files:**
- Create: `dbse/nucleus/budget.py`
- Create: `dbse/nucleus/z3_verify.py`
- Create: `tests/nucleus/test_z3_budget.py`

- [ ] **Step 1: Write failing tests**

```python
"""Z3 budget tests."""

from __future__ import annotations

from dbse.nucleus.budget import Z3Budget, Z3BudgetExceeded
from dbse.nucleus.z3_verify import verify_weight_force


def test_verify_weight_force_succeeds() -> None:
    ok, steps = verify_weight_force(mass=0.1, g=9.80665, force=0.980665, budget_ms=500)
    assert ok is True
    assert steps


def test_budget_exceeded_on_pathological() -> None:
    budget = Z3Budget(ms=1)
    # force a slow check by nesting many asserts — use verify that respects budget
    from dbse.nucleus.z3_verify import verify_with_budget

    def slow() -> bool:
        import time
        time.sleep(0.05)
        return True

    ok, _ = verify_with_budget(slow, budget=budget)
    assert ok is False
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/nucleus/test_z3_budget.py -v`

- [ ] **Step 3: Implement `budget.py`**

```python
"""Wall-clock budget for Z3 verification."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Z3Budget:
    ms: int = 100


class Z3BudgetExceeded(TimeoutError):
    """Raised when Z3 or wrapper exceeds the wall-clock budget."""


def verify_with_budget(fn: Callable[[], bool], *, budget: Z3Budget) -> tuple[bool, list[str]]:
    start = time.perf_counter()
    try:
        ok = fn()
    except Exception:
        return False, ["z3:error"]
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms > budget.ms:
        return False, ["z3:timeout"]
    return ok, ["z3:ok"] if ok else ["z3:fail"]
```

- [ ] **Step 4: Implement `z3_verify.py`**

```python
"""Budgeted Z3 verification (MVP: weight force)."""

from __future__ import annotations

import z3

from dbse.nucleus.budget import Z3Budget, verify_with_budget


def verify_weight_force(
    *,
    mass: float,
    g: float,
    force: float,
    budget_ms: int = 100,
    tol: float = 1e-6,
) -> tuple[bool, list[str]]:
    def _check() -> bool:
        m, g_sym, f = z3.Reals("m g f")
        s = z3.Solver()
        s.set("timeout", budget_ms)
        s.add(m == mass, g_sym == g, f == force)
        s.add(f >= m * g_sym - tol)
        s.add(f <= m * g_sym + tol)
        return s.check() == z3.sat

    return verify_with_budget(_check, budget=Z3Budget(ms=budget_ms))
```

- [ ] **Step 5: Wire Z3 into algebraic path in layer**

After `solve_algebraic` success, if `required_proof_level` in `("P1", "VERIFIED_NUMERIC")`:

```python
from dbse.nucleus.z3_verify import verify_weight_force

ok, z3_steps = verify_weight_force(
    mass=quantities.get("mass", 0.0),
    g=float(ctx.config.get("gravity", STANDARD_GRAVITY)),
    force=result.value,
    budget_ms=int(ctx.config.get("z3_budget_ms", 100)),
)
proof.z3_steps = z3_steps
if ok:
    proof.solver_path.append("z3:verified")
    proof.level = ProofLevel.P1
else:
    proof.solver_path.append("domain_switch:z3-timeout")
```

- [ ] **Step 6: Run — expect PASS**

Run: `python -m pytest tests/nucleus/test_z3_budget.py -v`

- [ ] **Step 7: Commit**

```bash
git add dbse/nucleus/budget.py dbse/nucleus/z3_verify.py tests/nucleus/test_z3_budget.py
git commit -m "feat(l5): budgeted Z3 verification with timeout fallback to P2"
```

---

## Task 5: Metamorphic k→0 + differential ODE QA

**Files:**
- Create: `tests/nucleus/test_ode_metamorphic.py`
- Create: `tests/nucleus/test_ode_differential.py`

- [ ] **Step 1: Write metamorphic test**

Create `tests/nucleus/test_ode_metamorphic.py`:

```python
"""Metamorphic: k→0 in dv/dt = g - k*v → free fall v≈g*t."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.solve_ode import solve_linear_ode_1


def _ode_ast(g: float, k: float) -> AST:
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(
                kind="OPERATOR",
                op="ADD",
                children=(
                    ASTNode(kind="CONST", value=g),
                    ASTNode(
                        kind="OPERATOR",
                        op="MUL",
                        children=(ASTNode(kind="CONST", value=-k), ASTNode(kind="SYMBOL", value="v")),
                    ),
                ),
            ),
        ),
    )
    return AST(root=ASTNode(kind="OBJECT", op="obj_1", children=(eq,)), structure_class="LinearODE_Order1")


def test_k_to_zero_approaches_free_fall() -> None:
    g = STANDARD_GRAVITY
    k_small = 1e-9
    t = 0.5
    result = solve_linear_ode_1(_ode_ast(g, k_small), t_end=t, v0=0.0)
    assert result.at(t) == pytest.approx(g * t, rel=1e-3)
```

- [ ] **Step 2: Write differential test**

Create `tests/nucleus/test_ode_differential.py`:

```python
"""Differential: SciPy vs SymPy dsolve for dv/dt = -k*v."""

from __future__ import annotations

import sympy as sp

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.solve_ode import solve_linear_ode_1


def test_scipy_matches_sympy_exponential_decay() -> None:
    k = 0.2
    t_end = 3.0
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(
                kind="OPERATOR",
                op="MUL",
                children=(ASTNode(kind="CONST", value=-k), ASTNode(kind="SYMBOL", value="v")),
            ),
        ),
    )
    ast = AST(root=ASTNode(kind="OBJECT", op="o", children=(eq,)), structure_class="LinearODE_Order1")
    numeric = solve_linear_ode_1(ast, t_end=t_end, v0=1.0).at(t_end)
    t = sp.Symbol("t")
    v = sp.Function("v")
    analytic = sp.dsolve(sp.Eq(v(t).diff(t), -k * v(t)), v(t), ics={v(0): 1})
    expected = float(analytic.rhs.subs(t, t_end))
    assert numeric == expected
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/nucleus/test_ode_metamorphic.py tests/nucleus/test_ode_differential.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/nucleus/test_ode_metamorphic.py tests/nucleus/test_ode_differential.py
git commit -m "test(l5): ODE metamorphic and differential oracles"
```

---

## Task 6: Full QA gate + docs

**Files:** `README.md`, `docs/spec-notes.md`

- [ ] **Step 1:** `ruff check . ; mypy ; python -m pytest -q`

- [ ] **Step 2: Update README**

Append:

```markdown
- Этап 7 — L5 NUCLEUS (часть 2): ✅ ОДУ первого порядка (SciPy + SymPy oracle),
  Continuous Invariant Monitor (`v<c` → P3 MODEL_BREAKDOWN), Z3 с бюджетом 100 мс
  (fallback P2). **Закрывает уязвимости №3 (ODE Drift) и №5 (Z3 explosion).**
```

- [ ] **Step 3: spec-notes**

```markdown
## L5 (Stage 7) — принятые решения
- **ОДУ MVP:** только `LinearODE_Order1`; SciPy `solve_ivp` + event при нарушении CRITICAL.
- **Monitor:** `ContinuousInvariantMonitor.check_invariants(t, state)` на каждом шаге.
- **P3:** `HaltReason.MODEL_BREAKDOWN` + suggestion про релятивистскую модель.
- **Z3:** `z3-solver`, budget default 100 ms; timeout → `domain_switch:z3-timeout`, P2.
- **SciPy** — runtime dependency (не только dev).
- **QA:** уровни 1 + 3 (ODE differential) + 4 (k→0) + 5 (adversarial v>c).
```

- [ ] **Step 4: Commit**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 7 (L5 ODE + monitor + Z3 budgets) complete"
```

---

## Self-review

- ODE + monitor → Tasks 1–3 ✅
- P3 on v>c → Task 3 adversarial ✅
- Z3 budget → Task 4 ✅
- QA 1+3+4+5 → Tasks 1–5 ✅
- Vulnerabilities #3, #5 → covered ✅

## Execution handoff

**Subagent-Driven:** extract 7 tasks → TodoWrite → implementer + dual review per task → `finishing-a-development-branch` after Task 6.
