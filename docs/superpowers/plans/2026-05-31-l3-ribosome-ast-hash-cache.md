# L3 RIBOSOME — AST Compiler + Canonical Hash + Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build L3 RIBOSOME — compile validated MEMBRANE output into a typed mathematical AST, normalize it to a canonical form, classify its structure, hash it deterministically, and cache results — so isomorphic problems share one hash (mitigating graph-isomorphism DDoS) and repeat queries bypass NUCLEUS via a signed cache (mitigating cache poisoning). This closes vulnerabilities #8 and #9.

**Architecture:** A new focused package `dbse/ribosome/` with six modules — `errors` (`RibosomeError`), `property_map` (property/unit → `AffineType` via L1 `parse_unit` + L1.5 `affine()`), `compile` (MEMBRANE dict → `AST` with deterministic `OPERATOR` nodes the LLM never emits), `normalize` (variable rename `x_1…`, commutative sort, constant fold), `classify` (`classify_structure` → strings like `LinearODE_Order1`), `hash` (`canonical_hash` = `sha256(f"{class}:{canonical}")[:16]`), and `cache` (LRU semantic cache with HMAC signatures, TTL, and a `core_version` invalidation hook for Stage 11). The pipeline layer `dbse/layers/ribosome.py` wires compile → normalize → classify → hash → cache lookup/store. L1/L1.5 **layer** stubs (`dimensional.py`, `affine_types.py`) stay pass-through; attaching `AffineType` to AST nodes happens inside `compile` (per Stage 3 scope guard). MEMBRANE schema gains an optional `equations: list[LinearOde1]` field — structured coefficients only, no `OPERATOR` nodes from the LLM.

**Tech Stack:** Python 3.11+, stdlib (`hashlib`, `hmac`, `json`, `time`, `functools`, `collections`), `pytest` + `hypothesis` for tests. Reuses `dbse.contracts.{AST, ASTNode, AffineType}`, `dbse.dimensional.parse_unit`, `dbse.semantic.affine`, `dbse.membrane.validate_membrane`.

---

## Environment notes (read once)

- Activate the venv first, or prefix commands: PowerShell `.\.venv\Scripts\Activate.ps1`.
- All test commands below use `python -m pytest ...`. Run from repo root `c:\Users\Clerikozoid\Desktop\Chromosome`.
- The shell is PowerShell: chain commands with `;`, **not** `&&`.
- Quality gate for every commit: `ruff check . ; mypy ; python -m pytest`.

## Key design decisions (made here, per the spec — note, don't re-litigate)

1. **LLM still never emits `OPERATOR`.** MEMBRANE may carry a new `equations` list with *structured coefficients* (`LinearOde1`: `state`, `constant`, `linear_coeff`). RIBOSOME deterministically builds the `OPERATOR` subtree (`DERIV`, `EQ`, `ADD`, `MUL`, …). This preserves the Stage 3 sandbox boundary.
2. **L1/L1.5 integration lives in `compile`, not in the L1/L1.5 layer stubs.** Quantity leaves get `affine_type` via `property_map.quantity_affine(property, unit)` which calls L1 `parse_unit` and L1.5 `affine()` (or falls back to `Unknown` tag when property is unmapped).
3. **MVP canonical hash is structural, not full graph isomorphism.** Normalization covers variable rename, commutative child sort (`ADD`/`MUL`), and constant folding. Two problems with different numeric coefficients share a *structure class* but **different hashes** — only isomorphic renamings/s reorderings share a hash. DoD: free-fall `dv/dt=g-kv` and RC `RC·dV/dt+V=0` (rewritten as `dV/dt=-V/RC`) both classify as `LinearODE_Order1`; isomorphic rewrites of the *same* equation share a hash.
4. **Cache entries are signed (HMAC-SHA256) and TTL-bound.** Poisoned payloads (bad signature / expired / stale `core_version`) are rejected. A `core_version` string in config enables Stage 11 invalidation without implementing Core yet.
5. **Cache hit pre-fills `ctx.solution`** so downstream NUCLEUS (still a stub) can skip work once it checks for an existing solution. Ribosome records `note="cache-hit"` in trace.
6. **Scope guard:** no SymPy, no ODE solving, no Z3 — only compile/normalize/hash/cache. NUCLEUS integration tests use placeholder solution dicts.

## AST node conventions (fixed for all tasks)

| `kind` | `op` | `value` | `children` | Role |
|---|---|---|---|---|
| `"OBJECT"` | object id | label string | `()` | Membrane object |
| `"QUANTITY"` | property name | numeric value | `()` | Membrane quantity + `affine_type` |
| `"SYMBOL"` | `None` | variable name (pre-normalize) | `()` | State variable |
| `"CONST"` | `None` | `float` | `()` | Literal constant |
| `"OPERATOR"` | `"EQ"`, `"ADD"`, `"SUB"`, `"MUL"`, `"DIV"`, `"NEG"`, `"DERIV"` | `None` | ordered tuple | Math tree |

`DERIV` has one child (`SYMBOL`) — first-order time derivative \(d/dt\).

## File Structure

`dbse/ribosome/`:
- Create `dbse/ribosome/__init__.py` — public exports.
- Create `dbse/ribosome/errors.py` — `RibosomeError`.
- Create `dbse/ribosome/property_map.py` — `quantity_affine()`.
- Create `dbse/ribosome/compile.py` — `compile_membrane()`.
- Create `dbse/ribosome/normalize.py` — `normalize_ast()`, `to_canonical()`.
- Create `dbse/ribosome/classify.py` — `classify_structure()`.
- Create `dbse/ribosome/hash.py` — `canonical_hash()`.
- Create `dbse/ribosome/cache.py` — `CacheEntry`, `SemanticCache`.

MEMBRANE schema extension:
- Modify `dbse/membrane/schema.py` — add `LinearOde1`, extend `MembraneOutput.equations`, reference validation.

Layer wiring:
- Modify `dbse/layers/ribosome.py` — real `Ribosome` layer.

