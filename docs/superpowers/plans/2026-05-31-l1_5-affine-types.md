# L1.5 Affine Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the L1.5 toolkit that augments bare `Dimension`s with semantic meaning (`AffineType`) and decides when two semantic types may combine — so that `Energy + Torque` is rejected (same dimension, different semantics) while `Work + Heat → InternalEnergy` is accepted. This closes vulnerability #1 (Semantic Mismatch).

**Architecture:** A new focused package `dbse/semantic/` with five small modules — `errors` (`SemanticTypeError`), `operators` (the `Operator` enum), `tags` (registry of physical semantic tags → dimension + tensor rank, plus a factory and the tag-combination rule tables), and `compatibility` (the `compatible()` predicate, the raising `check_compatible()`, and `combine()` for `×/÷`). **Critical layering rule (from final review):** the L1 functions `dbse.dimensional.check_add`/`check_subtract` remain the single source of *dimensional* pruning; L1.5 `compatibility` calls them for the dimension gate and only *adds* the semantic-tag / tensor-rank checks on top — it never re-implements `a.dimension == b.dimension`. The pipeline layer `dbse/layers/affine_types.py` stays a pass-through stub until L0 (Stage 3) produces quantities to feed it, exactly as `dbse/layers/dimensional.py` did in Stage 1; this stage builds and tests the reusable primitives only.

**Tech Stack:** Python 3.11+, stdlib only at runtime (`dataclasses`, `enum`), `pytest` + `hypothesis` for tests. Reuses `dbse.contracts.affine.AffineType`, `dbse.contracts.dimensions.Dimension`, and `dbse.dimensional.{check_add, check_subtract, DimensionError}`.

---

## Environment notes (read once)

- Activate the venv first, or prefix commands: PowerShell `.\.venv\Scripts\Activate.ps1`.
- All test commands below use `python -m pytest ...`. Run from repo root `c:\Users\Clerikozoid\Desktop\Chromosome`.
- Quality gate for every commit: `ruff check . ; mypy ; python -m pytest`.
- The shell is PowerShell: chain commands with `;`, not `&&`.

## Layering contract (the central design constraint — read before Task 3)

L1 (`dbse/dimensional/checks.py`) owns the **dimensional** gate:

```text
check_add(left, right)      -> raises DimensionError if dimensions differ
check_subtract(left, right) -> raises DimensionError if dimensions differ
```

L1.5 (`dbse/semantic/compatibility.py`) owns the **semantic** gate, *stacked on top*:

```text
check_compatible(a, b, ADD):
    1. check_add(a.dimension, b.dimension)   # REUSE L1 — do not re-implement
    2. then compare semantic_tag + tensor_rank (and allow whitelisted fusions)
```

Consequences (these are intentional and tested):
- `J + N` (unlike dimension) fails at step 1 with **`DimensionError`** (an L1 concern).
- `Energy + Torque` (same dimension, different tag/rank) passes step 1, fails step 2 with **`SemanticTypeError`** (an L1.5 concern).
- `Work + Heat` (same dimension, different tag, whitelisted) passes both → `InternalEnergy`.

`compatible(a, b, op) -> bool` is derived from `check_compatible` (it swallows both error types) so there is exactly one place where each rule lives.

## File Structure

- Create `dbse/semantic/__init__.py` — public exports.
- Create `dbse/semantic/errors.py` — `SemanticTypeError`.
- Create `dbse/semantic/operators.py` — `Operator` enum (`ADD, SUBTRACT, MULTIPLY, DIVIDE, DOT, CROSS`).
- Create `dbse/semantic/tags.py` — `TagSpec`, `_TAGS` registry, `affine()` factory, ambiguity helpers, `ADDITIVE_FUSIONS`, `MULTIPLICATIVE_FUSIONS`, `DIVISIVE_FUSIONS`.
- Create `dbse/semantic/compatibility.py` — `compatible`, `check_compatible`, `combine`, private `_check_additive/_check_dot/_check_cross`.
- Create `tests/semantic/test_tags.py` — registry, factory, ambiguity helpers.
- Create `tests/semantic/test_compatibility.py` — ADD/SUB/DOT/CROSS/×÷ rules, the Energy+Torque error, the Work+Heat fusion, suggestion text.
- Create `tests/semantic/test_properties.py` — property-based laws (reflexivity/symmetry — QA level 2).
- Create `tests/semantic/test_adversarial.py` — semantic-collision corpus (QA level 5).

---

## Task 0: Baseline is green

**Files:** none (verification only).

- [ ] **Step 1: Confirm Stage 1 is committed and the suite is green**

Run: `git log --oneline -3 ; ruff check . ; mypy ; python -m pytest -q`
Expected: recent commits include the L1 work (`test(l1): ...`, `docs: mark Stage 1 ... complete`); `All checks passed!`; `Success: no issues found`; all tests pass.

> No commit in this task — Stage 1 is already committed. This is a smoke check before starting Stage 2.

---

## Task 1: `SemanticTypeError`, `Operator`, and package skeleton

**Files:**
- Create: `dbse/semantic/errors.py`
- Create: `dbse/semantic/operators.py`
- Create: `dbse/semantic/__init__.py`
- Test: `tests/semantic/test_compatibility.py`

