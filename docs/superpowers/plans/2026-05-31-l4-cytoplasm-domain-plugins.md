# L4 CYTOPLASM — Epigenetics + Domain Plugin API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build L4 CYTOPLASM — a plug-in-style domain layer that reads pipeline context (MEMBRANE + AST), computes dimensionless indicators, selects a domain model, and injects constraints/invariants for downstream NUCLEUS (Stage 7) — without putting domain logic in the core. Plugins connect/disconnect via a registry; `classical_mechanics` is the first full plugin; `fluid_mechanics` is a reference skeleton.

**Architecture:** A new focused package `dbse/cytoplasm/` with five modules — `errors` (`CytoplasmError`), `contracts` (re-export of frozen `Constraint`/`Invariant`/`DomainModel` from `dbse/contracts/domain.py`), `plugin` (`DomainPlugin` Protocol), `registry` (`PluginRegistry` — pluggy-*style* hook ordering, no third-party pluggy dep), and `plugins/` (`classical_mechanics.py` full, `fluid_mechanics.py` skeleton). The pipeline layer `dbse/layers/cytoplasm.py` wires registry → active plugins → `PipelineContext` L4 slots (`constraints`, `invariants`, `domain_model`, `domain_indicators`). Domain hint comes from `ctx.config["domain_hint"]` (API §5) — **not** from MEMBRANE (LLM must never emit `CONTEXT`).

**Tech Stack:** Python 3.11+, stdlib only at runtime, `pytest` + `hypothesis` for tests. Reuses `dbse.contracts.{AffineType, PipelineContext, AST}`, `dbse.dimensional.parse_unit`, `dbse.ribosome` AST conventions.

---

## Environment notes (read once)

- Activate the venv first, or prefix commands: PowerShell `.\.venv\Scripts\Activate.ps1`.
- All test commands below use `python -m pytest ...`. Run from repo root `c:\Users\Clerikozoid\Desktop\Chromosome`.
- The shell is PowerShell: chain commands with `;`, **not** `&&`.
- Quality gate for every commit: `ruff check . ; mypy ; python -m pytest`.

## Key design decisions (made here, per the spec — note, don't re-litigate)

1. **No `pluggy` dependency.** ROADMAP says "pluggy-стиль" — we implement a tiny stdlib `PluginRegistry` with explicit registration order and per-plugin error isolation. YAGNI until we need dynamic entry-points.
2. **Domain hint is config-only.** API request `context.domain_hint` maps to `ctx.config["domain_hint"]`. MEMBRANE schema stays unchanged (Stage 3 sandbox: LLM never emits `CONTEXT`).
3. **MVP indicator math is deterministic and unit-aware.** `compute_indicators` converts membrane quantities to SI before forming dimensionless numbers (Reynolds, Mach, β=v/c). Metamorphic QA: same physics → same model after unit rescaling.
4. **Invariants are data, not evaluators yet.** `Invariant` records name, expression, threshold, severity — enough for NUCLEUS (Stage 7) to consume. Cytoplasm does not run SymPy/Z3 (scope guard).
5. **Friction model selection (classical_mechanics):** `drag_regime_indicator = v / v_ref` where `v_ref` defaults to `1.0 m/s` (configurable). `< 1` → `linear_friction`; `≥ 1` → `quadratic_friction`. When velocity is absent, default `linear_friction`.
6. **Plugin isolation:** a plugin raising `CytoplasmError` is skipped; trace records `plugin-error:<domain>`. Registry continues with remaining plugins unless all active plugins fail.
7. **Scope guard:** no SymPy, no ODE solving, no Z3 — only indicator computation, model selection, constraint/invariant injection. NUCLEUS integration tests use placeholder reads of `ctx.invariants`.

## L4 output conventions (fixed for all tasks)

| Field on `PipelineContext` | Type | Set by | Consumed by |
|---|---|---|---|
| `constraints` | `list[Constraint]` | Cytoplasm | NUCLEUS (Stage 7) |
| `invariants` | `list[Invariant]` | Cytoplasm | NUCLEUS monitor (Stage 7) |
| `domain_model` | `str` | Cytoplasm | trace + NUCLEUS |
| `domain_indicators` | `dict[str, float]` | Cytoplasm | trace + model selection audit |

Trace note values: `"applied"`, `"skipped:no-ast"`, `"skipped:unknown-domain"`, `"plugin-error:<domain>"`.

## File Structure

`dbse/contracts/`:
- Create `dbse/contracts/domain.py` — `Constraint`, `Invariant`, `DomainModel`.

`dbse/cytoplasm/`:
- Create `dbse/cytoplasm/__init__.py` — public exports.
- Create `dbse/cytoplasm/errors.py` — `CytoplasmError`.
- Create `dbse/cytoplasm/plugin.py` — `DomainPlugin` Protocol.
- Create `dbse/cytoplasm/registry.py` — `PluginRegistry`.
- Create `dbse/cytoplasm/indicators.py` — SI conversion helpers for indicator math.
- Create `dbse/cytoplasm/plugins/__init__.py` — plugin package marker.
- Create `dbse/cytoplasm/plugins/classical_mechanics.py` — first full plugin.
- Create `dbse/cytoplasm/plugins/fluid_mechanics.py` — skeleton plugin.