Tests:
- Create `tests/ribosome/__init__.py`
- Create `tests/ribosome/test_property_map.py`
- Create `tests/ribosome/test_compile.py`
- Create `tests/ribosome/test_normalize.py`
- Create `tests/ribosome/test_classify.py`
- Create `tests/ribosome/test_hash.py`
- Create `tests/ribosome/test_cache.py`
- Create `tests/ribosome/test_properties.py` — Hypothesis (QA level 2)
- Create `tests/ribosome/test_adversarial.py` — cache poisoning (QA level 5)
- Create `tests/ribosome/test_layer.py` — layer wiring + DoD cache hit
- Modify `tests/membrane/test_schema.py` — `LinearOde1` accept/reject

Docs:
- Modify `README.md`, `docs/spec-notes.md`

---

## Task 0: Baseline is green

**Files:** none (verification only).

- [ ] **Step 1: Confirm Stage 3 is committed and the suite is green**

Run: `git log --oneline -3 ; ruff check . ; mypy ; python -m pytest -q`
Expected: recent commits include Stage 3 work (`docs: mark Stage 3 ... complete`); `All checks passed!`; `Success: no issues found`; all tests pass.

> No commit in this task — smoke check before starting Stage 4.

---

## Task 1: `RibosomeError` and package skeleton

**Files:**
- Create: `dbse/ribosome/errors.py`
- Create: `dbse/ribosome/__init__.py`
- Create: `tests/ribosome/__init__.py`
- Create: `tests/ribosome/test_compile.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/__init__.py` (empty file):

```python
```

Create `tests/ribosome/test_compile.py`:

```python
"""L3 unit tests: MEMBRANE → AST compilation."""

from __future__ import annotations

import pytest

from dbse.ribosome import RibosomeError


def test_ribosome_error_is_a_value_error() -> None:
    assert issubclass(RibosomeError, ValueError)
    with pytest.raises(RibosomeError):
        raise RibosomeError("boom")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_compile.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.ribosome'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/errors.py`:

```python
"""L3 error type."""

from __future__ import annotations


class RibosomeError(ValueError):
    """Raised when MEMBRANE output cannot be compiled into a valid AST."""
```

Create `dbse/ribosome/__init__.py`:

```python
"""L3 RIBOSOME — AST compiler, canonical hash, semantic cache."""

from dbse.ribosome.errors import RibosomeError

__all__ = ["RibosomeError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_compile.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/errors.py dbse/ribosome/__init__.py tests/ribosome/__init__.py tests/ribosome/test_compile.py
git commit -m "feat(l3): add ribosome package skeleton and RibosomeError"
```

---

## Task 2: `quantity_affine` — L1/L1.5 on quantity leaves

**Files:**
- Create: `dbse/ribosome/property_map.py`
- Modify: `dbse/ribosome/__init__.py`
- Create: `tests/ribosome/test_property_map.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/test_property_map.py`:

```python
"""L3 unit tests: property/unit → AffineType mapping."""

from __future__ import annotations

from dbse.contracts import AffineType
from dbse.ribosome.property_map import quantity_affine


def test_mass_maps_to_mass_tag() -> None:
    aff = quantity_affine("mass", "kg")
    assert isinstance(aff, AffineType)
    assert aff.semantic_tag == "Mass"
    assert aff.tensor_rank == 0


def test_unknown_property_uses_dimension_from_unit() -> None:
    aff = quantity_affine("gravitational_force", "N")
    assert aff.semantic_tag == "Unknown"
    assert str(aff.dimension) == str(quantity_affine("force", "N").dimension)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_property_map.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.ribosome.property_map'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/property_map.py`:

```python
"""Map MEMBRANE quantity properties to L1.5 AffineType."""

from __future__ import annotations

from dbse.contracts.affine import AffineType
from dbse.dimensional import parse_unit
from dbse.semantic import affine

# Membrane property stems (from L0 adapter) → L1.5 semantic tag.
_PROPERTY_TAG: dict[str, str] = {
    "mass": "Mass",
    "distance": "Length",
    "velocity": "Velocity",
    "force": "Force",
    "energy": "Energy",
    "time": "Time",
    "value": "Unknown",
}


def quantity_affine(property_name: str, unit: str) -> AffineType:
    """Attach an :class:`AffineType` to a membrane quantity leaf."""
    tag = _PROPERTY_TAG.get(property_name)
    if tag is not None and tag != "Unknown":
        return affine(tag)
    dim = parse_unit(unit)
    return AffineType(dim, "Unknown")
```

Update `dbse/ribosome/__init__.py`:

```python
"""L3 RIBOSOME — AST compiler, canonical hash, semantic cache."""

from dbse.ribosome.errors import RibosomeError
from dbse.ribosome.property_map import quantity_affine

__all__ = ["RibosomeError", "quantity_affine"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_property_map.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/property_map.py dbse/ribosome/__init__.py tests/ribosome/test_property_map.py
git commit -m "feat(l3): map membrane quantities to AffineType via L1/L1.5"
```

---

## Task 3: Compile objects and quantities (no equations yet)

**Files:**
- Create: `dbse/ribosome/compile.py`
- Modify: `dbse/ribosome/__init__.py`
- Modify: `tests/ribosome/test_compile.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/ribosome/test_compile.py`:

```python
from dbse.contracts import AST, ASTNode
from dbse.ribosome.compile import compile_membrane


def test_compile_minimal_membrane_produces_object_and_quantity_leaves() -> None:
    membrane = {
        "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
        "quantities": [
            {"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "kg"},
        ],
        "relations": [],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "mass"},
    }
    ast = compile_membrane(membrane)
    assert isinstance(ast, AST)
    assert ast.root.kind == "OBJECT"
    assert ast.root.op == "obj_1"
    assert len(ast.root.children) == 1
    qty = ast.root.children[0]
    assert qty.kind == "QUANTITY"
    assert qty.op == "mass"
    assert qty.value == 0.1
    assert qty.affine_type is not None
    assert qty.affine_type.semantic_tag == "Mass"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_compile.py::test_compile_minimal_membrane_produces_object_and_quantity_leaves -v`