- [ ] **Step 1: Write the failing test**

Create `tests/semantic/test_compatibility.py`:

```python
"""L1.5 unit tests: semantic compatibility rules and SemanticTypeError."""

from __future__ import annotations

import pytest

from dbse.semantic import Operator, SemanticTypeError


def test_semantic_type_error_is_a_type_error() -> None:
    assert issubclass(SemanticTypeError, TypeError)
    with pytest.raises(SemanticTypeError):
        raise SemanticTypeError("boom")


def test_operator_has_the_six_kinds() -> None:
    names = {op.name for op in Operator}
    assert names == {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "DOT", "CROSS"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/semantic/test_compatibility.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.semantic'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/semantic/errors.py`:

```python
"""L1.5 error type."""

from __future__ import annotations


class SemanticTypeError(TypeError):
    """Raised when two affine types are semantically incompatible (L1.5).

    Distinct from :class:`dbse.dimensional.DimensionError`: a ``SemanticTypeError``
    means the *dimensions matched* but the *semantics* did not — e.g. adding
    ``Energy`` to ``Torque``. Subclasses :class:`TypeError` per the v5.0 spec
    ("Semantic mismatch at L1.5").
    """
```

Create `dbse/semantic/operators.py`:

```python
"""L1.5 operators over affine types.

A tiny enum shared by the compatibility checker now and by the L3 AST compiler
(Stage 4) later. Kept separate from the rules so both can import it without a
cycle.
"""

from __future__ import annotations

from enum import Enum


class Operator(Enum):
    """Binary operators whose semantic legality L1.5 decides."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    DOT = "dot"
    CROSS = "cross"
```

Create `dbse/semantic/__init__.py`:

```python
"""L1.5 AFFINE TYPES — semantic type checking on top of L1 dimensions."""

from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator

__all__ = ["Operator", "SemanticTypeError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_compatibility.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/semantic/__init__.py dbse/semantic/errors.py dbse/semantic/operators.py tests/semantic/test_compatibility.py
git commit -m "feat(l1.5): add SemanticTypeError and Operator enum"
```

---

## Task 2: Semantic-tag registry, `affine()` factory, ambiguity helpers

**Files:**
- Create: `dbse/semantic/tags.py`
- Modify: `dbse/semantic/__init__.py`
- Test: `tests/semantic/test_tags.py`

- [ ] **Step 1: Write the failing test**

Create `tests/semantic/test_tags.py`:

```python
"""L1.5 unit tests: the semantic-tag registry and helpers."""

from __future__ import annotations

import pytest

from dbse.contracts.affine import AffineType
from dbse.contracts.dimensions import Dimension
from dbse.semantic import SemanticTypeError, affine, ambiguous_tag, is_ambiguous

_ENERGY_DIM = Dimension.of(1, 2, -2)
_FORCE_DIM = Dimension.of(1, 1, -2)


def test_affine_builds_energy_from_registry() -> None:
    energy = affine("Energy")
    assert energy == AffineType(_ENERGY_DIM, "Energy", tensor_rank=0)


def test_affine_marks_torque_as_rank_one_pseudovector() -> None:
    torque = affine("Torque")
    assert torque.dimension == _ENERGY_DIM
    assert torque.semantic_tag == "Torque"
    assert torque.tensor_rank == 1


def test_affine_marks_force_as_rank_one() -> None:
    force = affine("Force")
    assert force == AffineType(_FORCE_DIM, "Force", tensor_rank=1)


def test_affine_carries_frame_of_reference() -> None:
    v = affine("Velocity", frame="lab")
    assert v.frame_of_reference == "lab"


def test_affine_unknown_tag_raises() -> None:
    with pytest.raises(SemanticTypeError):
        affine("Zorp")


def test_energy_and_torque_share_dimension_but_differ() -> None:
    # The whole reason L1.5 exists.
    assert affine("Energy").dimension == affine("Torque").dimension
    assert affine("Energy") != affine("Torque")


def test_ambiguous_tag_is_sorted_and_pipe_joined() -> None:
    assert ambiguous_tag("Work", "Torque") == "Torque|Work"
    assert ambiguous_tag("Torque", "Work") == "Torque|Work"  # order-independent


def test_is_ambiguous_detects_the_pipe() -> None:
    assert is_ambiguous("Torque|Work")
    assert not is_ambiguous("Energy")


def test_registry_has_at_least_ten_tags() -> None:
    from dbse.semantic.tags import _TAGS

    assert len(_TAGS) >= 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/semantic/test_tags.py -v`
Expected: FAIL — `ImportError: cannot import name 'affine' from 'dbse.semantic'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/semantic/tags.py`:

```python
"""L1.5 semantic-tag registry and tag-combination rules.

A *semantic tag* names the physical meaning of a quantity that a bare dimension
cannot distinguish (``Energy`` vs ``Torque`` both being ``[M L^2 T^-2]``). The
registry maps each known tag to its dimension and default tensor rank, and the
fusion tables encode how tags combine under ``+``/``-`` and ``×``/``÷``.

Ambiguity (e.g. ``Force × Length`` could be ``Work`` *or* ``Torque``) is encoded
directly in the ``semantic_tag`` string as a sorted, pipe-joined value
(``"Torque|Work"``) because :class:`~dbse.contracts.affine.AffineType` is a frozen
contract with a ``str`` tag field — L2 (Stage 8) resolves the ambiguity later.
"""

from __future__ import annotations

from dataclasses import dataclass

from dbse.contracts.affine import AffineType
from dbse.contracts.dimensions import Dimension
from dbse.semantic.errors import SemanticTypeError

_AMBIGUOUS_SEP = "|"


@dataclass(frozen=True, slots=True)
class TagSpec:
    """The dimension and default tensor rank of a known semantic tag."""

    dimension: Dimension
    tensor_rank: int = 0


# Known physical semantic tags. Many share a dimension on purpose.
_TAGS: dict[str, TagSpec] = {
    # [M L^2 T^-2] — the energy/torque collision family.
    "Energy": TagSpec(Dimension.of(1, 2, -2), 0),
    "Work": TagSpec(Dimension.of(1, 2, -2), 0),
    "Heat": TagSpec(Dimension.of(1, 2, -2), 0),
    "InternalEnergy": TagSpec(Dimension.of(1, 2, -2), 0),
    "Torque": TagSpec(Dimension.of(1, 2, -2), 1),  # pseudovector
    # mechanical
    "Force": TagSpec(Dimension.of(1, 1, -2), 1),
    "Momentum": TagSpec(Dimension.of(1, 1, -1), 1),
    "Power": TagSpec(Dimension.of(1, 2, -3), 0),
    "Velocity": TagSpec(Dimension.of(0, 1, -1), 1),
    "Length": TagSpec(Dimension.of(0, 1), 0),
    "Mass": TagSpec(Dimension.of(1), 0),
    "Time": TagSpec(Dimension.of(0, 0, 1), 0),
}

# Whitelisted additive fusions: unlike tags (same dimension) that MAY be added,
# producing a named result. Keyed by an unordered pair of tags.
ADDITIVE_FUSIONS: dict[frozenset[str], str] = {
    frozenset({"Work", "Heat"}): "InternalEnergy",
}

# Tag results of multiplication, keyed by an unordered pair. A tuple of length
# > 1 means the result is ambiguous (flagged for L2).
MULTIPLICATIVE_FUSIONS: dict[frozenset[str], tuple[str, ...]] = {
    frozenset({"Force", "Length"}): ("Torque", "Work"),
    frozenset({"Force", "Velocity"}): ("Power",),
    frozenset({"Mass", "Velocity"}): ("Momentum",),
}

# Tag results of division. Division is NOT commutative for tags, so the key is an
# ordered ``(numerator, denominator)`` pair.
DIVISIVE_FUSIONS: dict[tuple[str, str], str] = {
    ("Energy", "Time"): "Power",
    ("Work", "Time"): "Power",
    ("Momentum", "Time"): "Force",
}


def affine(tag: str, *, frame: str | None = None) -> AffineType:
    """Build an :class:`AffineType` for a known semantic tag from the registry."""
    spec = _TAGS.get(tag)
    if spec is None:
        raise SemanticTypeError(f"Unknown semantic tag: {tag!r}")
    return AffineType(spec.dimension, tag, spec.tensor_rank, frame)


def ambiguous_tag(*tags: str) -> str:
    """Encode an ambiguous result as a sorted, pipe-joined tag string."""
    return _AMBIGUOUS_SEP.join(sorted(set(tags)))


def is_ambiguous(tag: str) -> bool:
    """True if ``tag`` encodes more than one candidate semantic tag."""
    return _AMBIGUOUS_SEP in tag
```

Modify `dbse/semantic/__init__.py`:

```python
"""L1.5 AFFINE TYPES — semantic type checking on top of L1 dimensions."""

from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import affine, ambiguous_tag, is_ambiguous

__all__ = [
    "Operator",
    "SemanticTypeError",
    "affine",
    "ambiguous_tag",
    "is_ambiguous",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_tags.py -v`