Layer wiring:
- Modify `dbse/layers/cytoplasm.py` — real `Cytoplasm` layer.
- Modify `dbse/contracts/context.py` — L4 fields on `PipelineContext`.
- Modify `dbse/contracts/__init__.py` — export new types.

Tests:
- Create `tests/cytoplasm/__init__.py`
- Create `tests/cytoplasm/test_registry.py`
- Create `tests/cytoplasm/test_classical_mechanics.py`
- Create `tests/cytoplasm/test_fluid_mechanics.py`
- Create `tests/cytoplasm/test_metamorphic.py` — QA level 4
- Create `tests/cytoplasm/test_layer.py` — layer wiring + DoD

Docs:
- Modify `README.md`, `docs/spec-notes.md`

---

## Task 0: Baseline is green

**Files:** none (verification only).

- [ ] **Step 1: Confirm Stage 4 is committed and the suite is green**

Run: `git log --oneline -3 ; ruff check . ; mypy ; python -m pytest -q`
Expected: recent commits include Stage 4 work (`docs: mark Stage 4 ... complete`); `All checks passed!`; `Success: no issues found`; all tests pass.

> No commit in this task — smoke check before starting Stage 5.

---

## Task 1: `CytoplasmError` and package skeleton

**Files:**
- Create: `dbse/cytoplasm/errors.py`
- Create: `dbse/cytoplasm/__init__.py`
- Create: `tests/cytoplasm/__init__.py`
- Create: `tests/cytoplasm/test_registry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/cytoplasm/__init__.py` (empty file):

```python
```

Create `tests/cytoplasm/test_registry.py`:

```python
"""L4 unit tests: plugin registry."""

from __future__ import annotations

import pytest

from dbse.cytoplasm import CytoplasmError


def test_cytoplasm_error_is_a_value_error() -> None:
    assert issubclass(CytoplasmError, ValueError)
    with pytest.raises(CytoplasmError):
        raise CytoplasmError("boom")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.cytoplasm'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/cytoplasm/errors.py`:

```python
"""L4 error type."""

from __future__ import annotations


class CytoplasmError(ValueError):
    """Raised when a domain plugin cannot process the pipeline context."""
```

Create `dbse/cytoplasm/__init__.py`:

```python
"""L4 CYTOPLASM — epigenetics + domain plugins."""

from dbse.cytoplasm.errors import CytoplasmError

__all__ = ["CytoplasmError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_registry.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add dbse/cytoplasm/errors.py dbse/cytoplasm/__init__.py tests/cytoplasm/__init__.py tests/cytoplasm/test_registry.py
git commit -m "feat(l4): add cytoplasm package skeleton and CytoplasmError"
```

---

## Task 2: Domain contract types — `Constraint`, `Invariant`, `DomainModel`

**Files:**
- Create: `dbse/contracts/domain.py`
- Modify: `dbse/contracts/__init__.py`
- Create: `tests/cytoplasm/test_contracts.py`

- [ ] **Step 1: Write the failing test**

Create `tests/cytoplasm/test_contracts.py`:

```python
"""L4 contract tests: domain types."""

from __future__ import annotations

from dbse.contracts import Constraint, DomainModel, Invariant
from dbse.contracts.proof import Severity


def test_invariant_defaults_to_critical() -> None:
    inv = Invariant(name="v_lt_c", expression="v < c", threshold=299792458.0)
    assert inv.severity is Severity.CRITICAL
    assert inv.tolerance == 0.0


def test_constraint_carries_type_label() -> None:
    c = Constraint(expression="div(v) = 0", constraint_type="continuity")
    assert c.constraint_type == "continuity"


def test_domain_model_is_frozen() -> None:
    m = DomainModel(id="linear_friction", label="Linear drag")
    assert m.id == "linear_friction"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_contracts.py -v`
Expected: FAIL — `ImportError: cannot import name 'Constraint'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/contracts/domain.py`:

```python
"""L4 contract: domain constraints, invariants, and model descriptors."""

from __future__ import annotations

from dataclasses import dataclass, field

from dbse.contracts.proof import Severity


@dataclass(frozen=True, slots=True)
class Constraint:
    """A domain equation or boundary condition injected by a plugin."""

    expression: str
    constraint_type: str
    boundary: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Invariant:
    """A physical invariant for the Continuous Invariant Monitor (L5)."""

    name: str
    expression: str
    threshold: float | None = None
    severity: Severity = Severity.CRITICAL
    tolerance: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DomainModel:
    """A coarse model choice returned by ``select_model``."""

    id: str
    label: str
    metadata: dict[str, str] = field(default_factory=dict)
```

Update `dbse/contracts/__init__.py` — add imports and `__all__` entries:

```python
from dbse.contracts.domain import Constraint, DomainModel, Invariant
```

