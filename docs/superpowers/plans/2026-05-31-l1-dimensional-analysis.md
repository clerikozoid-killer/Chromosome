# L1 Dimensional Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the L1 toolkit that parses unit strings (`"kg*m/s^2"`, `"N"`, `"Pa"`) into the existing `Dimension` type and enforces dimensional rules (`+/-` need equal dimensions, transcendental functions need dimensionless arguments).

**Architecture:** A new focused package `dbse/dimensional/` with four small modules — `errors` (the `DimensionError`), `units` (named-unit registry + SI prefix resolution, magnitude ignored), `parser` (left-to-right expression evaluator producing a `Dimension`), and `checks` (the `+/-` and transcendental rules). The pipeline layer `dbse/layers/dimensional.py` stays a stub until L0 (Stage 3) produces quantities to feed it; this stage builds and tests the reusable primitives.

**Tech Stack:** Python 3.11+, stdlib only at runtime (`re`, `fractions`), `pytest` + `hypothesis` for tests. Reuses `dbse.contracts.dimensions.Dimension`.

---

## Environment notes (read once)

- Activate the venv first, or prefix commands: PowerShell `.\.venv\Scripts\Activate.ps1`.
- All test commands below use `python -m pytest ...`. Run from repo root `c:\Users\Clerikozoid\Desktop\Chromosome`.
- Quality gate for every commit: `ruff check . ; mypy ; python -m pytest`.

## File Structure

- Create `dbse/dimensional/__init__.py` — public exports (`DimensionError`, `parse_unit`, `resolve`, `check_add`, `check_subtract`, `check_transcendental`).
- Create `dbse/dimensional/errors.py` — `DimensionError`.
- Create `dbse/dimensional/units.py` — `_UNITS` registry, `_PREFIXES`, `resolve(symbol) -> Dimension`.
- Create `dbse/dimensional/parser.py` — `parse_unit(text) -> Dimension` (+ private `_tokenize`, `_evaluate`).
- Create `dbse/dimensional/checks.py` — `check_add`, `check_subtract`, `check_transcendental`, `TRANSCENDENTAL`.
- Create `tests/dimensional/test_units.py` — registry + prefix resolution + the 30+ unit table.
- Create `tests/dimensional/test_parser.py` — composite expressions, powers, errors.
- Create `tests/dimensional/test_checks.py` — add/sub equality, transcendental rule.
- Create `tests/dimensional/test_properties.py` — property-based laws (parse consistency, conversion invariance).

---

## Task 0: Baseline commit of Stage 0

**Files:** none (git only).

- [ ] **Step 1: Confirm Stage 0 is green**

Run: `ruff check . ; mypy ; python -m pytest`
Expected: `All checks passed!`, `Success: no issues found`, `17 passed`.

- [ ] **Step 2: Commit the Stage 0 baseline**

```bash
git add .
git commit -m "chore: Stage 0 foundation (contracts, layer stubs, QA infra)"
```

---

## Task 1: `DimensionError`

**Files:**
- Create: `dbse/dimensional/errors.py`
- Create: `dbse/dimensional/__init__.py`
- Test: `tests/dimensional/test_checks.py`

- [ ] **Step 1: Write the failing test**

Create `tests/dimensional/test_checks.py`:

```python
"""L1 unit tests: dimensional rules and the DimensionError."""

from __future__ import annotations

import pytest

from dbse.dimensional import DimensionError


def test_dimension_error_is_a_value_error() -> None:
    assert issubclass(DimensionError, ValueError)
    with pytest.raises(DimensionError):
        raise DimensionError("boom")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/dimensional/test_checks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.dimensional'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/dimensional/errors.py`:

```python
"""L1 error type."""

from __future__ import annotations


class DimensionError(ValueError):
    """Raised when a dimensional rule is violated (L1).

    Examples: adding quantities of unlike dimension, passing a dimensionful
    argument to a transcendental function, or parsing an unknown unit.
    """
```

Create `dbse/dimensional/__init__.py`:

```python
"""L1 DIMENSIONAL ANALYSIS — unit parsing and dimensional rules."""

from dbse.dimensional.errors import DimensionError

__all__ = ["DimensionError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/dimensional/test_checks.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/dimensional/__init__.py dbse/dimensional/errors.py tests/dimensional/test_checks.py
git commit -m "feat(l1): add DimensionError"
```

---

## Task 2: Unit registry + SI prefix resolution

**Files:**
- Create: `dbse/dimensional/units.py`
- Modify: `dbse/dimensional/__init__.py`
- Test: `tests/dimensional/test_units.py`

- [ ] **Step 1: Write the failing test**

Create `tests/dimensional/test_units.py`:

```python
"""L1 unit tests: named-unit registry and SI-prefix resolution."""

from __future__ import annotations

import pytest

from dbse.contracts.dimensions import Dimension
from dbse.dimensional import DimensionError, resolve

# (symbol, expected dimension) — magnitude is irrelevant at L1.
RESOLVE_TABLE: list[tuple[str, Dimension]] = [
    ("kg", Dimension.of(1)),
    ("g", Dimension.of(1)),
    ("m", Dimension.of(0, 1)),
    ("s", Dimension.of(0, 0, 1)),
    ("A", Dimension.of(0, 0, 0, 1)),
    ("K", Dimension.of(0, 0, 0, 0, 1)),
    ("mol", Dimension.of(0, 0, 0, 0, 0, 1)),
    ("cd", Dimension.of(0, 0, 0, 0, 0, 0, 1)),
    ("N", Dimension.of(1, 1, -2)),
    ("J", Dimension.of(1, 2, -2)),
    ("W", Dimension.of(1, 2, -3)),
    ("Pa", Dimension.of(1, -1, -2)),
    ("Hz", Dimension.of(0, 0, -1)),
    ("C", Dimension.of(0, 0, 1, 1)),
    ("V", Dimension.of(1, 2, -3, -1)),
    ("ohm", Dimension.of(1, 2, -3, -2)),
    ("Ω", Dimension.of(1, 2, -3, -2)),
    # prefixes do not change the dimension:
    ("km", Dimension.of(0, 1)),
    ("mm", Dimension.of(0, 1)),
    ("mg", Dimension.of(1)),
    ("kN", Dimension.of(1, 1, -2)),
    ("MHz", Dimension.of(0, 0, -1)),
    ("kPa", Dimension.of(1, -1, -2)),
    ("µm", Dimension.of(0, 1)),
]


@pytest.mark.parametrize(("symbol", "expected"), RESOLVE_TABLE)
def test_resolve_known_symbols(symbol: str, expected: Dimension) -> None:
    assert resolve(symbol) == expected


def test_resolve_unknown_symbol_raises() -> None:
    with pytest.raises(DimensionError):
        resolve("zorp")


def test_registry_has_at_least_30_named_units() -> None:
    from dbse.dimensional.units import _UNITS

    assert len(_UNITS) >= 30
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/dimensional/test_units.py -v`
Expected: FAIL — `ImportError: cannot import name 'resolve' from 'dbse.dimensional'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/dimensional/units.py`:

```python
"""L1 named-unit registry and SI-prefix resolution.

At L1 only the *dimension* matters, not the magnitude, so SI prefixes
(kilo, milli, ...) leave the dimension unchanged — they only need to be
stripped to find the underlying unit.
"""

from __future__ import annotations

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional.errors import DimensionError

# Named units → dimensional signature [M, L, T, I, Θ, N, J].
_UNITS: dict[str, Dimension] = {
    # dimensionless
    "1": DIMENSIONLESS,
    "rad": DIMENSIONLESS,
    "sr": DIMENSIONLESS,
    # SI base
    "kg": Dimension.of(1),
    "g": Dimension.of(1),
    "m": Dimension.of(0, 1),
    "s": Dimension.of(0, 0, 1),
    "A": Dimension.of(0, 0, 0, 1),
    "K": Dimension.of(0, 0, 0, 0, 1),
    "mol": Dimension.of(0, 0, 0, 0, 0, 1),
    "cd": Dimension.of(0, 0, 0, 0, 0, 0, 1),
    # time / length alternates (dimension only)
    "min": Dimension.of(0, 0, 1),
    "h": Dimension.of(0, 0, 1),
    "day": Dimension.of(0, 0, 1),
    "L": Dimension.of(0, 3),
    # derived — mechanical
    "N": Dimension.of(1, 1, -2),
    "J": Dimension.of(1, 2, -2),
    "W": Dimension.of(1, 2, -3),
    "Pa": Dimension.of(1, -1, -2),
    "bar": Dimension.of(1, -1, -2),
    "Hz": Dimension.of(0, 0, -1),
    "eV": Dimension.of(1, 2, -2),
    "cal": Dimension.of(1, 2, -2),
    # derived — electromagnetic
    "C": Dimension.of(0, 0, 1, 1),
    "V": Dimension.of(1, 2, -3, -1),
    "ohm": Dimension.of(1, 2, -3, -2),
    "Ω": Dimension.of(1, 2, -3, -2),
    "F": Dimension.of(-1, -2, 4, 2),
    "S": Dimension.of(-1, -2, 3, 2),
    "Wb": Dimension.of(1, 2, -2, -1),
    "H": Dimension.of(1, 2, -2, -2),
}

# SI prefixes (longest first so "da" is tried before "d").
_PREFIXES: tuple[str, ...] = (
    "da",
    "y", "z", "a", "f", "p", "n", "u", "µ", "μ",
    "m", "c", "d", "h", "k", "M", "G", "T", "P", "E", "Z", "Y",
)


def resolve(symbol: str) -> Dimension:
    """Resolve a single unit symbol (optionally prefixed) to its dimension."""
    if symbol in _UNITS:
        return _UNITS[symbol]
    for prefix in sorted(_PREFIXES, key=len, reverse=True):
        if symbol.startswith(prefix):
            rest = symbol[len(prefix):]
            if rest and rest != "1" and rest in _UNITS:
                return _UNITS[rest]
    raise DimensionError(f"Unknown unit symbol: {symbol!r}")
```

Modify `dbse/dimensional/__init__.py` to re-export `resolve`:

```python
"""L1 DIMENSIONAL ANALYSIS — unit parsing and dimensional rules."""

from dbse.dimensional.errors import DimensionError
from dbse.dimensional.units import resolve

__all__ = ["DimensionError", "resolve"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/dimensional/test_units.py -v`
Expected: PASS (25 parametrized + 2 = 27 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/dimensional/units.py dbse/dimensional/__init__.py tests/dimensional/test_units.py
git commit -m "feat(l1): unit registry and SI-prefix resolution"
```

---

## Task 3: Unit expression parser

**Files:**
- Create: `dbse/dimensional/parser.py`
- Modify: `dbse/dimensional/__init__.py`
- Test: `tests/dimensional/test_parser.py`

- [ ] **Step 1: Write the failing test**

Create `tests/dimensional/test_parser.py`:

```python
"""L1 unit tests: the unit-expression parser."""

from __future__ import annotations

import pytest

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional import DimensionError, parse_unit

PARSE_TABLE: list[tuple[str, Dimension]] = [
    ("", DIMENSIONLESS),
    ("1", DIMENSIONLESS),
    ("kg", Dimension.of(1)),
    ("m/s", Dimension.of(0, 1, -1)),
    ("m/s^2", Dimension.of(0, 1, -2)),
    ("m*s^-2", Dimension.of(0, 1, -2)),
    ("kg*m/s^2", Dimension.of(1, 1, -2)),       # == N
    ("kg m / s^2", Dimension.of(1, 1, -2)),      # implicit multiplication
    ("m^3", Dimension.of(0, 3)),
    ("1/s", Dimension.of(0, 0, -1)),             # == Hz
    ("N*m", Dimension.of(1, 2, -2)),             # == J
    ("kg*m^2/s^2", Dimension.of(1, 2, -2)),      # == J
]


@pytest.mark.parametrize(("text", "expected"), PARSE_TABLE)
def test_parse_unit_expressions(text: str, expected: Dimension) -> None:
    assert parse_unit(text) == expected


def test_named_unit_equals_its_composition() -> None:
    assert parse_unit("N") == parse_unit("kg*m/s^2")
    assert parse_unit("J") == parse_unit("N*m")
    assert parse_unit("Pa") == parse_unit("N/m^2")


def test_caret_without_exponent_raises() -> None:
    with pytest.raises(DimensionError):
        parse_unit("m^")


def test_unknown_unit_in_expression_raises() -> None:
    with pytest.raises(DimensionError):
        parse_unit("kg*zorp")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/dimensional/test_parser.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_unit' from 'dbse.dimensional'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/dimensional/parser.py`:

```python
"""L1 unit-expression parser.

Grammar (no parentheses; YAGNI — named derived units cover the rest):

    expr   := factor (('*' | '/' | <implicit *>) factor)*
    factor := IDENT ('^' INT)?

Evaluation is strictly left-to-right, so "kg*m/s^2" == ((kg·m)/s²).
"""

from __future__ import annotations

import re

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional.errors import DimensionError
from dbse.dimensional.units import resolve

_TOKEN = re.compile(r"\s*(?:(?P<op>[*/^])|(?P<int>[+-]?\d+)|(?P<ident>[A-Za-zµμΩ]+))")


def parse_unit(text: str) -> Dimension:
    """Parse a unit expression into a :class:`Dimension`."""
    s = text.strip()
    if s in ("", "1", "dimensionless"):
        return DIMENSIONLESS
    return _evaluate(_tokenize(s), s)


def _tokenize(s: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if m is None or m.end() == pos:
            raise DimensionError(f"Cannot parse unit expression {s!r} near {s[pos:]!r}")
        pos = m.end()
        if m.group("op") is not None:
            tokens.append(("op", m.group("op")))
        elif m.group("int") is not None:
            tokens.append(("int", m.group("int")))
        else:
            tokens.append(("ident", m.group("ident")))
    return tokens


def _evaluate(tokens: list[tuple[str, str]], original: str) -> Dimension:
    result = DIMENSIONLESS
    op = "*"
    i = 0
    n = len(tokens)

    while i < n:
        kind, val = tokens[i]
        if kind == "op":
            if val in ("*", "/"):
                op = val
                i += 1
                continue
            raise DimensionError(f"Unexpected operator {val!r} in unit expression {original!r}")
        if kind == "int":
            raise DimensionError(f"Unexpected number {val!r} in unit expression {original!r}")

        # kind == "ident": a factor, optionally raised to an integer power.
        dim = resolve(val)
        i += 1
        if i < n and tokens[i] == ("op", "^"):
            i += 1
            if i >= n or tokens[i][0] != "int":
                raise DimensionError(
                    f"Expected integer exponent after '^' in unit expression {original!r}"
                )
            dim = dim ** int(tokens[i][1])
            i += 1

        result = result * dim if op == "*" else result / dim
        op = "*"  # adjacent factors multiply implicitly

    return result
```

Modify `dbse/dimensional/__init__.py`:

```python
"""L1 DIMENSIONAL ANALYSIS — unit parsing and dimensional rules."""

from dbse.dimensional.errors import DimensionError
from dbse.dimensional.parser import parse_unit
from dbse.dimensional.units import resolve

__all__ = ["DimensionError", "parse_unit", "resolve"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/dimensional/test_parser.py -v`
Expected: PASS (12 parametrized + 3 = 15 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/dimensional/parser.py dbse/dimensional/__init__.py tests/dimensional/test_parser.py
git commit -m "feat(l1): unit-expression parser"
```

---

## Task 4: Dimensional rules (`+/-` equality, transcendental dimensionless)

**Files:**
- Create: `dbse/dimensional/checks.py`
- Modify: `dbse/dimensional/__init__.py`
- Test: `tests/dimensional/test_checks.py` (append)

- [ ] **Step 1: Write the failing test (append to existing file)**

Append to `tests/dimensional/test_checks.py`:

```python
from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional import check_add, check_subtract, check_transcendental

_J = Dimension.of(1, 2, -2)
_N = Dimension.of(1, 1, -2)


def test_check_add_allows_equal_dimensions() -> None:
    assert check_add(_J, _J) == _J


def test_check_add_rejects_unequal_dimensions() -> None:
    # 1 J + 1 N must be rejected purely on dimensions.
    with pytest.raises(DimensionError):
        check_add(_J, _N)


def test_check_subtract_rejects_unequal_dimensions() -> None:
    with pytest.raises(DimensionError):
        check_subtract(_J, _N)


def test_transcendental_requires_dimensionless_argument() -> None:
    # sin(5 kg) is rejected.
    with pytest.raises(DimensionError):
        check_transcendental("sin", Dimension.of(1))


def test_transcendental_accepts_dimensionless_argument() -> None:
    assert check_transcendental("exp", DIMENSIONLESS) == DIMENSIONLESS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/dimensional/test_checks.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_add' from 'dbse.dimensional'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/dimensional/checks.py`:

```python
"""L1 dimensional rules used by the type checker and the solver."""

from __future__ import annotations

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional.errors import DimensionError

TRANSCENDENTAL: frozenset[str] = frozenset(
    {"sin", "cos", "tan", "asin", "acos", "atan",
     "exp", "log", "ln", "sinh", "cosh", "tanh"}
)


def check_add(left: Dimension, right: Dimension) -> Dimension:
    """Addition requires identical dimensions; returns that dimension."""
    if left != right:
        raise DimensionError(
            f"Cannot add quantities of unlike dimension: {left} + {right}"
        )
    return left


def check_subtract(left: Dimension, right: Dimension) -> Dimension:
    """Subtraction requires identical dimensions; returns that dimension."""
    if left != right:
        raise DimensionError(
            f"Cannot subtract quantities of unlike dimension: {left} - {right}"
        )
    return left


def check_transcendental(func: str, arg: Dimension) -> Dimension:
    """A transcendental function requires a dimensionless argument."""
    if not arg.is_dimensionless:
        raise DimensionError(
            f"Argument of {func}() must be dimensionless, got {arg}"
        )
    return DIMENSIONLESS
```

Modify `dbse/dimensional/__init__.py`:

```python
"""L1 DIMENSIONAL ANALYSIS — unit parsing and dimensional rules."""

from dbse.dimensional.checks import (
    TRANSCENDENTAL,
    check_add,
    check_subtract,
    check_transcendental,
)
from dbse.dimensional.errors import DimensionError
from dbse.dimensional.parser import parse_unit
from dbse.dimensional.units import resolve

__all__ = [
    "TRANSCENDENTAL",
    "DimensionError",
    "check_add",
    "check_subtract",
    "check_transcendental",
    "parse_unit",
    "resolve",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/dimensional/test_checks.py -v`
Expected: PASS (1 from Task 1 + 5 = 6 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/dimensional/checks.py dbse/dimensional/__init__.py tests/dimensional/test_checks.py
git commit -m "feat(l1): add/subtract equality and transcendental dimensionless rules"
```

---

## Task 5: Property-based laws (QA-gate level 2)

**Files:**
- Create: `tests/dimensional/test_properties.py`

- [ ] **Step 1: Write the failing test**

Create `tests/dimensional/test_properties.py`:

```python
"""L1 property-based laws (QA-gate level 2)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.dimensional import parse_unit, resolve

_BASE_SYMBOLS = ["kg", "m", "s", "A", "K", "mol", "cd"]


@given(st.sampled_from(_BASE_SYMBOLS), st.integers(min_value=1, max_value=5))
def test_power_equals_repeated_multiplication(symbol: str, power: int) -> None:
    # "m^3" == "m*m*m"
    via_power = parse_unit(f"{symbol}^{power}")
    via_product = parse_unit("*".join([symbol] * power))
    assert via_power == via_product


@given(st.sampled_from(_BASE_SYMBOLS))
def test_multiply_then_divide_is_identity(symbol: str) -> None:
    # "kg*m/m" == "kg"
    assert parse_unit(f"kg*{symbol}/{symbol}") == resolve("kg")


@given(st.sampled_from(["k", "m", "M", "µ", "n"]), st.sampled_from(["m", "s", "g", "N", "Pa"]))
def test_prefix_does_not_change_dimension(prefix: str, unit: str) -> None:
    # A prefixed unit has the same dimension as the bare unit (magnitude aside).
    assert resolve(prefix + unit) == resolve(unit)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/dimensional/test_properties.py -v`
Expected: PASS already (it only uses public APIs built in Tasks 2-3). If any case fails, it reveals a real parser/resolver bug — fix the implementation, not the test.

> Note: this task has no new production code; it locks in invariants. If all pass on first run, proceed to Step 3.

- [ ] **Step 3: Run the full suite + quality gate**

Run: `ruff check . ; mypy ; python -m pytest`
Expected: `All checks passed!`, `Success: no issues found`, all tests passed (Stage 0 `17` + L1 tasks).

- [ ] **Step 4: Commit**

```bash
git add tests/dimensional/test_properties.py
git commit -m "test(l1): property-based dimensional laws"
```

---

## Task 6: Update status docs

**Files:**
- Modify: `README.md` (Status section)
- Modify: `docs/spec-notes.md` (Open questions, if any surfaced)

- [ ] **Step 1: Update README status**

In `README.md`, change the "Статус" section to note L1 is implemented:

```markdown
## Статус

- Этап 0 — фундамент: ✅ каркас, контракты, заглушки, QA-инфра.
- Этап 1 — L1 (размерностный анализ): ✅ парсинг единиц + правила размерностей
  (`dbse/dimensional/`). Интеграция в слой `L1.DIMENSIONS` — после L0 (Этап 3).
```

- [ ] **Step 2: Commit**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 1 (L1 dimensional analysis) complete"
```

---

## Self-Review

**1. Spec coverage (ROADMAP Этап 1 DoD):**
- "таблица из 30+ единиц парсится корректно" → Task 2 registry (≥30, asserted) + Task 3 parse table. ✅
- "`sin(5 kg)` отвергается" → Task 4 `test_transcendental_requires_dimensionless_argument`. ✅
- "`1 J + 1 N` отвергается по размерности" → Task 4 `test_check_add_rejects_unequal_dimensions`. ✅
- QA-gate "уровни 1 (юнит) + 2 (property: `Dim(a·b)=Dim(a)+Dim(b)`, инвариантность к конвертации)" → Tasks 1-4 (unit) + Task 5 (property: power=repeated multiply, multiply/divide identity, prefix invariance). ✅
  - Note: `Dim(a·b)=Dim(a)+Dim(b)` itself is already covered by Stage 0 `test_property_mul_is_exponentwise_addition`; Task 5 adds the L1-level parse/resolve invariants.

**2. Placeholder scan:** No TBD/TODO; every code step contains full code; every test step contains full test code. ✅

**3. Type consistency:**
- `Dimension.of(...)`, `Dimension.__mul__/__truediv__/__pow__`, `DIMENSIONLESS`, `.is_dimensionless` — all match `dbse/contracts/dimensions.py` (Stage 0). ✅
- Public names used consistently across tasks: `DimensionError`, `resolve`, `parse_unit`, `check_add`, `check_subtract`, `check_transcendental`, `TRANSCENDENTAL`, `_UNITS`, `_PREFIXES`. ✅
- `resolve` returns `Dimension`; `parse_unit` returns `Dimension`; checks return `Dimension`. ✅

No gaps found.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-l1-dimensional-analysis.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session with checkpoints for review.

Which approach?