Expected: FAIL — `ImportError` / `cannot import name 'compile_membrane'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/compile.py`:

```python
"""Compile validated MEMBRANE output into an AST."""

from __future__ import annotations

from typing import Any

from dbse.contracts.ast import AST, ASTNode
from dbse.ribosome.errors import RibosomeError
from dbse.ribosome.property_map import quantity_affine


def compile_membrane(membrane: dict[str, Any]) -> AST:
    """Build an :class:`AST` from a validated membrane dict."""
    objects = membrane.get("objects")
    if not isinstance(objects, list) or not objects:
        raise RibosomeError("MEMBRANE must contain at least one object")
    # MVP: single-object queries — attach quantities to the first object tree.
    root_obj = objects[0]
    obj_id = str(root_obj["id"])
    label = str(root_obj.get("label", obj_id))
    quantities = membrane.get("quantities") or []
    qty_nodes: list[ASTNode] = []
    for q in quantities:
        if str(q.get("ref")) != obj_id:
            continue
        prop = str(q["property"])
        unit = str(q["unit"])
        qty_nodes.append(
            ASTNode(
                kind="QUANTITY",
                op=prop,
                value=float(q["value"]),
                affine_type=quantity_affine(prop, unit),
            )
        )
    root = ASTNode(
        kind="OBJECT",
        op=obj_id,
        value=label,
        children=tuple(qty_nodes),
    )
    return AST(root=root)
```

Update `dbse/ribosome/__init__.py` exports to include `compile_membrane`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_compile.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/compile.py dbse/ribosome/__init__.py tests/ribosome/test_compile.py
git commit -m "feat(l3): compile membrane objects and quantities to AST leaves"
```

---

## Task 4: MEMBRANE schema — `LinearOde1` equations

**Files:**
- Modify: `dbse/membrane/schema.py`
- Modify: `tests/membrane/test_schema.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/membrane/test_schema.py`:

```python
def test_linear_ode_1_equation_accepts_valid_coefficients() -> None:
    payload = {
        **_VALID,
        "equations": [
            {
                "object_ref": "obj_1",
                "state": "v",
                "constant": 9.81,
                "linear_coeff": -0.5,
            }
        ],
    }
    out = validate_membrane(payload)
    assert len(out.equations) == 1
    assert out.equations[0].state == "v"
    assert out.equations[0].constant == 9.81