```python
    "Constraint",
    "DomainModel",
    "Invariant",
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_contracts.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/contracts/domain.py dbse/contracts/__init__.py tests/cytoplasm/test_contracts.py
git commit -m "feat(l4): add Constraint, Invariant, DomainModel contracts"
```

---

## Task 3: Extend `PipelineContext` with L4 slots

**Files:**
- Modify: `dbse/contracts/context.py`
- Modify: `tests/test_contracts.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_contracts.py`:

```python
from dbse.contracts import Constraint, Invariant


def test_pipeline_context_has_l4_cytoplasm_slots() -> None:
    ctx = PipelineContext(query="q")
    inv = Invariant(name="v_lt_c", expression="v < c")
    con = Constraint(expression="F = m*a", constraint_type="newton_2")
    ctx.invariants = [inv]
    ctx.constraints = [con]
    ctx.domain_model = "linear_friction"
    ctx.domain_indicators = {"beta": 0.001}
    assert ctx.invariants[0].name == "v_lt_c"
    assert ctx.constraints[0].constraint_type == "newton_2"
    assert ctx.domain_model == "linear_friction"
    assert ctx.domain_indicators["beta"] == 0.001
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_contracts.py::test_pipeline_context_has_l4_cytoplasm_slots -v`
Expected: FAIL — `AttributeError` / field missing.

- [ ] **Step 3: Write minimal implementation**

In `dbse/contracts/context.py`, add import:

```python
from dbse.contracts.domain import Constraint, Invariant
```

In `PipelineContext`, after `ast: AST | None = None`:

```python
    constraints: list[Constraint] | None = None       # L4
    invariants: list[Invariant] | None = None           # L4
    domain_model: str | None = None                     # L4
    domain_indicators: dict[str, float] | None = None   # L4
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_contracts.py -v`
Expected: all contract tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dbse/contracts/context.py tests/test_contracts.py
git commit -m "feat(l4): add cytoplasm output slots to PipelineContext"
```

---

## Task 4: `DomainPlugin` Protocol

**Files:**
- Create: `dbse/cytoplasm/plugin.py`
- Modify: `dbse/cytoplasm/__init__.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/cytoplasm/test_registry.py`:

```python
from typing import ClassVar

from dbse.contracts import AffineType, Constraint, DomainModel, Invariant, PipelineContext
from dbse.cytoplasm.plugin import DomainPlugin


class _EchoPlugin:
    domain: ClassVar[str] = "echo"
    dimensionless_numbers: ClassVar[list[str]] = ["beta"]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        return {"beta": float(ctx.config.get("beta", 0.0))}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        return DomainModel(id="echo_model", label="Echo")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [Constraint(expression="x = x", constraint_type="identity")]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return []