Expected: PASS (9 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/semantic/tags.py dbse/semantic/__init__.py tests/semantic/test_tags.py
git commit -m "feat(l1.5): semantic-tag registry, affine() factory, ambiguity helpers"
```

---

## Task 3: Additive compatibility (`ADD`/`SUB`) stacked on L1 pruning

> This is the task that implements the central layering rule. The dimensional
> gate is delegated to `check_add`/`check_subtract`; only the semantic checks
> (tag + rank, plus whitelisted fusions) are added here.

**Files:**
- Create: `dbse/semantic/compatibility.py`
- Modify: `dbse/semantic/__init__.py`
- Test: `tests/semantic/test_compatibility.py` (append)

- [ ] **Step 1: Write the failing test (append to existing file)**

Append to `tests/semantic/test_compatibility.py`:

```python
from dbse.contracts.dimensions import Dimension
from dbse.dimensional import DimensionError
from dbse.semantic import affine, check_compatible, compatible


def test_add_same_tag_is_compatible_and_returns_that_type() -> None:
    result = check_compatible(affine("Energy"), affine("Energy"), Operator.ADD)
    assert result == affine("Energy")
    assert compatible(affine("Energy"), affine("Energy"), Operator.ADD)


def test_add_energy_and_torque_raises_semantic_type_error() -> None:
    # Same dimension, different tag AND rank -> the L1.5 collision.
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
    assert not compatible(affine("Energy"), affine("Torque"), Operator.ADD)


def test_add_error_message_mentions_operands_and_suggestion() -> None:
    with pytest.raises(SemanticTypeError) as excinfo:
        check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
    message = str(excinfo.value)
    assert "Energy" in message
    assert "Torque" in message
    assert "ADD" in message
    # Suggestion advertises the known fusion.
    assert "Work" in message and "Heat" in message


def test_add_work_and_heat_fuses_to_internal_energy() -> None:
    result = check_compatible(affine("Work"), affine("Heat"), Operator.ADD)
    assert result == affine("InternalEnergy")
    assert compatible(affine("Work"), affine("Heat"), Operator.ADD)


def test_add_unlike_dimension_raises_dimension_error_not_semantic() -> None:
    # J + N differ in dimension: the L1 gate must fire first (DimensionError),
    # NOT a SemanticTypeError. This proves L1.5 reuses L1 pruning.
    joule = affine("Energy")           # [M L^2 T^-2]
    newton = affine("Force")           # [M L T^-2]
    with pytest.raises(DimensionError):
        check_compatible(joule, newton, Operator.ADD)
    assert not compatible(joule, newton, Operator.ADD)


def test_subtract_follows_the_same_rules() -> None:
    assert compatible(affine("Energy"), affine("Energy"), Operator.SUBTRACT)
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Energy"), affine("Torque"), Operator.SUBTRACT)


def test_add_same_dimension_same_tag_different_rank_is_rejected() -> None:
    # Construct two "Energy"-tagged values that disagree on rank.
    scalar = affine("Energy")
    pseudo = AffineType(Dimension.of(1, 2, -2), "Energy", tensor_rank=1)
    with pytest.raises(SemanticTypeError):
        check_compatible(scalar, pseudo, Operator.ADD)
```

(Add `from dbse.contracts.affine import AffineType` to the imports at the top of the file if not already present.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/semantic/test_compatibility.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_compatible' from 'dbse.semantic'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/semantic/compatibility.py`:

```python
"""L1.5 semantic compatibility — stacked on top of L1 dimensional pruning.

The L1 functions ``check_add`` / ``check_subtract`` remain the single source of
*dimensional* truth. This module reuses them for the dimension gate and adds the
*semantic* layer (tag + tensor rank, plus whitelisted fusions) on top. It never
re-implements ``a.dimension == b.dimension``.
"""

from __future__ import annotations

from dbse.contracts.affine import AffineType
from dbse.dimensional import DimensionError, check_add, check_subtract
from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import ADDITIVE_FUSIONS, _TAGS


def compatible(a: AffineType, b: AffineType, op: Operator) -> bool:
    """Predicate form of :func:`check_compatible` (swallows both error types)."""
    try:
        check_compatible(a, b, op)
    except (DimensionError, SemanticTypeError):
        return False
    return True


def check_compatible(a: AffineType, b: AffineType, op: Operator) -> AffineType:
    """Validate ``a op b`` and return the resulting :class:`AffineType`.

    Raises :class:`~dbse.dimensional.DimensionError` if the *dimensions* are
    incompatible (the L1 gate), or :class:`SemanticTypeError` if the dimensions
    match but the *semantics* do not (the L1.5 gate). For ``×``/``÷`` the result
    is always defined (see :func:`combine`).
    """
    if op in (Operator.ADD, Operator.SUBTRACT):
        return _check_additive(a, b, op)
    if op in (Operator.MULTIPLY, Operator.DIVIDE):
        return combine(a, b, op)
    raise SemanticTypeError(f"Unsupported operator: {op!r}")


def _check_additive(a: AffineType, b: AffineType, op: Operator) -> AffineType:
    # Step 1: L1 dimensional pruning (REUSED, not duplicated).
    dim_gate = check_add if op is Operator.ADD else check_subtract
    dim_gate(a.dimension, b.dimension)  # raises DimensionError on mismatch

    # Step 2: L1.5 semantic layer on top.
    if a.semantic_tag == b.semantic_tag and a.tensor_rank == b.tensor_rank:
        return AffineType(a.dimension, a.semantic_tag, a.tensor_rank, a.frame_of_reference)

    fused = ADDITIVE_FUSIONS.get(frozenset({a.semantic_tag, b.semantic_tag}))
    if fused is not None and a.tensor_rank == b.tensor_rank:
        spec = _TAGS[fused]
        return AffineType(a.dimension, fused, spec.tensor_rank, a.frame_of_reference)

    raise SemanticTypeError(_mismatch_message(a, b, op))


def _additive_suggestion() -> str:
    examples = [
        f"{' + '.join(sorted(pair))} -> {result}"
        for pair, result in ADDITIVE_FUSIONS.items()
    ]
    return "Did you mean: " + "; ".join(examples) + "?"


def _mismatch_message(a: AffineType, b: AffineType, op: Operator) -> str:
    return (
        "Semantic mismatch at L1.5\n"
        f"  Left:  {a}\n"
        f"  Right: {b}\n"
        f"  Operation: {op.name}\n"
        f"  Suggestion: {_additive_suggestion()}"
    )
```

> Note: `combine` is referenced by `check_compatible` for `×`/`÷` but is added in
> Task 5. Until then the `MULTIPLY`/`DIVIDE` branch will raise `NameError` if
> exercised — Task 3 tests only touch `ADD`/`SUBTRACT`, so this is fine. Task 4
> adds `DOT`/`CROSS`; Task 5 adds `combine`.

Modify `dbse/semantic/__init__.py`:

```python
"""L1.5 AFFINE TYPES — semantic type checking on top of L1 dimensions."""

from dbse.semantic.compatibility import check_compatible, compatible
from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import affine, ambiguous_tag, is_ambiguous

__all__ = [
    "Operator",
    "SemanticTypeError",
    "affine",
    "ambiguous_tag",
    "check_compatible",
    "compatible",
    "is_ambiguous",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_compatibility.py -v`
Expected: PASS (2 from Task 1 + 7 = 9 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/semantic/compatibility.py dbse/semantic/__init__.py tests/semantic/test_compatibility.py
git commit -m "feat(l1.5): additive compatibility stacked on L1 dimensional pruning"
```

---

## Task 4: `DOT` and `CROSS` compatibility

**Files:**
- Modify: `dbse/semantic/compatibility.py`
- Test: `tests/semantic/test_compatibility.py` (append)

- [ ] **Step 1: Write the failing test (append to existing file)**

Append to `tests/semantic/test_compatibility.py`:

```python
def test_dot_requires_two_rank_one_equal_dimension_vectors() -> None:
    v = affine("Velocity")  # rank 1
    result = check_compatible(v, v, Operator.DOT)
    assert result.tensor_rank == 0                      # dot of vectors -> scalar
    assert result.dimension == Dimension.of(0, 2, -2)   # velocity^2
    assert compatible(v, v, Operator.DOT)


def test_dot_rejects_a_scalar_operand() -> None:
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Energy"), affine("Velocity"), Operator.DOT)


def test_dot_rejects_unequal_dimension_vectors() -> None:
    assert not compatible(affine("Velocity"), affine("Force"), Operator.DOT)


def test_cross_requires_two_polar_vectors() -> None:
    p = AffineType(Dimension.of(0, 1), "PolarVector", tensor_rank=1)
    result = check_compatible(p, p, Operator.CROSS)
    assert result.tensor_rank == 1                 # cross -> (pseudo)vector
    assert result.semantic_tag == "AxialVector"
    assert compatible(p, p, Operator.CROSS)


def test_cross_rejects_non_polar_vectors() -> None:
    with pytest.raises(SemanticTypeError):
        check_compatible(affine("Velocity"), affine("Velocity"), Operator.CROSS)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/semantic/test_compatibility.py -k "dot or cross" -v`
Expected: FAIL — `SemanticTypeError: Unsupported operator: <Operator.DOT: 'dot'>` (the dispatch does not yet handle `DOT`/`CROSS`).

- [ ] **Step 3: Write minimal implementation**

In `dbse/semantic/compatibility.py`, extend the dispatch in `check_compatible` to route `DOT` and `CROSS`. Replace the body of `check_compatible` with:

```python
def check_compatible(a: AffineType, b: AffineType, op: Operator) -> AffineType:
    """Validate ``a op b`` and return the resulting :class:`AffineType`.

    Raises :class:`~dbse.dimensional.DimensionError` if the *dimensions* are
    incompatible (the L1 gate), or :class:`SemanticTypeError` if the dimensions
    match but the *semantics* do not (the L1.5 gate). For ``×``/``÷`` the result
    is always defined (see :func:`combine`).
    """
    if op in (Operator.ADD, Operator.SUBTRACT):
        return _check_additive(a, b, op)
    if op is Operator.DOT:
        return _check_dot(a, b)
    if op is Operator.CROSS:
        return _check_cross(a, b)
    if op in (Operator.MULTIPLY, Operator.DIVIDE):
        return combine(a, b, op)
    raise SemanticTypeError(f"Unsupported operator: {op!r}")
```

Add these two helpers to `dbse/semantic/compatibility.py` (e.g. after `_check_additive`):

```python
def _check_dot(a: AffineType, b: AffineType) -> AffineType:
    if a.tensor_rank == 1 and b.tensor_rank == 1 and a.dimension == b.dimension:
        return AffineType(a.dimension * b.dimension, "Scalar", tensor_rank=0)
    raise SemanticTypeError(
        "Semantic mismatch at L1.5\n"
        f"  Left:  {a}\n"
        f"  Right: {b}\n"
        "  Operation: DOT\n"
        "  Suggestion: DOT requires two rank-1 vectors of equal dimension."
    )


def _check_cross(a: AffineType, b: AffineType) -> AffineType:
    if a.semantic_tag == b.semantic_tag == "PolarVector":
        return AffineType(a.dimension * b.dimension, "AxialVector", tensor_rank=1)
    raise SemanticTypeError(
        "Semantic mismatch at L1.5\n"
        f"  Left:  {a}\n"
        f"  Right: {b}\n"
        "  Operation: CROSS\n"
        "  Suggestion: CROSS requires two PolarVector operands."
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_compatibility.py -v`
Expected: PASS (9 from Tasks 1+3 + 5 = 14 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/semantic/compatibility.py tests/semantic/test_compatibility.py
git commit -m "feat(l1.5): DOT and CROSS compatibility rules"
```

---

## Task 5: `combine()` for `×`/`÷` (tag combination + ambiguity flag)

**Files:**
- Modify: `dbse/semantic/compatibility.py`
- Modify: `dbse/semantic/__init__.py`
- Test: `tests/semantic/test_compatibility.py` (append)

- [ ] **Step 1: Write the failing test (append to existing file)**

Append to `tests/semantic/test_compatibility.py`:

```python
from dbse.semantic import combine, is_ambiguous


def test_multiply_unambiguous_tag_force_times_velocity_is_power() -> None:
    result = combine(affine("Force"), affine("Velocity"), Operator.MULTIPLY)
    assert result.dimension == Dimension.of(1, 2, -3)   # power dimension
    assert result.semantic_tag == "Power"
    assert not is_ambiguous(result.semantic_tag)


def test_multiply_force_times_length_is_ambiguous_work_or_torque() -> None:
    result = combine(affine("Force"), affine("Length"), Operator.MULTIPLY)
    assert result.dimension == Dimension.of(1, 2, -2)
    assert is_ambiguous(result.semantic_tag)
    assert set(result.semantic_tag.split("|")) == {"Torque", "Work"}


def test_multiply_is_commutative_for_dimension_and_tag() -> None:
    ab = combine(affine("Force"), affine("Length"), Operator.MULTIPLY)
    ba = combine(affine("Length"), affine("Force"), Operator.MULTIPLY)
    assert ab.dimension == ba.dimension
    assert ab.semantic_tag == ba.semantic_tag


def test_multiply_or_divide_is_always_compatible() -> None:
    # Per the v5.0 spec, ×/÷ never fail the semantic gate.
    assert compatible(affine("Energy"), affine("Torque"), Operator.MULTIPLY)
    assert compatible(affine("Energy"), affine("Torque"), Operator.DIVIDE)


def test_divide_energy_by_time_is_power() -> None:
    result = combine(affine("Energy"), affine("Time"), Operator.DIVIDE)
    assert result.dimension == Dimension.of(1, 2, -3)
    assert result.semantic_tag == "Power"


def test_unknown_product_yields_unknown_tag() -> None:
    result = combine(affine("Heat"), affine("Length"), Operator.MULTIPLY)
    assert result.semantic_tag == "Unknown"
    assert result.dimension == Dimension.of(1, 3, -2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/semantic/test_compatibility.py -k "multiply or divide or unknown_product" -v`
Expected: FAIL — `ImportError: cannot import name 'combine' from 'dbse.semantic'`.

- [ ] **Step 3: Write minimal implementation**

Add to the imports at the top of `dbse/semantic/compatibility.py`:

```python
from dbse.semantic.tags import (
    ADDITIVE_FUSIONS,
    DIVISIVE_FUSIONS,
    MULTIPLICATIVE_FUSIONS,
    _TAGS,
    ambiguous_tag,
)
```

(Replace the existing `from dbse.semantic.tags import ADDITIVE_FUSIONS, _TAGS` line with the block above.)

Add the `combine` function to `dbse/semantic/compatibility.py`:

```python
def combine(a: AffineType, b: AffineType, op: Operator) -> AffineType:
    """Result type of ``a × b`` or ``a ÷ b``.

    ``×``/``÷`` are always dimensionally and semantically legal; this computes the
    resulting dimension and best-effort semantic tag. An ambiguous product (e.g.
    ``Force × Length`` → ``Work`` *or* ``Torque``) yields a pipe-joined tag flagged
    for L2 to resolve; an unknown combination yields ``"Unknown"``.
    """
    if op is Operator.MULTIPLY:
        dimension = a.dimension * b.dimension
        candidates = MULTIPLICATIVE_FUSIONS.get(
            frozenset({a.semantic_tag, b.semantic_tag}), ()
        )
    elif op is Operator.DIVIDE:
        dimension = a.dimension / b.dimension
        divided = DIVISIVE_FUSIONS.get((a.semantic_tag, b.semantic_tag))
        candidates = (divided,) if divided is not None else ()
    else:  # pragma: no cover - guarded by check_compatible dispatch
        raise SemanticTypeError(f"combine() does not handle {op!r}")

    if len(candidates) == 1:
        tag = candidates[0]
    elif len(candidates) > 1:
        tag = ambiguous_tag(*candidates)
    else:
        tag = "Unknown"

    if a.tensor_rank and b.tensor_rank:
        rank = 0
    else:
        rank = a.tensor_rank + b.tensor_rank

    return AffineType(dimension, tag, rank)
```

Modify `dbse/semantic/__init__.py` to export `combine`:

```python
"""L1.5 AFFINE TYPES — semantic type checking on top of L1 dimensions."""

from dbse.semantic.compatibility import check_compatible, combine, compatible
from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import affine, ambiguous_tag, is_ambiguous

__all__ = [
    "Operator",
    "SemanticTypeError",
    "affine",
    "ambiguous_tag",
    "check_compatible",
    "combine",
    "compatible",
    "is_ambiguous",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_compatibility.py -v`
Expected: PASS (14 from Tasks 1+3+4 + 6 = 20 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/semantic/compatibility.py dbse/semantic/__init__.py tests/semantic/test_compatibility.py
git commit -m "feat(l1.5): combine() for multiplication/division with ambiguity flag"
```

---

## Task 6: Property-based laws (QA-gate level 2)

**Files:**
- Create: `tests/semantic/test_properties.py`

- [ ] **Step 1: Write the test**

Create `tests/semantic/test_properties.py`:

```python
"""L1.5 property-based laws (QA-gate level 2): reflexivity and symmetry."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.semantic import Operator, affine, compatible

_SCALAR_TAGS = ["Energy", "Work", "Heat", "Power", "Length", "Mass", "Time"]
_VECTOR_TAGS = ["Force", "Velocity", "Momentum", "Torque"]
_ALL_TAGS = _SCALAR_TAGS + _VECTOR_TAGS
_ADDITIVE = [Operator.ADD, Operator.SUBTRACT]


@given(st.sampled_from(_ALL_TAGS), st.sampled_from(_ADDITIVE))
def test_addition_is_reflexive(tag: str, op: Operator) -> None:
    # A quantity is always addable to itself.
    assert compatible(affine(tag), affine(tag), op)


@given(
    st.sampled_from(_ALL_TAGS),
    st.sampled_from(_ALL_TAGS),
    st.sampled_from(_ADDITIVE),
)
def test_additive_compatibility_is_symmetric(a: str, b: str, op: Operator) -> None:
    # compatible(a, b) iff compatible(b, a) for + and -.
    assert compatible(affine(a), affine(b), op) == compatible(affine(b), affine(a), op)


@given(st.sampled_from(_ALL_TAGS), st.sampled_from(_ALL_TAGS))
def test_multiplication_is_always_compatible(a: str, b: str) -> None:
    assert compatible(affine(a), affine(b), Operator.MULTIPLY)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_properties.py -v`
Expected: PASS. If a case fails it reveals a real asymmetry bug — fix the implementation, not the test.

> This task has no new production code; it locks in the level-2 invariants.

- [ ] **Step 3: Commit**

```bash
git add tests/semantic/test_properties.py
git commit -m "test(l1.5): property-based compatibility laws (reflexivity, symmetry)"
```

---

## Task 7: Adversarial collision corpus (QA-gate level 5) + full gate

**Files:**
- Create: `tests/semantic/test_adversarial.py`

- [ ] **Step 1: Write the test**

Create `tests/semantic/test_adversarial.py`:

```python
"""L1.5 adversarial tests (QA-gate level 5): same-dimension semantic collisions."""

from __future__ import annotations

import pytest

from dbse.semantic import Operator, SemanticTypeError, affine, check_compatible

# Pairs that share a dimension but must NOT be addable.
_COLLISIONS = [
    ("Energy", "Torque"),
    ("Torque", "Energy"),
    ("Heat", "Torque"),
    ("Work", "Torque"),
    ("InternalEnergy", "Torque"),
]


@pytest.mark.parametrize(("left", "right"), _COLLISIONS)
def test_same_dimension_collisions_are_rejected(left: str, right: str) -> None:
    assert affine(left).dimension == affine(right).dimension  # same dimension
    with pytest.raises(SemanticTypeError):
        check_compatible(affine(left), affine(right), Operator.ADD)


def test_the_canonical_energy_plus_torque_attack() -> None:
    # The vulnerability the whole stage exists to close.
    with pytest.raises(SemanticTypeError) as excinfo:
        check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
    assert "Semantic mismatch at L1.5" in str(excinfo.value)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/semantic/test_adversarial.py -v`
Expected: PASS (5 parametrized + 1 = 6 passed).

- [ ] **Step 3: Run the full suite + quality gate**

Run: `ruff check . ; mypy ; python -m pytest -q`
Expected: `All checks passed!`, `Success: no issues found`, all tests pass (Stage 0 + L1 + the new L1.5 tests).

> If `ruff` flags the import of the private `_TAGS` in tests/impl, that is an
> intentional internal use; if your `ruff` config forbids it, expose a public
> `tag_spec(name)` accessor in `tags.py` and use that instead. If `mypy` flags the
> `frozenset({...})` key types, annotate the fusion tables exactly as written in
> Task 2 (they already carry explicit annotations).

- [ ] **Step 4: Commit**

```bash
git add tests/semantic/test_adversarial.py
git commit -m "test(l1.5): adversarial Energy+Torque collision corpus"
```

---

## Task 8: Update status docs

**Files:**
- Modify: `README.md` (Status section)
- Modify: `docs/spec-notes.md` (record Stage 2 decisions)

- [ ] **Step 1: Update README status**

In `README.md`, append to the "Статус" section:

```markdown
- Этап 2 — L1.5 (affine types): ✅ семантические теги + правила совместимости
  (`dbse/semantic/`). `compatible()`/`check_compatible()` навешивают семантику
  поверх L1-pruning (`check_add`/`check_subtract`). Интеграция в слой
  `L1.5.AFFINE_TYPES` — после L0 (Этап 3).
```

- [ ] **Step 2: Record Stage 2 decisions in spec-notes**

In `docs/spec-notes.md`, under "## Открытые вопросы (накапливаются по ходу)", add:

```markdown
- L1.5 (Stage 2) решения:
  - `compatible()`/`check_compatible()` для ADD/SUB вызывают L1 `check_add`/
    `check_subtract` для размерностного гейта и лишь *добавляют* проверку
    semantic_tag + tensor_rank — логика не дублируется (см. финальный ревью L1).
    Следствие: `J + N` → `DimensionError` (L1), `Energy + Torque` →
    `SemanticTypeError` (L1.5).
  - Неоднозначный результат `×` (напр. `Force × Length`) кодируется прямо в
    `semantic_tag` как отсортированная строка через `|` (`"Torque|Work"`),
    т.к. контракт `AffineType` заморожен (`semantic_tag: str`). Разрешает L2
    (Этап 8). Хелперы: `ambiguous_tag()`, `is_ambiguous()`.
  - `Operator` живёт в `dbse/semantic/operators.py` (переиспользуется L3 на
    Этапе 4).
  - Слой `dbse/layers/affine_types.py` остаётся pass-through до Этапа 3 (как
    `dbse/layers/dimensional.py` на Этапе 1).
```

- [ ] **Step 3: Commit**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 2 (L1.5 affine types) complete"
```

---

## Self-Review

**1. Spec coverage (ROADMAP Этап 2 DoD + scope):**
- "`AffineType = (Dimension, semantic_tag, tensor_rank, frame_of_reference)`" → already in `dbse/contracts/affine.py` (Stage 0); reused, factory `affine()` in Task 2. ✅
- "Реестр семантических тегов (Energy, Work, Heat, Torque, Force, Momentum…)" → Task 2 `_TAGS` (≥10, asserted). ✅
- "`compatible(a, b, op)` ADD/SUB: равны dimension и semantic_tag и tensor_rank" → Task 3 `_check_additive`. ✅
- "DOT: оба ранга 1, равные размерности" → Task 4 `_check_dot`. ✅
- "CROSS: оба полярные векторы" → Task 4 `_check_cross`. ✅
- "×/÷: разрешено, semantic_tag комбинируется (Force×Length→Work|Torque, пометка для L2)" → Task 5 `combine` + ambiguity flag. ✅
- "Информативная ошибка `SemanticTypeError` с подсказкой (Did you mean Work + Heat?)" → Task 1 error, Task 3 `_mismatch_message`/`_additive_suggestion`, asserted in Task 3 + Task 7. ✅
- DoD "`Energy + Torque` → `SemanticTypeError`" → Tasks 3 & 7. ✅
- DoD "`Work + Heat → InternalEnergy` валиден" → Task 3 `test_add_work_and_heat_fuses_to_internal_energy`. ✅
- DoD "покрытие тестами всех правил совместимости" → Tasks 3–5 cover ADD/SUB/DOT/CROSS/×/÷. ✅
- QA-gate "уровни 1 + 2 (рефлексивность/симметрия) + 5 (adversarial Energy+Torque)" → Tasks 1/3/4/5 (level 1), Task 6 (level 2), Task 7 (level 5). ✅
- **Reviewer note (the reason for this revision):** `check_add`/`check_subtract` remain the dimensional pruning; `compatible()` stacks semantic tags on top without duplicating logic → Task 3 `_check_additive` delegates the dimension gate to `check_add`/`check_subtract`; proven by `test_add_unlike_dimension_raises_dimension_error_not_semantic`. ✅

**2. Placeholder scan:** No TBD/TODO; every code step has full code; every test step has full test code. The only forward reference (`combine` used in Task 3's dispatch, defined in Task 5) is called out explicitly with the safe interim behavior. ✅

**3. Type consistency:**
- `AffineType(dimension, semantic_tag, tensor_rank, frame_of_reference)` matches `dbse/contracts/affine.py`. ✅
- `Dimension.of`, `*`, `/`, `==` match `dbse/contracts/dimensions.py`. ✅
- `check_add`/`check_subtract`/`DimensionError` imported from `dbse.dimensional` (exist in its `__init__`). ✅
- Public names consistent across tasks: `SemanticTypeError`, `Operator`, `affine`, `ambiguous_tag`, `is_ambiguous`, `compatible`, `check_compatible`, `combine`, `_TAGS`, `TagSpec`, `ADDITIVE_FUSIONS`, `MULTIPLICATIVE_FUSIONS`, `DIVISIVE_FUSIONS`. ✅
- `check_compatible`/`combine` return `AffineType`; `compatible` returns `bool`. ✅

No gaps found.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-l1_5-affine-types.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session with checkpoints for review.

Which approach?