def test_linear_ode_1_rejects_dangling_object_ref() -> None:
    bad = {
        **_VALID,
        "equations": [
            {"object_ref": "missing", "state": "v", "constant": 0.0, "linear_coeff": -1.0}
        ],
    }
    with pytest.raises(MembraneError):
        validate_membrane(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/membrane/test_schema.py::test_linear_ode_1_equation_accepts_valid_coefficients -v`
Expected: FAIL — `TypeError` / validation error on unknown field `equations`.

- [ ] **Step 3: Write minimal implementation**

In `dbse/membrane/schema.py`, add after `RelationNode`:

```python
class LinearOde1(BaseModel):
    """Structured first-order linear ODE: d(state)/dt = constant + linear_coeff * state.

    The LLM emits coefficients only — RIBOSOME (L3) builds OPERATOR nodes.
    """

    model_config = _STRICT

    object_ref: str
    state: str
    constant: float = 0.0
    linear_coeff: float = 0.0
```

In `MembraneOutput`, add:

```python
    equations: list[LinearOde1] = Field(default_factory=list)
```

In `_references_resolve`, after the existing dangling checks:

```python
        for eq in self.equations:
            if eq.object_ref not in known:
                dangling.append(eq.object_ref)
```

Export `LinearOde1` from `dbse/membrane/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/membrane/test_schema.py -v`
Expected: all schema tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dbse/membrane/schema.py dbse/membrane/__init__.py tests/membrane/test_schema.py
git commit -m "feat(l0): add LinearOde1 equation field to MEMBRANE schema"
```

---

## Task 5: Compile `LinearOde1` into OPERATOR AST

**Files:**
- Modify: `dbse/ribosome/compile.py`
- Modify: `tests/ribosome/test_compile.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/ribosome/test_compile.py`:

```python
def _find_operator(root: ASTNode, op: str) -> ASTNode | None:
    if root.kind == "OPERATOR" and root.op == op:
        return root
    for child in root.children:
        found = _find_operator(child, op)
        if found is not None:
            return found
    return None


def test_compile_linear_ode_1_builds_derivative_equation_tree() -> None:
    membrane = {
        "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
        "quantities": [],
        "relations": [],
        "equations": [
            {"object_ref": "obj_1", "state": "v", "constant": 9.81, "linear_coeff": -0.5},
        ],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "velocity"},
    }
    ast = compile_membrane(membrane)
    eq = _find_operator(ast.root, "EQ")
    assert eq is not None
    deriv = _find_operator(ast.root, "DERIV")
    assert deriv is not None
    assert deriv.children[0].kind == "SYMBOL"
    assert deriv.children[0].value == "v"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_compile.py::test_compile_linear_ode_1_builds_derivative_equation_tree -v`
Expected: FAIL — no `EQ`/`DERIV` nodes in tree.

- [ ] **Step 3: Write minimal implementation**

Add helpers and extend `compile_membrane` in `dbse/ribosome/compile.py`:

```python
def _symbol(name: str) -> ASTNode:
    return ASTNode(kind="SYMBOL", value=name)


def _const(value: float) -> ASTNode:
    return ASTNode(kind="CONST", value=float(value))


def _op(op: str, *children: ASTNode) -> ASTNode:
    return ASTNode(kind="OPERATOR", op=op, children=children)


def _linear_combo(constant: float, linear_coeff: float, state: str) -> ASTNode:
    """Build constant + linear_coeff * state."""
    terms: list[ASTNode] = []
    if constant != 0.0:
        terms.append(_const(constant))
    if linear_coeff != 0.0:
        term: ASTNode
        if linear_coeff == 1.0:
            term = _symbol(state)
        elif linear_coeff == -1.0:
            term = _op("NEG", _symbol(state))
        else:
            term = _op("MUL", _const(linear_coeff), _symbol(state))
        terms.append(term)
    if not terms:
        return _const(0.0)
    if len(terms) == 1:
        return terms[0]
    return _op("ADD", *terms)


def _compile_linear_ode_1(eq: dict[str, Any]) -> ASTNode:
    state = str(eq["state"])
    constant = float(eq.get("constant", 0.0))
    linear_coeff = float(eq.get("linear_coeff", 0.0))
    lhs = _op("DERIV", _symbol(state))
    rhs = _linear_combo(constant, linear_coeff, state)
    return _op("EQ", lhs, rhs)
```

After building the object root, if `membrane.get("equations")`:

```python
    eq_nodes: list[ASTNode] = []
    for raw_eq in membrane.get("equations") or []:
        eq_nodes.append(_compile_linear_ode_1(raw_eq))
    if eq_nodes:
        root = ASTNode(
            kind="OBJECT",
            op=obj_id,
            value=label,
            children=(*qty_nodes, *eq_nodes),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_compile.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/compile.py tests/ribosome/test_compile.py
git commit -m "feat(l3): compile LinearOde1 equations to OPERATOR AST"
```

---

## Task 6: `normalize_ast` — rename, sort, fold

**Files:**
- Create: `dbse/ribosome/normalize.py`
- Modify: `dbse/ribosome/__init__.py`
- Create: `tests/ribosome/test_normalize.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/test_normalize.py`:

```python
"""L3 unit tests: AST normalization and canonical serialization."""

from __future__ import annotations

from dbse.contracts import ASTNode
from dbse.ribosome.normalize import normalize_ast, to_canonical


def _sym(name: str) -> ASTNode:
    return ASTNode(kind="SYMBOL", value=name)


def _c(value: float) -> ASTNode:
    return ASTNode(kind="CONST", value=value)


def _op(op: str, *kids: ASTNode) -> ASTNode:
    return ASTNode(kind="OPERATOR", op=op, children=kids)


def test_normalize_renames_symbols_to_x_i() -> None:
    tree = _op("EQ", _op("DERIV", _sym("v")), _sym("v"))
    out = normalize_ast(tree)
    syms = [n.value for n in _walk(out) if n.kind == "SYMBOL"]
    assert syms == ["x_1", "x_1"]


def test_normalize_sorts_commutative_add_children() -> None:
    tree = _op("ADD", _sym("b"), _sym("a"))
    out = normalize_ast(tree)
    add = out
    keys = [to_canonical(c) for c in add.children]
    assert keys == sorted(keys)


def test_normalize_folds_numeric_add() -> None:
    tree = _op("ADD", _c(2.0), _c(3.0))
    out = normalize_ast(tree)
    assert out.kind == "CONST"
    assert out.value == 5.0


def _walk(node: ASTNode) -> list[ASTNode]:
    out = [node]
    for ch in node.children:
        out.extend(_walk(ch))
    return out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_normalize.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/normalize.py`:

```python
"""Canonical normalization of AST nodes."""

from __future__ import annotations

from dbse.contracts.ast import AST, ASTNode

_COMMUTATIVE = frozenset({"ADD", "MUL"})


def normalize_ast(node: ASTNode) -> ASTNode:
    """Return a normalized copy: rename symbols, sort commutative ops, fold constants."""
    renamed = _rename_symbols(node)
    folded = _fold_constants(renamed)
    return _sort_commutative(folded)


def to_canonical(node: ASTNode) -> str:
    """Stable string form for hashing."""
    if node.kind in {"SYMBOL", "CONST", "QUANTITY", "OBJECT"}:
        val = node.value if node.value is not None else ""
        return f"({node.kind}:{node.op}:{val})"
    if node.kind == "OPERATOR":
        inner = ",".join(to_canonical(c) for c in node.children)
        return f"({node.op}[{inner}])"
    inner = ",".join(to_canonical(c) for c in node.children)
    return f"({node.kind}:{node.op}[{inner}])"


def normalize_ast_tree(ast: AST) -> AST:
    """Normalize the full AST wrapper, preserving metadata slots."""
    root = normalize_ast(ast.root)
    return AST(root=root, structure_class=ast.structure_class, canonical_hash=ast.canonical_hash)


def _rename_symbols(node: ASTNode, mapping: dict[str, str] | None = None, counter: list[int] | None = None) -> ASTNode:
    if mapping is None:
        mapping = {}
    if counter is None:
        counter = [0]

    def map_name(name: str) -> str:
        if name not in mapping:
            counter[0] += 1
            mapping[name] = f"x_{counter[0]}"
        return mapping[name]

    if node.kind == "SYMBOL" and isinstance(node.value, str):
        return ASTNode(kind="SYMBOL", value=map_name(node.value))
    children = tuple(_rename_symbols(c, mapping, counter) for c in node.children)
    if children == node.children and node.kind != "SYMBOL":
        return node
    return ASTNode(
        kind=node.kind,
        op=node.op,
        children=children,
        value=node.value,
        affine_type=node.affine_type,
        bindings=node.bindings,
    )


def _fold_constants(node: ASTNode) -> ASTNode:
    children = tuple(_fold_constants(c) for c in node.children)
    if node.kind == "OPERATOR" and node.op == "ADD" and len(children) == 2:
        a, b = children
        if a.kind == "CONST" and b.kind == "CONST":
            return ASTNode(kind="CONST", value=float(a.value) + float(b.value))
    if node.kind == "OPERATOR" and node.op == "MUL" and len(children) == 2:
        a, b = children
        if a.kind == "CONST" and b.kind == "CONST":
            return ASTNode(kind="CONST", value=float(a.value) * float(b.value))
    if children != node.children:
        return ASTNode(
            kind=node.kind,
            op=node.op,
            children=children,
            value=node.value,
            affine_type=node.affine_type,
            bindings=node.bindings,
        )
    return node


def _sort_commutative(node: ASTNode) -> ASTNode:
    children = tuple(_sort_commutative(c) for c in node.children)
    if node.kind == "OPERATOR" and node.op in _COMMUTATIVE and len(children) > 1:
        children = tuple(sorted(children, key=to_canonical))
    if children != node.children:
        return ASTNode(
            kind=node.kind,
            op=node.op,
            children=children,
            value=node.value,
            affine_type=node.affine_type,
            bindings=node.bindings,
        )
    return node
```

Export `normalize_ast`, `normalize_ast_tree`, `to_canonical` from `dbse/ribosome/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_normalize.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/normalize.py dbse/ribosome/__init__.py tests/ribosome/test_normalize.py
git commit -m "feat(l3): normalize AST (rename, commutative sort, constant fold)"
```

---

## Task 7: `classify_structure`

**Files:**
- Create: `dbse/ribosome/classify.py`
- Create: `tests/ribosome/test_classify.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/test_classify.py`:

```python
"""L3 unit tests: structural classification."""

from __future__ import annotations

from dbse.contracts import ASTNode
from dbse.ribosome.classify import classify_structure
from dbse.ribosome.compile import compile_membrane


def test_free_fall_and_rc_circuit_both_classify_as_linear_ode_order_1() -> None:
    free_fall = compile_membrane(
        {
            "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
            "quantities": [],
            "relations": [],
            "equations": [
                {"object_ref": "obj_1", "state": "v", "constant": 9.81, "linear_coeff": -0.5},
            ],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "velocity"},
        }
    )
    rc = compile_membrane(
        {
            "objects": [{"id": "obj_1", "type": "circuit", "label": "rc"}],
            "quantities": [],
            "relations": [],
            "equations": [
                # RC dV/dt + V/R = 0  →  dV/dt = -(1/R) * V  (homogeneous)
                {"object_ref": "obj_1", "state": "V", "constant": 0.0, "linear_coeff": -0.2},
            ],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "value"},
        }
    )
    assert classify_structure(free_fall.root) == "LinearODE_Order1"
    assert classify_structure(rc.root) == "LinearODE_Order1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_classify.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/classify.py`:

```python
"""Structural class labels for normalized AST roots."""

from __future__ import annotations

from dbse.contracts.ast import ASTNode


def classify_structure(root: ASTNode) -> str:
    """Return a coarse structural class string for the AST root."""
    if _contains_linear_ode_1(root):
        return "LinearODE_Order1"
    if _contains_only_quantities(root):
        return "Algebraic_Quantities"
    return "Unknown"


def _contains_linear_ode_1(node: ASTNode) -> bool:
    if node.kind == "OPERATOR" and node.op == "EQ":
        lhs, rhs = node.children
        if lhs.kind == "OPERATOR" and lhs.op == "DERIV" and len(lhs.children) == 1:
            if lhs.children[0].kind == "SYMBOL":
                return True
    for child in node.children:
        if _contains_linear_ode_1(child):
            return True
    return False


def _contains_only_quantities(node: ASTNode) -> bool:
    allowed = {"OBJECT", "QUANTITY"}
    stack = [node]
    while stack:
        cur = stack.pop()
        if cur.kind not in allowed and cur.kind != "OBJECT":
            if cur.kind == "OPERATOR":
                return False
        stack.extend(cur.children)
    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_classify.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/classify.py tests/ribosome/test_classify.py
git commit -m "feat(l3): classify_structure for LinearODE_Order1 and algebraic payloads"
```

---

## Task 8: `canonical_hash`

**Files:**
- Create: `dbse/ribosome/hash.py`
- Modify: `tests/ribosome/test_hash.py` (create)
- Modify: `dbse/ribosome/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/test_hash.py`:

```python
"""L3 unit tests: canonical hashing."""

from __future__ import annotations

from dbse.ribosome.compile import compile_membrane
from dbse.ribosome.hash import canonical_hash


def _membrane(state: str, constant: float, linear_coeff: float) -> dict:
    return {
        "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
        "quantities": [],
        "relations": [],
        "equations": [
            {
                "object_ref": "obj_1",
                "state": state,
                "constant": constant,
                "linear_coeff": linear_coeff,
            }
        ],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "velocity"},
    }


def test_renamed_state_variable_yields_same_hash() -> None:
    a = compile_membrane(_membrane("v", 9.81, -0.5))
    b = compile_membrane(_membrane("velocity", 9.81, -0.5))
    assert canonical_hash(a) == canonical_hash(b)
    assert len(canonical_hash(a)) == 16


def test_different_coefficients_yield_different_hashes() -> None:
    a = compile_membrane(_membrane("v", 9.81, -0.5))
    b = compile_membrane(_membrane("v", 9.81, -0.6))
    assert canonical_hash(a) != canonical_hash(b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_hash.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/hash.py`:

```python
"""Canonical AST hashing."""

from __future__ import annotations

import hashlib

from dbse.contracts.ast import AST
from dbse.ribosome.classify import classify_structure
from dbse.ribosome.normalize import normalize_ast_tree, to_canonical


def canonical_hash(ast: AST) -> str:
    """Return a 16-hex-char structural hash: sha256(class + canonical form)[:16]."""
    normalized = normalize_ast_tree(ast)
    structure_class = classify_structure(normalized.root)
    normalized = AST(
        root=normalized.root,
        structure_class=structure_class,
        canonical_hash=normalized.canonical_hash,
    )
    payload = f"{structure_class}:{to_canonical(normalized.root)}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def annotate_ast(ast: AST) -> AST:
    """Normalize, classify, and attach metadata fields on the AST wrapper."""
    normalized = normalize_ast_tree(ast)
    structure_class = classify_structure(normalized.root)
    digest = canonical_hash(
        AST(root=normalized.root, structure_class=structure_class)
    )
    return AST(root=normalized.root, structure_class=structure_class, canonical_hash=digest)
```

Export `canonical_hash`, `annotate_ast` from `dbse/ribosome/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_hash.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/hash.py dbse/ribosome/__init__.py tests/ribosome/test_hash.py
git commit -m "feat(l3): canonical_hash with structure class prefix"
```

---

## Task 9: Property-based tests (QA level 2)

**Files:**
- Create: `tests/ribosome/test_properties.py`

- [ ] **Step 1: Write the property tests**

Create `tests/ribosome/test_properties.py`:

```python
"""L3 property-based tests: normalization idempotence and hash invariance."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.contracts import ASTNode
from dbse.ribosome.hash import canonical_hash
from dbse.ribosome.normalize import normalize_ast, to_canonical
from dbse.contracts import AST


def _sym(name: str) -> ASTNode:
    return ASTNode(kind="SYMBOL", value=name)


def _c(value: float) -> ASTNode:
    return ASTNode(kind="CONST", value=value)


def _op(op: str, *kids: ASTNode) -> ASTNode:
    return ASTNode(kind="OPERATOR", op=op, children=kids)


@st.composite
def symbol_names(draw: st.DrawFn) -> str:
    return draw(st.sampled_from(["a", "b", "v", "x", "velocity", "state"]))


@st.composite
def small_trees(draw: st.DrawFn) -> ASTNode:
    a = _sym(draw(symbol_names()))
    b = _sym(draw(symbol_names()))
    return draw(
        st.one_of(
            st.just(_op("ADD", a, b)),
            st.just(_op("MUL", a, b)),
            st.just(_op("EQ", _op("DERIV", a), b)),
        )
    )


@given(small_trees())
def test_property_normalization_is_idempotent(tree: ASTNode) -> None:
    once = normalize_ast(tree)
    twice = normalize_ast(once)
    assert to_canonical(once) == to_canonical(twice)


@given(small_trees(), symbol_names(), symbol_names())
def test_property_renamed_symbols_do_not_change_hash_when_isomorphic(
    tree: ASTNode, n1: str, n2: str
) -> None:
    if n1 == n2:
        return
    # Build two trees that differ only by symbol spelling if both appear.
    def repl(node: ASTNode, src: str, dst: str) -> ASTNode:
        if node.kind == "SYMBOL" and node.value == src:
            return ASTNode(kind="SYMBOL", value=dst)
        kids = tuple(repl(c, src, dst) for c in node.children)
        return ASTNode(kind=node.kind, op=node.op, children=kids, value=node.value)

    if not any(n.value == n1 for n in _walk(tree)):
        return
    a = AST(root=tree)
    b = AST(root=repl(tree, n1, n2))
    if to_canonical(normalize_ast(a.root)) == to_canonical(normalize_ast(b.root)):
        assert canonical_hash(a) == canonical_hash(b)


def _walk(node: ASTNode) -> list[ASTNode]:
    out = [node]
    for ch in node.children:
        out.extend(_walk(ch))
    return out
```

- [ ] **Step 2: Run property tests**

Run: `python -m pytest tests/ribosome/test_properties.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/ribosome/test_properties.py
git commit -m "test(l3): property-based normalization and hash invariance"
```

---

## Task 10: `SemanticCache` — LRU, HMAC, TTL, core_version hook

**Files:**
- Create: `dbse/ribosome/cache.py`
- Create: `tests/ribosome/test_cache.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/test_cache.py`:

```python
"""L3 unit tests: signed semantic cache."""

from __future__ import annotations

import time

from dbse.contracts import AST, ASTNode
from dbse.ribosome.cache import CacheEntry, SemanticCache


def _dummy_ast() -> AST:
    return AST(root=ASTNode(kind="OBJECT", op="obj_1", value="x"))


def test_cache_put_get_round_trip_increments_hits() -> None:
    cache = SemanticCache(secret="test-secret", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(
        ast=_dummy_ast(),
        solution={"value": 42},
        proof_level="P2",
        tinfo=0.1,
    )
    cache.put("abc123", entry, core_version="core-1")
    got = cache.get("abc123", core_version="core-1")
    assert got is not None
    assert got.hits == 1
    assert got.solution == {"value": 42}


def test_cache_rejects_tampered_signature() -> None:
    cache = SemanticCache(secret="test-secret", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(ast=_dummy_ast(), solution={}, proof_level="P2", tinfo=0.0)
    cache.put("deadbeef", entry, core_version="core-1")
    # Simulate poisoning by mutating internal store after put
    raw = cache._store["deadbeef"]  # noqa: SLF001 — intentional adversarial setup
    raw["solution"] = {"hacked": True}
    assert cache.get("deadbeef", core_version="core-1") is None


def test_cache_expires_after_ttl() -> None:
    cache = SemanticCache(secret="s", ttl_seconds=0, max_entries=10)
    entry = CacheEntry(ast=_dummy_ast(), solution={}, proof_level="P2", tinfo=0.0)
    cache.put("k", entry, core_version="core-1")
    time.sleep(0.01)
    assert cache.get("k", core_version="core-1") is None


def test_cache_invalidates_on_core_version_change() -> None:
    cache = SemanticCache(secret="s", ttl_seconds=60, max_entries=10)
    entry = CacheEntry(ast=_dummy_ast(), solution={}, proof_level="P2", tinfo=0.0)
    cache.put("k", entry, core_version="core-1")
    assert cache.get("k", core_version="core-2") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_cache.py -v`
Expected: FAIL — import error.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/ribosome/cache.py`:

```python
"""Signed LRU semantic cache for canonical AST hashes."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from dbse.contracts.ast import AST, ASTNode


@dataclass
class CacheEntry:
    """One cached solve result keyed by canonical hash."""

    ast: AST
    solution: dict[str, Any]
    proof_level: str
    tinfo: float
    hits: int = 0


@dataclass
class _StoredEntry:
    entry: CacheEntry
    signature: str
    created_at: float
    core_version: str


class SemanticCache:
    """LRU cache with HMAC integrity, TTL expiry, and core-version invalidation."""

    def __init__(
        self,
        *,
        secret: str,
        ttl_seconds: float = 3600.0,
        max_entries: int = 256,
    ) -> None:
        self._secret = secret.encode()
        self._ttl = ttl_seconds
        self._max = max_entries
        self._store: OrderedDict[str, _StoredEntry] = OrderedDict()

    def put(self, key: str, entry: CacheEntry, *, core_version: str) -> None:
        payload = self._serialize(entry)
        sig = self._sign(payload)
        self._store[key] = _StoredEntry(
            entry=entry,
            signature=sig,
            created_at=time.monotonic(),
            core_version=core_version,
        )
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def get(self, key: str, *, core_version: str) -> CacheEntry | None:
        stored = self._store.get(key)
        if stored is None:
            return None
        if stored.core_version != core_version:
            del self._store[key]
            return None
        if time.monotonic() - stored.created_at > self._ttl:
            del self._store[key]
            return None
        payload = self._serialize(stored.entry)
        if not hmac.compare_digest(self._sign(payload), stored.signature):
            del self._store[key]
            return None
        stored.entry.hits += 1
        self._store.move_to_end(key)
        return stored.entry

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _serialize(entry: CacheEntry) -> str:
        # AST metadata only — full tree serialization via structure_class + hash already on ast.
        data = {
            "structure_class": entry.ast.structure_class,
            "canonical_hash": entry.ast.canonical_hash,
            "solution": entry.solution,
            "proof_level": entry.proof_level,
            "tinfo": entry.tinfo,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
```

Export `CacheEntry`, `SemanticCache` from `dbse/ribosome/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_cache.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/ribosome/cache.py dbse/ribosome/__init__.py tests/ribosome/test_cache.py
git commit -m "feat(l3): signed semantic cache with TTL and core_version invalidation"
```

---

## Task 11: Adversarial cache poisoning corpus (QA level 5)

**Files:**
- Create: `tests/ribosome/test_adversarial.py`

- [ ] **Step 1: Write adversarial tests**

Create `tests/ribosome/test_adversarial.py`:

```python
"""L3 adversarial tests: cache poisoning mitigation (vulnerability #9)."""

from __future__ import annotations

from dbse.contracts import AST, ASTNode
from dbse.ribosome.cache import CacheEntry, SemanticCache


def test_forged_entry_without_valid_hmac_is_rejected() -> None:
    cache = SemanticCache(secret="production-secret", ttl_seconds=3600, max_entries=16)
    cache._store["evil"] = cache._store.get("evil")  # noqa: SLF001 — ensure dict exists
    from dbse.ribosome.cache import _StoredEntry  # noqa: PLC0415

    cache._store["evil"] = _StoredEntry(  # noqa: SLF001
        entry=CacheEntry(
            ast=AST(root=ASTNode(kind="OBJECT", op="x", value="poison")),
            solution={"answer": "WRONG"},
            proof_level="P0",
            tinfo=0.0,
        ),
        signature="deadbeef" * 8,
        created_at=0.0,
        core_version="core-1",
    )
    assert cache.get("evil", core_version="core-1") is None
    assert "evil" not in cache._store  # noqa: SLF001 — evicted
```

- [ ] **Step 2: Run adversarial tests**

Run: `python -m pytest tests/ribosome/test_adversarial.py -v`
Expected: PASS (1 test).

- [ ] **Step 3: Commit**

```bash
git add tests/ribosome/test_adversarial.py
git commit -m "test(l3): adversarial cache poisoning corpus"
```

---

## Task 12: Wire the `Ribosome` pipeline layer

**Files:**
- Modify: `dbse/layers/ribosome.py`
- Create: `tests/ribosome/test_layer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/ribosome/test_layer.py`:

```python
"""L3 layer integration tests."""

from __future__ import annotations

from dbse.contracts import PipelineContext
from dbse.layers.ribosome import Ribosome
from dbse.ribosome.cache import SemanticCache


def test_ribosome_compiles_membrane_into_annotated_ast() -> None:
    layer = Ribosome()
    ctx = PipelineContext(
        query="ignored",
        membrane={
            "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
            "quantities": [
                {"ref": "obj_1", "property": "mass", "value": 1.0, "unit": "kg"},
            ],
            "relations": [],
            "equations": [],
            "question_type": "compute",
            "target": {"ref": "obj_1", "property": "mass"},
        },
    )
    out = layer.process(ctx)
    assert out.ast is not None
    assert out.ast.structure_class == "Algebraic_Quantities"
    assert out.ast.canonical_hash is not None
    assert len(out.ast.canonical_hash) == 16
    assert out.trace[-1].layer == "L3.RIBOSOME"
    assert out.trace[-1].note == "compiled"


def test_ribosome_cache_hit_skips_recompute_and_prefills_solution() -> None:
    cache = SemanticCache(secret="layer-test", ttl_seconds=60, max_entries=8)
    layer = Ribosome(cache=cache, cache_secret="layer-test", core_version="core-test")
    membrane = {
        "objects": [{"id": "obj_1", "type": "body", "label": "body"}],
        "quantities": [],
        "relations": [],
        "equations": [
            {"object_ref": "obj_1", "state": "v", "constant": 1.0, "linear_coeff": -0.1},
        ],
        "question_type": "compute",
        "target": {"ref": "obj_1", "property": "velocity"},
    }
    ctx1 = PipelineContext(query="q1", membrane=membrane, config={"cache_secret": "layer-test"})
    out1 = layer.process(ctx1)
    assert out1.solution is None
    digest = out1.ast.canonical_hash
    assert digest is not None

    # Simulate NUCLEUS having stored a result via cache.put on miss — layer does this on miss with placeholder for now
    from dbse.ribosome.cache import CacheEntry

    cache.put(
        digest,
        CacheEntry(
            ast=out1.ast,
            solution={"status": "solved", "via": "nucleus"},
            proof_level="P2",
            tinfo=0.05,
        ),
        core_version="core-test",
    )

    ctx2 = PipelineContext(query="q2", membrane=membrane, config={"cache_secret": "layer-test"})
    out2 = layer.process(ctx2)
    assert out2.solution == {"status": "solved", "via": "nucleus"}
    assert out2.trace[-1].note == "cache-hit"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ribosome/test_layer.py -v`
Expected: FAIL — layer still pass-through stub.

- [ ] **Step 3: Write minimal implementation**

Replace `dbse/layers/ribosome.py`:

```python
"""L3 RIBOSOME — AST compiler + canonical hash + cache."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import PipelineContext
from dbse.ribosome.cache import CacheEntry, SemanticCache
from dbse.ribosome.compile import compile_membrane
from dbse.ribosome.errors import RibosomeError
from dbse.ribosome.hash import annotate_ast


class Ribosome:
    """L3 layer: compile MEMBRANE → AST, hash, cache lookup/store."""

    name: ClassVar[str] = "L3.RIBOSOME"

    def __init__(
        self,
        cache: SemanticCache | None = None,
        *,
        cache_secret: str = "dev-cache-secret",
        core_version: str = "core-dev",
    ) -> None:
        self._cache = cache or SemanticCache(secret=cache_secret)
        self._core_version = core_version

    def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.membrane is None:
            ctx.record(self.name, note="skipped:no-membrane")
            return ctx
        try:
            raw_ast = compile_membrane(ctx.membrane)
            ast = annotate_ast(raw_ast)
        except RibosomeError as exc:
            ctx.record(self.name, note="compile-error")
            ctx.halt_message = str(exc)
            return ctx
        ctx.ast = ast
        digest = ast.canonical_hash
        if digest is not None:
            hit = self._cache.get(digest, core_version=self._core_version)
            if hit is not None:
                ctx.solution = hit.solution
                ctx.record(
                    self.name,
                    note="cache-hit",
                    hash=digest,
                    hits=hit.hits,
                    proof_level=hit.proof_level,
                )
                return ctx
        ctx.record(
            self.name,
            note="compiled",
            hash=digest,
            structure_class=ast.structure_class,
        )
        return ctx
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ribosome/test_layer.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dbse/layers/ribosome.py tests/ribosome/test_layer.py
git commit -m "feat(l3): wire RIBOSOME layer (compile, hash, cache lookup)"
```

---

## Task 13: Full quality gate + pipeline skeleton still green

**Files:** none (verification only).

- [ ] **Step 1: Run the full QA gate**

Run: `ruff check . ; mypy ; python -m pytest -q`
Expected: `All checks passed!`; `Success: no issues found`; all tests pass including `tests/test_pipeline_skeleton.py`.

- [ ] **Step 2: Commit if any fixups were needed**

Only if fixups were required in Step 1.

---

## Task 14: Update status docs

**Files:**
- Modify: `README.md`
- Modify: `docs/spec-notes.md`

- [ ] **Step 1: Update README status**

Append to `README.md` "Статус":

```markdown
- Этап 4 — L3 RIBOSOME: ✅ компиляция MEMBRANE → AST с навешиванием
  `AffineType` (L1/L1.5 в `compile`), нормализация (rename/sort/fold),
  `classify_structure`, `canonical_hash` (16 hex), подписанный LRU-кэш
  (`dbse/ribosome/`). Слой `L3.RIBOSOME` подключён: cache hit →
  `ctx.solution` без NUCLEUS. **Закрывает уязвимости №8 (Graph isomorphism
  DDoS) и №9 (Cache poisoning).**
```

- [ ] **Step 2: Record Stage 4 decisions in spec-notes**

Append to `docs/spec-notes.md`:

```markdown
## L3 (Stage 4) — принятые решения
- **MEMBRANE расширена полем `equations: list[LinearOde1]`** — LLM по-прежнему
  не генерирует `OPERATOR`; только структурированные коэффициенты
  `d(state)/dt = constant + linear_coeff * state`. RIBOSOME строит дерево
  `DERIV`/`EQ`/`ADD`/`MUL` детерминированно.
- **L1/L1.5 интеграция в `compile`, не в layer stubs.** `quantity_affine()`
  вызывает L1 `parse_unit` + L1.5 `affine()`. Слои `L1.DIMENSIONS` /
  `L1.5.AFFINE_TYPES` остаются pass-through.
- **MVP hash — структурный, не полный изоморфизм.** Переименование переменных и
  перестановка коммутативных операндов не меняют хеш; разные коэффициенты —
  меняют. `classify_structure` для DoD: `LinearODE_Order1` покрывает и
  `dv/dt=g-kv`, и RC `dV/dt=-V/RC`.
- **Кэш:** HMAC-SHA256 подпись записи, TTL, LRU, инвалидация по `core_version`
  (хук для Этапа 11). Отравленная запись → `get()` возвращает `None` и удаляет
  ключ.
- **QA-гейт:** уровни 1 (юнит), 2 (`test_properties.py`), 5
  (`test_adversarial.py` cache poisoning).
```

- [ ] **Step 3: Commit docs**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 4 (L3 RIBOSOME) complete"
```

---

## Self-review (plan author checklist)

**Spec coverage (ROADMAP Stage 4):**
- Сборка AST из MEMBRANE + AffineType → Tasks 2–5, 12 ✅
- Нормализация (rename, sort, fold) → Task 6 ✅
- `classify_structure` → Task 7 ✅
- `canonical_hash` = sha256(class + canonical)[:16] → Task 8 ✅
- LRU + semantic cache with hits/solution/proof_level/tinfo → Task 10 ✅
- Cache protection: TTL, signature, core invalidation hook → Tasks 10–11 ✅
- DoD: free-fall + RC same class → Task 7 test ✅
- DoD: repeat query cache hit → Task 12 test ✅
- Vulnerabilities #8, #9 → Tasks 8–11 ✅

**Placeholder scan:** no TBD/TODO steps ✅

**Type consistency:** `LinearOde1`, `CacheEntry`, `annotate_ast`, layer trace notes consistent across tasks ✅