def test_domain_plugin_protocol_accepts_concrete_class() -> None:
    plugin: DomainPlugin = _EchoPlugin()
    assert plugin.domain == "echo"
    assert plugin.dimensionless_numbers == ["beta"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_registry.py::test_domain_plugin_protocol_accepts_concrete_class -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.cytoplasm.plugin'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/cytoplasm/plugin.py`:

```python
"""Domain plugin protocol (L4)."""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant


@runtime_checkable
class DomainPlugin(Protocol):
    """Hook surface for domain-specific epigenetic overlays."""

    domain: ClassVar[str]
    dimensionless_numbers: ClassVar[list[str]]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]: ...

    def select_model(self, indicators: dict[str, float]) -> DomainModel: ...

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]: ...

    def register_affine_types(self) -> list[AffineType]: ...

    def register_invariants(self) -> list[Invariant]: ...
```

Update `dbse/cytoplasm/__init__.py`:

```python
from dbse.cytoplasm.plugin import DomainPlugin

__all__ = ["CytoplasmError", "DomainPlugin"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_registry.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/cytoplasm/plugin.py dbse/cytoplasm/__init__.py tests/cytoplasm/test_registry.py
git commit -m "feat(l4): add DomainPlugin protocol"
```

---

## Task 5: SI indicator helpers + `PluginRegistry`

**Files:**
- Create: `dbse/cytoplasm/indicators.py`
- Create: `dbse/cytoplasm/registry.py`
- Modify: `dbse/cytoplasm/__init__.py`
- Modify: `tests/cytoplasm/test_registry.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/cytoplasm/test_registry.py`:

```python
from dbse.cytoplasm.registry import PluginRegistry


def test_registry_resolves_plugin_by_domain_hint() -> None:
    reg = PluginRegistry()
    reg.register(_EchoPlugin())
    got = reg.get("echo")
    assert got is not None
    assert got.domain == "echo"


def test_registry_unregister_removes_plugin() -> None:
    reg = PluginRegistry()
    reg.register(_EchoPlugin())
    reg.unregister("echo")
    assert reg.get("echo") is None


def test_registry_apply_merges_plugin_outputs() -> None:
    reg = PluginRegistry()
    reg.register(_EchoPlugin())
    ctx = PipelineContext(query="q", config={"domain_hint": "echo", "beta": 0.5})
    result = reg.apply(ctx, domains=["echo"])
    assert result.domain_model == "echo_model"
    assert result.domain_indicators == {"beta": 0.5}
    assert len(result.constraints) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_registry.py::test_registry_resolves_plugin_by_domain_hint -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/cytoplasm/indicators.py`:

```python
"""SI conversion helpers for dimensionless indicator computation."""

from __future__ import annotations

from typing import Any

# SI conversion factors relative to base SI units used in membrane quantities.
_LENGTH_TO_M: dict[str, float] = {"m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001}
_VELOCITY_TO_M_S: dict[str, float] = {"m/s": 1.0, "km/h": 1.0 / 3.6, "km/s": 1000.0}
_DENSITY_TO_KG_M3: dict[str, float] = {"kg/m^3": 1.0, "g/cm^3": 1000.0}


def quantity_value_si(membrane: dict[str, Any], property_name: str) -> float | None:
    """Return the first quantity with ``property_name`` converted to SI base."""
    for q in membrane.get("quantities") or []:
        if str(q.get("property")) != property_name:
            continue
        value = float(q["value"])
        unit = str(q.get("unit", ""))
        if property_name == "velocity":
            factor = _VELOCITY_TO_M_S.get(unit)
            if factor is None:
                return None
            return value * factor
        if property_name in {"distance", "length", "radius"}:
            factor = _LENGTH_TO_M.get(unit)
            if factor is None:
                return None
            return value * factor
        if property_name == "density":
            factor = _DENSITY_TO_KG_M3.get(unit)
            if factor is None:
                return None
            return value * factor
        # mass, force, time, etc. — assume already SI when unit matches L1 registry
        return value
    return None


def reynolds(rho: float, velocity: float, length: float, viscosity: float) -> float:
    """Re = ρ v L / μ."""
    if viscosity == 0.0:
        return float("inf")
    return rho * velocity * length / viscosity


def beta_velocity_ratio(velocity_m_s: float, c: float = 299_792_458.0) -> float:
    """β = v/c — non-relativistic indicator."""
    return abs(velocity_m_s) / c
```

Create `dbse/cytoplasm/registry.py`:

```python
"""Pluggy-style plugin registry (stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.cytoplasm.errors import CytoplasmError
from dbse.cytoplasm.plugin import DomainPlugin


@dataclass
class CytoplasmApplyResult:
    """Merged output from one or more domain plugins."""

    domain_model: str | None = None
    domain_indicators: dict[str, float] = field(default_factory=dict)
    constraints: list[Constraint] = field(default_factory=list)
    invariants: list[Invariant] = field(default_factory=list)
    affine_types: list[AffineType] = field(default_factory=list)
    applied_domains: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PluginRegistry:
    """Register domain plugins and apply them to a pipeline context."""

    def __init__(self) -> None:
        self._plugins: dict[str, DomainPlugin] = {}
        self._order: list[str] = []

    def register(self, plugin: DomainPlugin) -> None:
        domain = plugin.domain
        if domain not in self._order:
            self._order.append(domain)
        self._plugins[domain] = plugin

    def unregister(self, domain: str) -> None:
        self._plugins.pop(domain, None)
        if domain in self._order:
            self._order.remove(domain)

    def get(self, domain: str) -> DomainPlugin | None:
        return self._plugins.get(domain)

    def domains(self) -> list[str]:
        return list(self._order)

    def apply(
        self,
        ctx: PipelineContext,
        *,
        domains: list[str] | None = None,
    ) -> CytoplasmApplyResult:
        """Run plugins in registration order; merge outputs; isolate per-plugin errors."""
        target = domains if domains is not None else self._order
        result = CytoplasmApplyResult()
        for domain in target:
            plugin = self._plugins.get(domain)
            if plugin is None:
                continue
            try:
                indicators = plugin.compute_indicators(ctx)
                model = plugin.select_model(indicators)
                result.domain_indicators.update(indicators)
                result.domain_model = model.id
                result.constraints.extend(plugin.inject_constraints(ctx))
                result.invariants.extend(plugin.register_invariants())
                result.affine_types.extend(plugin.register_affine_types())
                result.applied_domains.append(domain)
            except CytoplasmError as exc:
                result.errors.append(f"{domain}:{exc}")
        return result
```

Update `dbse/cytoplasm/__init__.py` exports: `PluginRegistry`, `CytoplasmApplyResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_registry.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/cytoplasm/indicators.py dbse/cytoplasm/registry.py dbse/cytoplasm/__init__.py tests/cytoplasm/test_registry.py
git commit -m "feat(l4): add SI indicator helpers and PluginRegistry"
```

---

## Task 6: `classical_mechanics` plugin — invariants + constraints

**Files:**
- Create: `dbse/cytoplasm/plugins/__init__.py`
- Create: `dbse/cytoplasm/plugins/classical_mechanics.py`
- Create: `tests/cytoplasm/test_classical_mechanics.py`

- [ ] **Step 1: Write the failing test**

Create `tests/cytoplasm/test_classical_mechanics.py`:

```python
"""L4 unit tests: classical_mechanics domain plugin."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.contracts.proof import Severity
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin


def test_classical_mechanics_registers_non_relativistic_invariant() -> None:
    plugin = ClassicalMechanicsPlugin()
    names = {inv.name for inv in plugin.register_invariants()}
    assert "v_lt_c" in names
    inv = next(i for i in plugin.register_invariants() if i.name == "v_lt_c")
    assert inv.severity is Severity.CRITICAL
    assert inv.threshold == 299_792_458.0


def test_classical_mechanics_injects_newton_2_constraint() -> None:
    plugin = ClassicalMechanicsPlugin()
    ctx = PipelineContext(query="q", membrane={"quantities": []})
    types = {c.constraint_type for c in plugin.inject_constraints(ctx)}
    assert "newton_2" in types
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_classical_mechanics.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/cytoplasm/plugins/__init__.py`:

```python
"""Built-in domain plugins for L4 CYTOPLASM."""
```

Create `dbse/cytoplasm/plugins/classical_mechanics.py`:

```python
"""Newtonian mechanics domain plugin."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.contracts.proof import Severity
from dbse.cytoplasm.indicators import beta_velocity_ratio, quantity_value_si
from dbse.cytoplasm.plugin import DomainPlugin

_C_LIGHT = 299_792_458.0
_DEFAULT_V_REF = 1.0  # m/s — threshold between linear/quadratic drag regimes


class ClassicalMechanicsPlugin:
    """Epigenetic overlay for non-relativistic Newtonian mechanics."""

    domain: ClassVar[str] = "classical_mechanics"
    dimensionless_numbers: ClassVar[list[str]] = ["beta", "drag_regime"]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        membrane = ctx.membrane or {}
        velocity = quantity_value_si(membrane, "velocity")
        beta = beta_velocity_ratio(velocity) if velocity is not None else 0.0
        drag_regime = (abs(velocity) / _DEFAULT_V_REF) if velocity is not None else 0.0
        return {"beta": beta, "drag_regime": drag_regime}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        drag = indicators.get("drag_regime", 0.0)
        if drag >= 1.0:
            return DomainModel(id="quadratic_friction", label="Quadratic drag (F ∝ v|v|)")
        return DomainModel(id="linear_friction", label="Linear drag (F = -k v)")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [
            Constraint(expression="F = m * a", constraint_type="newton_2"),
        ]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return [
            Invariant(
                name="v_lt_c",
                expression="v < c",
                threshold=_C_LIGHT,
                severity=Severity.CRITICAL,
            ),
            Invariant(
                name="energy_conserved",
                expression="dE/dt = 0",
                severity=Severity.SOFT,
                tolerance=1e-6,
            ),
        ]


def _type_check() -> None:
    _: DomainPlugin = ClassicalMechanicsPlugin()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_classical_mechanics.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/cytoplasm/plugins/__init__.py dbse/cytoplasm/plugins/classical_mechanics.py tests/cytoplasm/test_classical_mechanics.py
git commit -m "feat(l4): classical_mechanics plugin invariants and constraints"
```

---

## Task 7: `classical_mechanics` — friction model selection

**Files:**
- Modify: `tests/cytoplasm/test_classical_mechanics.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/cytoplasm/test_classical_mechanics.py`:

```python
def test_low_velocity_selects_linear_friction_model() -> None:
    plugin = ClassicalMechanicsPlugin()
    ctx = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 0.5, "unit": "m/s"},
            ]
        },
    )
    indicators = plugin.compute_indicators(ctx)
    model = plugin.select_model(indicators)
    assert model.id == "linear_friction"


def test_high_velocity_selects_quadratic_friction_model() -> None:
    plugin = ClassicalMechanicsPlugin()
    ctx = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 50.0, "unit": "m/s"},
            ]
        },
    )
    indicators = plugin.compute_indicators(ctx)
    model = plugin.select_model(indicators)
    assert model.id == "quadratic_friction"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_classical_mechanics.py::test_high_velocity_selects_quadratic_friction_model -v`
Expected: FAIL — wrong model id (implementation from Task 6 should already pass if thresholds correct; if PASS, skip to Step 4).

- [ ] **Step 3: Adjust thresholds if needed**

No code change expected if Task 6 used `_DEFAULT_V_REF = 1.0` correctly. If test fails, verify `quantity_value_si` handles `"m/s"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_classical_mechanics.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit** (only if Step 3 changed code)

```bash
git add dbse/cytoplasm/plugins/classical_mechanics.py tests/cytoplasm/test_classical_mechanics.py
git commit -m "test(l4): classical_mechanics friction model selection"
```

> If Task 6 already satisfies these tests, mark Step 5 checkboxes done with no commit.

---

## Task 8: `fluid_mechanics` skeleton plugin

**Files:**
- Create: `dbse/cytoplasm/plugins/fluid_mechanics.py`
- Create: `tests/cytoplasm/test_fluid_mechanics.py`

- [ ] **Step 1: Write the failing test**

Create `tests/cytoplasm/test_fluid_mechanics.py`:

```python
"""L4 unit tests: fluid_mechanics skeleton plugin."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.cytoplasm.plugins.fluid_mechanics import FluidMechanicsPlugin


def test_fluid_mechanics_selects_turbulent_at_high_reynolds() -> None:
    plugin = FluidMechanicsPlugin()
    model = plugin.select_model({"Reynolds": 5000.0, "Mach": 0.01})
    assert model.id == "turbulent_navier_stokes"


def test_fluid_mechanics_selects_compressible_at_high_mach() -> None:
    plugin = FluidMechanicsPlugin()
    model = plugin.select_model({"Reynolds": 100.0, "Mach": 0.5})
    assert model.id == "compressible_navier_stokes"


def test_fluid_mechanics_injects_continuity_constraint() -> None:
    plugin = FluidMechanicsPlugin()
    ctx = PipelineContext(query="q", membrane={"quantities": []})
    types = {c.constraint_type for c in plugin.inject_constraints(ctx)}
    assert "continuity" in types


def test_fluid_mechanics_computes_reynolds_from_membrane_quantities() -> None:
    plugin = FluidMechanicsPlugin()
    ctx = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "density", "value": 1000.0, "unit": "kg/m^3"},
                {"ref": "obj_1", "property": "velocity", "value": 2.0, "unit": "m/s"},
                {"ref": "obj_1", "property": "length", "value": 0.1, "unit": "m"},
            ]
        },
        config={"viscosity_pa_s": 0.001},
    )
    indicators = plugin.compute_indicators(ctx)
    assert indicators["Reynolds"] == 200_000.0
    assert indicators["Mach"] == 0.0  # no speed-of-sound quantity → default 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_fluid_mechanics.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/cytoplasm/plugins/fluid_mechanics.py`:

```python
"""Fluid mechanics domain plugin (skeleton / reference implementation)."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.affine import AffineType
from dbse.contracts.context import PipelineContext
from dbse.contracts.domain import Constraint, DomainModel, Invariant
from dbse.cytoplasm.indicators import quantity_value_si, reynolds
from dbse.cytoplasm.plugin import DomainPlugin

_A_SOUND_DEFAULT = 340.0  # m/s — dry air at STP, MVP constant


class FluidMechanicsPlugin:
    """Reynolds/Mach/Froude → laminar/turbulent/compressible model selection."""

    domain: ClassVar[str] = "fluid_mechanics"
    dimensionless_numbers: ClassVar[list[str]] = ["Reynolds", "Mach", "Froude"]

    def compute_indicators(self, ctx: PipelineContext) -> dict[str, float]:
        membrane = ctx.membrane or {}
        rho = quantity_value_si(membrane, "density") or 1.0
        velocity = quantity_value_si(membrane, "velocity") or 0.0
        length = quantity_value_si(membrane, "length")
        if length is None:
            length = quantity_value_si(membrane, "distance") or 1.0
        viscosity = float(ctx.config.get("viscosity_pa_s", 0.001))
        re = reynolds(rho, velocity, length, viscosity)
        mach = abs(velocity) / _A_SOUND_DEFAULT if velocity else 0.0
        # Froude skeleton: V / sqrt(g L) — g fixed for MVP
        g = 9.81
        froude = abs(velocity) / (g * length) ** 0.5 if length > 0 else 0.0
        return {"Reynolds": re, "Mach": mach, "Froude": froude}

    def select_model(self, indicators: dict[str, float]) -> DomainModel:
        ma = indicators.get("Mach", 0.0)
        re = indicators.get("Reynolds", 0.0)
        if ma > 0.3:
            return DomainModel(id="compressible_navier_stokes", label="Compressible Navier-Stokes")
        if re > 2300:
            return DomainModel(id="turbulent_navier_stokes", label="Turbulent (k-ε)")
        if re > 1:
            return DomainModel(id="laminar_navier_stokes", label="Laminar Navier-Stokes")
        return DomainModel(id="stokes_flow", label="Stokes (creeping flow)")

    def inject_constraints(self, ctx: PipelineContext) -> list[Constraint]:
        return [
            Constraint(expression="div(v) = 0", constraint_type="continuity"),
            Constraint(expression="v = 0", constraint_type="no_slip", boundary="walls"),
        ]

    def register_affine_types(self) -> list[AffineType]:
        return []

    def register_invariants(self) -> list[Invariant]:
        return []


def _type_check() -> None:
    _: DomainPlugin = FluidMechanicsPlugin()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_fluid_mechanics.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/cytoplasm/plugins/fluid_mechanics.py tests/cytoplasm/test_fluid_mechanics.py
git commit -m "feat(l4): fluid_mechanics skeleton plugin (Re/Ma/Fr model selection)"
```

---

## Task 9: Wire the `Cytoplasm` pipeline layer

**Files:**
- Modify: `dbse/layers/cytoplasm.py`
- Modify: `dbse/cytoplasm/__init__.py`
- Create: `tests/cytoplasm/test_layer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/cytoplasm/test_layer.py`:

```python
"""L4 layer integration tests."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.layers.cytoplasm import Cytoplasm
from dbse.cytoplasm.registry import PluginRegistry
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin


def test_cytoplasm_applies_classical_mechanics_plugin_by_domain_hint() -> None:
    registry = PluginRegistry()
    registry.register(ClassicalMechanicsPlugin())
    layer = Cytoplasm(registry=registry)
    ctx = PipelineContext(
        query="falling body",
        config={"domain_hint": "classical_mechanics"},
        membrane={
            "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 10.0, "unit": "m/s"},
            ],
            "relations": [],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "velocity"},
        },
        ast=None,
    )
    out = layer.process(ctx)
    assert out.domain_model == "quadratic_friction"
    assert out.invariants is not None
    assert any(inv.name == "v_lt_c" for inv in out.invariants)
    assert out.constraints is not None
    assert out.trace[-1].layer == "L4.CYTOPLASM"
    assert out.trace[-1].note == "applied"


def test_cytoplasm_plugin_disconnect_does_not_require_core_changes() -> None:
    registry = PluginRegistry()
    registry.register(ClassicalMechanicsPlugin())
    layer = Cytoplasm(registry=registry)
    registry.unregister("classical_mechanics")
    ctx = PipelineContext(
        query="q",
        config={"domain_hint": "classical_mechanics"},
        membrane={"quantities": []},
    )
    out = layer.process(ctx)
    assert out.trace[-1].note == "skipped:unknown-domain"
    assert out.invariants is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cytoplasm/test_layer.py -v`
Expected: FAIL — layer still pass-through stub.

- [ ] **Step 3: Write minimal implementation**

Replace `dbse/layers/cytoplasm.py`:

```python
"""L4 CYTOPLASM — epigenetics + domain plugins."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import PipelineContext
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin
from dbse.cytoplasm.plugins.fluid_mechanics import FluidMechanicsPlugin
from dbse.cytoplasm.registry import PluginRegistry


def default_registry() -> PluginRegistry:
    """Built-in plugins shipped with the core (connect/disconnect at runtime)."""
    reg = PluginRegistry()
    reg.register(ClassicalMechanicsPlugin())
    reg.register(FluidMechanicsPlugin())
    return reg


class Cytoplasm:
    """L4 layer: apply domain plugins → constraints, invariants, model selection."""

    name: ClassVar[str] = "L4.CYTOPLASM"

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self._registry = registry if registry is not None else default_registry()

    def process(self, ctx: PipelineContext) -> PipelineContext:
        hint = str(ctx.config.get("domain_hint", "")).strip()
        if not hint:
            ctx.record(self.name, note="skipped:no-domain-hint")
            return ctx
        plugin = self._registry.get(hint)
        if plugin is None:
            ctx.record(self.name, note="skipped:unknown-domain", domain_hint=hint)
            return ctx
        result = self._registry.apply(ctx, domains=[hint])
        if result.errors:
            ctx.record(self.name, note=f"plugin-error:{hint}", errors=result.errors)
            return ctx
        ctx.constraints = result.constraints
        ctx.invariants = result.invariants
        ctx.domain_model = result.domain_model
        ctx.domain_indicators = result.domain_indicators
        ctx.record(
            self.name,
            note="applied",
            domain=hint,
            domain_model=result.domain_model,
            indicators=result.domain_indicators,
        )
        return ctx
```

Update `dbse/cytoplasm/__init__.py` to export `PluginRegistry`, `ClassicalMechanicsPlugin`, `FluidMechanicsPlugin`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/cytoplasm/test_layer.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/layers/cytoplasm.py dbse/cytoplasm/__init__.py tests/cytoplasm/test_layer.py
git commit -m "feat(l4): wire CYTOPLASM layer with plugin registry"
```

---

## Task 10: Metamorphic tests — indicator unit invariance (QA level 4)

**Files:**
- Create: `tests/cytoplasm/test_metamorphic.py`

- [ ] **Step 1: Write metamorphic tests**

Create `tests/cytoplasm/test_metamorphic.py`:

```python
"""L4 metamorphic tests: model selection invariant under unit rescaling."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.cytoplasm.plugins.classical_mechanics import ClassicalMechanicsPlugin
from dbse.cytoplasm.plugins.fluid_mechanics import FluidMechanicsPlugin


def test_classical_mechanics_model_stable_under_velocity_unit_change() -> None:
    plugin = ClassicalMechanicsPlugin()
    si = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 3.6, "unit": "km/h"},
            ]
        },
    )
    native = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "velocity", "value": 1.0, "unit": "m/s"},
            ]
        },
    )
    model_si = plugin.select_model(plugin.compute_indicators(si))
    model_native = plugin.select_model(plugin.compute_indicators(native))
    assert model_si.id == model_native.id == "linear_friction"


def test_fluid_mechanics_reynolds_stable_under_compatible_units() -> None:
    plugin = FluidMechanicsPlugin()
    ctx_a = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "density", "value": 1000.0, "unit": "kg/m^3"},
                {"ref": "obj_1", "property": "velocity", "value": 1.0, "unit": "m/s"},
                {"ref": "obj_1", "property": "length", "value": 0.01, "unit": "m"},
            ]
        },
        config={"viscosity_pa_s": 0.001},
    )
    ctx_b = PipelineContext(
        query="q",
        membrane={
            "quantities": [
                {"ref": "obj_1", "property": "density", "value": 1000.0, "unit": "kg/m^3"},
                {"ref": "obj_1", "property": "velocity", "value": 3.6, "unit": "km/h"},
                {"ref": "obj_1", "property": "length", "value": 1.0, "unit": "cm"},
            ]
        },
        config={"viscosity_pa_s": 0.001},
    )
    ind_a = plugin.compute_indicators(ctx_a)
    ind_b = plugin.compute_indicators(ctx_b)
    model_a = plugin.select_model(ind_a)
    model_b = plugin.select_model(ind_b)
    assert ind_a["Reynolds"] == ind_b["Reynolds"]
    assert model_a.id == model_b.id
```

- [ ] **Step 2: Run metamorphic tests**

Run: `python -m pytest tests/cytoplasm/test_metamorphic.py -v`
Expected: PASS (2 tests).

- [ ] **Step 3: Commit**

```bash
git add tests/cytoplasm/test_metamorphic.py
git commit -m "test(l4): metamorphic indicator invariance under unit change"
```

---

## Task 11: Full quality gate + pipeline skeleton still green

**Files:** none (verification only).

- [ ] **Step 1: Run the full QA gate**

Run: `ruff check . ; mypy ; python -m pytest -q`
Expected: `All checks passed!`; `Success: no issues found`; all tests pass including `tests/test_pipeline_skeleton.py`.

- [ ] **Step 2: Commit if any fixups were needed**

Only if fixups were required in Step 1.

---

## Task 12: Update status docs

**Files:**
- Modify: `README.md`
- Modify: `docs/spec-notes.md`

- [ ] **Step 1: Update README status**

Append to `README.md` "Статус":

```markdown
- Этап 5 — L4 CYTOPLASM: ✅ Domain Plugin API (`DomainPlugin` Protocol),
  stdlib `PluginRegistry` (pluggy-стиль без зависимости), плагины
  `classical_mechanics` (инварианты `v<c`, выбор linear/quadratic friction)
  и каркас `fluid_mechanics` (Re/Ma/Fr → model). Слой `L4.CYTOPLASM`
  читает `config.domain_hint`, пишет `constraints`/`invariants`/`domain_model`
  для NUCLEUS (Этап 7). Плагины подключаются/отключаются без изменения ядра.
```

- [ ] **Step 2: Record Stage 5 decisions in spec-notes**

Append to `docs/spec-notes.md`:

```markdown
## L4 (Stage 5) — принятые решения
- **`DomainPlugin` Protocol** в `dbse/cytoplasm/plugin.py`: шесть хуков
  (`compute_indicators`, `select_model`, `inject_constraints`,
  `register_affine_types`, `register_invariants`) + `dimensionless_numbers`.
- **Registry без pluggy** — `PluginRegistry` с явным порядком регистрации и
  per-plugin error isolation (`CytoplasmError` → trace, не crash пайплайна).
- **Domain hint только из `ctx.config`** (API `context.domain_hint`), не из
  MEMBRANE — сохраняем sandbox Stage 3 (LLM не эмитит `CONTEXT`).
- **Инварианты — data-only** на этом этапе; Continuous Invariant Monitor
  (SymPy/Z3) — Этап 7. `classical_mechanics` инъецирует `v_lt_c` (CRITICAL) и
  `energy_conserved` (SOFT).
- **Friction selection:** `drag_regime = |v|/v_ref` (default `v_ref=1 m/s`);
  `<1` → `linear_friction`, `≥1` → `quadratic_friction`.
- **`fluid_mechanics`** — reference skeleton по спеке (Re>2300 turbulent,
  Ma>0.3 compressible); не блокирует MVP.
- **QA-гейт:** уровни 1 (юнит + layer) + 4 (`test_metamorphic.py` — стабильность
  model selection при смене единиц индикаторов).
```

- [ ] **Step 3: Commit docs**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 5 (L4 CYTOPLASM) complete"
```

---

## Self-review (plan author checklist)

**Spec coverage (ROADMAP Stage 5):**
- `DomainPlugin` Protocol with all six hooks → Tasks 4, 6, 8 ✅
- Plugin registry, order, isolation → Task 5, 9 ✅
- `classical_mechanics` — invariants + friction model selection → Tasks 6–7 ✅
- `fluid_mechanics` skeleton (Re/Ma/Froude) → Task 8 ✅
- DoD: plugin connect/disconnect without core change → Task 9 test ✅
- DoD: invariants visible for Stage 7 → Task 9 `ctx.invariants` ✅
- QA level 4 metamorphic → Task 10 ✅

**Placeholder scan:** no TBD/TODO steps ✅

**Type consistency:** `Constraint`, `Invariant`, `DomainModel`, `PipelineContext` L4 fields, trace notes consistent across tasks ✅
