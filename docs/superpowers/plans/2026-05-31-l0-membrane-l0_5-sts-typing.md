# L0 MEMBRANE + L0.5 STS Typing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a free-text query into a strictly-validated entity graph (L0 MEMBRANE) and classify the query's type for routing (L0.5 STS Typing) — so that prompt-injection attempts (`SUPPRESS(friction)`, injected `invariant`/`operator`/`context` nodes, off-schema fields) are rejected by the schema (→ `clarification`) and opinion queries are refused (→ `UNHANDLED`). This closes vulnerability #2 (Prompt Injection in L0).

**Architecture:** Two new focused packages mirroring `dbse/dimensional/` and `dbse/semantic/`:
- `dbse/membrane/` — the L0 primitives: a strict **Pydantic v2** output schema (`schema.py`), a provider-agnostic parser interface plus a **deterministic, network-free fallback parser** (`adapter.py`), and `MembraneError` (`errors.py`). The schema is the security boundary: `extra="forbid"` on every model means the LLM physically cannot emit `INVARIANT`/`CONTEXT`/`OPERATOR` nodes or any off-schema field; `question_type` is a closed enum; quantity/relation units must parse through the **existing L1** `parse_unit` (reuse, not re-implement); object references must resolve.
- `dbse/sts/` — the L0.5 primitives: a `QueryType` enum, a `ROUTES` map, and a rule-based `classify()` (no LLM).

The two pipeline layers `dbse/layers/membrane.py` and `dbse/layers/sts_typing.py` stop being pass-through stubs and wire these primitives into the conveyor: MEMBRANE parses+validates (halts `CLARIFICATION` on schema violation), STS classifies (halts `UNHANDLED` on `OPINION`). The L1/L1.5 layers stay pass-through — attaching `AffineType` to an AST is Stage 4 (RIBOSOME).

**Tech Stack:** Python 3.11+, **Pydantic v2** (first runtime dependency — mandated by the spec: "строго валидируется Pydantic"), `pytest` + `hypothesis` for tests. Reuses `dbse.dimensional.{parse_unit, DimensionError}` for unit validation and `dbse.contracts.context.{PipelineContext, HaltReason}` for layer wiring.

---

## Environment notes (read once)

- Activate the venv first, or prefix commands: PowerShell `.\.venv\Scripts\Activate.ps1`.
- All test commands below use `python -m pytest ...`. Run from repo root `c:\Users\Clerikozoid\Desktop\Chromosome`.
- The shell is PowerShell: chain commands with `;`, **not** `&&`.
- Quality gate for every commit: `ruff check . ; mypy ; python -m pytest`.
- **After Task 1 edits `pyproject.toml`, reinstall once** so Pydantic and the mypy plugin are picked up: `pip install -e ".[dev]"`.

## Key design decisions (made here, per the spec — note, don't re-litigate)

1. **Pydantic v2 is introduced as the first runtime dependency.** The spec (§2 L0, §6 mitigation table) explicitly mandates a strict Pydantic schema. Up to now `dependencies = []`; Task 1 adds `pydantic>=2,<3` and the `pydantic.mypy` plugin (strict mypy is on).
2. **The deterministic fallback parser drives every test.** No network, no real LLM. The real LLM provider is out of scope for Stage 3; only the `ParserAdapter` Protocol (the seam a provider plugs into) and the deterministic implementation ship. This honours the project rule "тестируемость без LLM".
3. **The schema is the injection boundary.** `extra="forbid"` everywhere + a closed `question_type` enum + referential-integrity + unit-validation are what reject injection. The deterministic parser, by construction, can only emit `OBJECT`/`QUANTITY`/`RELATION`/`question_type`/`target` — never `INVARIANT`/`CONTEXT`/`OPERATOR`.
4. **The fallback parser never raises on plain natural language.** It extracts what it can (number+unit pairs whose unit resolves through L1), drops the rest, and always emits a schema-valid minimal membrane (one `obj_1` system object). Only a *compromised* / explicitly-bad adapter payload trips `MembraneError`. Tests exercise the halt path with a stub adapter that returns a bad dict.
5. **Scope guard:** L1/L1.5 *layer* integration (attaching `AffineType` to AST nodes) is **Stage 4**, not here. Stage 3 only reuses L1's `parse_unit` to validate unit *strings* at the boundary. `dbse/layers/{dimensional,affine_types}.py` stay pass-through.

## File Structure

L0 — `dbse/membrane/`:
- Create `dbse/membrane/__init__.py` — public exports.
- Create `dbse/membrane/errors.py` — `MembraneError`.
- Create `dbse/membrane/schema.py` — `QuestionType`, `ObjectNode`, `QuantityNode`, `RelationNode`, `Target`, `MembraneOutput`, `validate_membrane()`.
- Create `dbse/membrane/adapter.py` — `ParserAdapter` Protocol, `DeterministicParser`.

L0.5 — `dbse/sts/`:
- Create `dbse/sts/__init__.py` — public exports.
- Create `dbse/sts/classifier.py` — `QueryType`, `ROUTES`, `classify()`.

Layer wiring:
- Modify `dbse/layers/membrane.py` — real `Membrane` layer.
- Modify `dbse/layers/sts_typing.py` — real `StsTyping` layer.

Tests + fixtures:
- Create `tests/membrane/__init__.py`, `tests/sts/__init__.py` (package markers — pytest prepend-import mode needs them, per the Stage 2 note).
- Create `tests/membrane/test_schema.py` — schema accept/reject, enum, refs, unit validation.
- Create `tests/membrane/test_adapter.py` — deterministic extraction.
- Create `tests/membrane/test_layer.py` — MEMBRANE layer wiring + halt.
- Create `tests/membrane/test_adversarial.py` — prompt-injection corpus (QA level 5).
- Create `tests/membrane/test_parse_accuracy.py` — parsing accuracy vs labeled corpus (QA level 7, deterministic stand-in).
- Create `tests/sts/test_classifier.py` — classification rules + routing.
- Create `tests/sts/test_layer.py` — STS layer wiring + `UNHANDLED` halt.
- Create `cases/parse/membrane_parse.jsonl` — labeled parsing corpus.

Docs:
- Modify `README.md`, `docs/spec-notes.md`.

---

## Task 0: Baseline is green

**Files:** none (verification only).

- [ ] **Step 1: Confirm Stages 0–2 are committed and the suite is green**

Run: `git log --oneline -3 ; ruff check . ; mypy ; python -m pytest -q`
Expected: recent commits include the L1.5 work; `All checks passed!`; `Success: no issues found`; all tests pass.

> No commit in this task — a smoke check before starting Stage 3.

---

## Task 1: Add Pydantic, `MembraneError`, and the `dbse/membrane` skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `dbse/membrane/errors.py`
- Create: `dbse/membrane/__init__.py`
- Create: `tests/membrane/__init__.py`
- Create: `tests/membrane/test_schema.py`

- [ ] **Step 1: Write the failing test**

Create `tests/membrane/__init__.py` (empty file):

```python
```

Create `tests/membrane/test_schema.py`:

```python
"""L0 unit tests: the MEMBRANE output schema and MembraneError."""

from __future__ import annotations

import pytest

from dbse.membrane import MembraneError


def test_membrane_error_is_a_value_error() -> None:
    assert issubclass(MembraneError, ValueError)
    with pytest.raises(MembraneError):
        raise MembraneError("boom")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/membrane/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.membrane'`.

- [ ] **Step 3: Write minimal implementation**

In `pyproject.toml`, change the runtime dependencies and add the Pydantic mypy plugin.

Replace:

```toml
dependencies = []
```

with:

```toml
dependencies = ["pydantic>=2,<3"]
```

Replace the `[tool.mypy]` block:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_configs = true
files = ["dbse", "tests"]
```

with:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_configs = true
files = ["dbse", "tests"]
plugins = ["pydantic.mypy"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

Create `dbse/membrane/errors.py`:

```python
"""L0 error type."""

from __future__ import annotations


class MembraneError(ValueError):
    """Raised when the MEMBRANE output fails strict schema validation (L0).

    A ``MembraneError`` means the parsed payload escaped the allowed shape — an
    off-schema field, a forbidden node type (``INVARIANT``/``CONTEXT``/``OPERATOR``),
    an unknown ``question_type``, an unresolvable unit, or a dangling reference.
    The MEMBRANE layer turns this into a ``HaltReason.CLARIFICATION`` rather than
    silently "completing" the input (the v5.0 prompt-injection mitigation).
    """
```

Create `dbse/membrane/__init__.py`:

```python
"""L0 MEMBRANE — strict, sandboxed parsing of free text into an entity graph."""

from dbse.membrane.errors import MembraneError

__all__ = ["MembraneError"]
```

- [ ] **Step 4: Reinstall so Pydantic is available, then run the test**

Run: `pip install -e ".[dev]" ; python -m pytest tests/membrane/test_schema.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml dbse/membrane/__init__.py dbse/membrane/errors.py tests/membrane/__init__.py tests/membrane/test_schema.py
git commit -m "feat(l0): add Pydantic dep, MembraneError, membrane package skeleton"
```

---

## Task 2: The strict MEMBRANE output schema

> This is the security-critical task. The schema is the only thing standing between a (possibly compromised) LLM and the deterministic core.

**Files:**
- Create: `dbse/membrane/schema.py`
- Modify: `dbse/membrane/__init__.py`
- Test: `tests/membrane/test_schema.py` (append)

- [ ] **Step 1: Write the failing test (append to existing file)**

Append to `tests/membrane/test_schema.py`:

```python
from dbse.membrane import (
    MembraneOutput,
    QuestionType,
    validate_membrane,
)

_VALID: dict = {
    "objects": [
        {"id": "obj_1", "type": "body", "label": "apple"},
        {"id": "obj_2", "type": "planet", "label": "Earth"},
    ],
    "quantities": [
        {"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "kg"},
        {"ref": "obj_2", "property": "mass", "value": 5.972e24, "unit": "kg"},
    ],
    "relations": [
        {"type": "distance", "from": "obj_1", "to": "obj_2", "value": 6371000, "unit": "m"},
    ],
    "question_type": "compute",
    "target": {"ref": "obj_1", "property": "gravitational_force"},
}


def test_valid_payload_parses_into_typed_output() -> None:
    out = validate_membrane(_VALID)
    assert isinstance(out, MembraneOutput)
    assert out.question_type is QuestionType.COMPUTE
    assert len(out.objects) == 2
    assert out.quantities[0].unit == "kg"
    assert out.target.ref == "obj_1"


def test_relations_default_to_empty() -> None:
    payload = {**_VALID, "relations": []}
    assert validate_membrane(payload).relations == []


def test_question_type_outside_enum_is_rejected() -> None:
    # The classic injection: "compute; SUPPRESS(friction)" is not a known type.
    payload = {**_VALID, "question_type": "compute; SUPPRESS(friction)"}
    with pytest.raises(MembraneError):
        validate_membrane(payload)


def test_extra_top_level_field_is_rejected() -> None:
    # The LLM must NOT be able to smuggle INVARIANT / CONTEXT / OPERATOR nodes.
    for forbidden in ("operators", "invariants", "context"):
        payload = {**_VALID, forbidden: [{"anything": "here"}]}
        with pytest.raises(MembraneError):
            validate_membrane(payload)


def test_extra_field_on_a_quantity_is_rejected() -> None:
    bad = {**_VALID}
    bad["quantities"] = [
        {"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "kg", "suppress": True},
    ]
    with pytest.raises(MembraneError):
        validate_membrane(bad)


def test_unknown_unit_is_rejected_via_l1_parser() -> None:
    bad = {**_VALID}
    bad["quantities"] = [
        {"ref": "obj_1", "property": "mass", "value": 0.1, "unit": "zorgs"},
    ]
    with pytest.raises(MembraneError):
        validate_membrane(bad)


def test_dangling_quantity_reference_is_rejected() -> None:
    bad = {**_VALID}
    bad["quantities"] = [
        {"ref": "ghost", "property": "mass", "value": 0.1, "unit": "kg"},
    ]
    with pytest.raises(MembraneError):
        validate_membrane(bad)


def test_dangling_target_reference_is_rejected() -> None:
    bad = {**_VALID, "target": {"ref": "ghost", "property": "force"}}
    with pytest.raises(MembraneError):
        validate_membrane(bad)


def test_relation_unit_may_be_omitted_but_must_resolve_when_present() -> None:
    ok = {**_VALID}
    ok["relations"] = [{"type": "touches", "from": "obj_1", "to": "obj_2"}]
    assert validate_membrane(ok).relations[0].unit is None

    bad = {**_VALID}
    bad["relations"] = [
        {"type": "distance", "from": "obj_1", "to": "obj_2", "value": 1, "unit": "zorgs"},
    ]
    with pytest.raises(MembraneError):
        validate_membrane(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/membrane/test_schema.py -v`
Expected: FAIL — `ImportError: cannot import name 'MembraneOutput' from 'dbse.membrane'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/membrane/schema.py`:

```python
"""L0 MEMBRANE output schema — the strict, sandboxed boundary.

Pydantic v2 models with ``extra="forbid"`` everywhere: the LLM may emit ONLY
``OBJECT`` / ``QUANTITY`` / ``RELATION`` nodes, a closed ``question_type`` enum and
a ``target`` — never ``INVARIANT`` / ``CONTEXT`` / ``OPERATOR`` (those are produced
deterministically downstream, not by the LLM). Unit strings are validated by the
*existing* L1 ``parse_unit`` (reuse, not re-implementation), and every reference
must resolve to a declared object. Any escape from this shape raises
:class:`MembraneError`, which the layer maps to ``HaltReason.CLARIFICATION``.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from dbse.dimensional import DimensionError, parse_unit
from dbse.membrane.errors import MembraneError

_STRICT = ConfigDict(extra="forbid", populate_by_name=True)


class QuestionType(StrEnum):
    """The only query intents the LLM may assign (closed set)."""

    COMPUTE = "compute"
    PROVE = "prove"
    EXPLAIN = "explain"


def _validate_unit(unit: str | None) -> str | None:
    """Reject any unit string the L1 parser cannot resolve."""
    if unit is None:
        return None
    try:
        parse_unit(unit)
    except DimensionError as exc:
        raise ValueError(f"Unresolvable unit {unit!r}: {exc}") from exc
    return unit


class ObjectNode(BaseModel):
    """A physical entity. The LLM may name it but not endow it with physics."""

    model_config = _STRICT

    id: str
    type: str
    label: str


class QuantityNode(BaseModel):
    """A numeric value with a unit, attached to an object via ``ref``."""

    model_config = _STRICT

    ref: str
    property: str
    value: float
    unit: str

    _check_unit = field_validator("unit")(_validate_unit)


class RelationNode(BaseModel):
    """A typed relation between two objects, optionally quantified."""

    model_config = _STRICT

    type: str
    from_: str = Field(alias="from")
    to: str
    value: float | None = None
    unit: str | None = None

    _check_unit = field_validator("unit")(_validate_unit)


class Target(BaseModel):
    """What the query asks to compute/prove/explain."""

    model_config = _STRICT

    ref: str
    property: str


class MembraneOutput(BaseModel):
    """The whole validated L0 payload."""

    model_config = _STRICT

    objects: list[ObjectNode] = Field(default_factory=list)
    quantities: list[QuantityNode] = Field(default_factory=list)
    relations: list[RelationNode] = Field(default_factory=list)
    question_type: QuestionType
    target: Target

    @model_validator(mode="after")
    def _references_resolve(self) -> MembraneOutput:
        known = {obj.id for obj in self.objects}
        dangling: list[str] = []
        for q in self.quantities:
            if q.ref not in known:
                dangling.append(q.ref)
        for r in self.relations:
            dangling += [ref for ref in (r.from_, r.to) if ref not in known]
        if self.target.ref not in known:
            dangling.append(self.target.ref)
        if dangling:
            raise ValueError(f"Dangling object reference(s): {sorted(set(dangling))}")
        return self


def validate_membrane(raw: dict[str, object]) -> MembraneOutput:
    """Validate a raw parser payload, mapping any failure to :class:`MembraneError`."""
    try:
        return MembraneOutput.model_validate(raw)
    except ValidationError as exc:
        raise MembraneError(f"MEMBRANE schema violation:\n{exc}") from exc
```

Modify `dbse/membrane/__init__.py`:

```python
"""L0 MEMBRANE — strict, sandboxed parsing of free text into an entity graph."""

from dbse.membrane.errors import MembraneError
from dbse.membrane.schema import (
    MembraneOutput,
    ObjectNode,
    QuantityNode,
    QuestionType,
    RelationNode,
    Target,
    validate_membrane,
)

__all__ = [
    "MembraneError",
    "MembraneOutput",
    "ObjectNode",
    "QuantityNode",
    "QuestionType",
    "RelationNode",
    "Target",
    "validate_membrane",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/membrane/test_schema.py -v`
Expected: PASS (1 from Task 1 + 9 = 10 passed).

> If `mypy` later complains about the `field_validator(...)` assignment lines, the `pydantic.mypy` plugin (added in Task 1) understands them. Run `mypy` now to confirm: `mypy` → `Success: no issues found`.

- [ ] **Step 5: Commit**

```bash
git add dbse/membrane/schema.py dbse/membrane/__init__.py tests/membrane/test_schema.py
git commit -m "feat(l0): strict Pydantic MEMBRANE schema (extra=forbid, refs, units)"
```

---

## Task 3: The deterministic fallback parser

**Files:**
- Create: `dbse/membrane/adapter.py`
- Modify: `dbse/membrane/__init__.py`
- Test: `tests/membrane/test_adapter.py`

- [ ] **Step 1: Write the failing test**

Create `tests/membrane/test_adapter.py`:

```python
"""L0 unit tests: the deterministic (network-free) fallback parser."""

from __future__ import annotations

from dbse.membrane import DeterministicParser, validate_membrane


def _parse(query: str) -> dict:
    return DeterministicParser().parse(query)


def test_extracts_value_unit_pairs() -> None:
    raw = _parse("an apple of mass 0.1 kg falls 5 m")
    pairs = {(q["value"], q["unit"]) for q in raw["quantities"]}
    assert (0.1, "kg") in pairs
    assert (5.0, "m") in pairs


def test_extracts_scientific_notation_and_compound_units() -> None:
    raw = _parse("gravity is 9.81 m/s^2 over 5.972e24 kg")
    pairs = {(q["value"], q["unit"]) for q in raw["quantities"]}
    assert (9.81, "m/s^2") in pairs
    assert (5.972e24, "kg") in pairs


def test_drops_quantities_with_unresolvable_units() -> None:
    raw = _parse("there are 5 apples and 3 kg of flour")
    units = {q["unit"] for q in raw["quantities"]}
    assert "kg" in units
    assert "apples" not in units  # 'apples' does not resolve via L1


def test_always_emits_one_system_object() -> None:
    raw = _parse("anything at all")
    assert raw["objects"] == [{"id": "obj_1", "type": "system", "label": "query"}]


def test_question_type_compute_prove_explain() -> None:
    assert _parse("compute the 3 kg force")["question_type"] == "compute"
    assert _parse("prove that the set is infinite")["question_type"] == "prove"
    assert _parse("what is entropy")["question_type"] == "explain"


def test_output_is_always_schema_valid() -> None:
    # Whatever NL we throw at it, the result must pass strict validation.
    for query in ["", "hello", "mass 0.1 kg", "what is the best language?"]:
        validate_membrane(_parse(query))  # must not raise


def test_property_keyword_is_attached_when_present() -> None:
    raw = _parse("mass 0.1 kg")
    masses = [q for q in raw["quantities"] if q["property"] == "mass"]
    assert masses and masses[0]["value"] == 0.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/membrane/test_adapter.py -v`
Expected: FAIL — `ImportError: cannot import name 'DeterministicParser' from 'dbse.membrane'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/membrane/adapter.py`:

```python
"""L0 parser adapters.

``ParserAdapter`` is the provider-agnostic seam: a real LLM provider plugs in here
later. ``DeterministicParser`` is the network-free fallback used for tests and
non-standard input — it extracts ``value+unit`` pairs (validated through the L1
unit parser), infers a coarse ``question_type``, and emits a schema-valid payload.
It can only ever produce the allowed node kinds, so it is injection-safe by
construction.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, Protocol, runtime_checkable

from dbse.dimensional import DimensionError, parse_unit

# A number (int / float / scientific) followed by a unit token. The unit token is
# letters, optionally raised to an integer power and chained with '*' or '/'.
_NUMBER_UNIT = re.compile(
    r"(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
    r"(?P<unit>[A-Za-zµμΩ]+(?:\^-?\d+)?(?:[*/][A-Za-zµμΩ]+(?:\^-?\d+)?)*)"
)

# question_type markers, checked in this order.
_PROVE_MARKERS = ("prove", "theorem", "докаж", "теорем")
_EXPLAIN_MARKERS = ("what is", "what are", "define", "definition", "что такое", "определени")

# property stems → canonical property (EN + RU), matched against the words just
# before a number.
_PROPERTY_STEMS: tuple[tuple[str, str], ...] = (
    ("mass", "mass"),
    ("масс", "mass"),
    ("distance", "distance"),
    ("расстояни", "distance"),
    ("velocit", "velocity"),
    ("speed", "velocity"),
    ("скорост", "velocity"),
    ("force", "force"),
    ("сил", "force"),
    ("energy", "energy"),
    ("энерг", "energy"),
    ("time", "time"),
    ("врем", "time"),
)

_OBJECT: dict[str, str] = {"id": "obj_1", "type": "system", "label": "query"}


@runtime_checkable
class ParserAdapter(Protocol):
    """A parser that turns a raw query into an (unvalidated) membrane payload."""

    name: ClassVar[str]

    def parse(self, query: str) -> dict[str, Any]:
        """Return a dict to be validated by :func:`validate_membrane`."""
        ...


class DeterministicParser:
    """Rule-based, network-free fallback parser."""

    name: ClassVar[str] = "deterministic"

    def parse(self, query: str) -> dict[str, Any]:
        text = query.casefold()
        quantities = self._extract_quantities(query, text)
        return {
            "objects": [dict(_OBJECT)],
            "quantities": quantities,
            "relations": [],
            "question_type": self._question_type(text),
            "target": {"ref": "obj_1", "property": self._target_property(text)},
        }

    def _extract_quantities(self, query: str, text: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for match in _NUMBER_UNIT.finditer(query):
            unit = match.group("unit")
            try:
                parse_unit(unit)
            except DimensionError:
                continue  # unit does not resolve in L1 — drop the pair
            out.append(
                {
                    "ref": "obj_1",
                    "property": self._property_before(text, match.start()),
                    "value": float(match.group("value")),
                    "unit": unit,
                }
            )
        return out

    @staticmethod
    def _property_before(text: str, index: int) -> str:
        window = text[max(0, index - 24) : index]
        for stem, prop in _PROPERTY_STEMS:
            if stem in window:
                return prop
        return "value"

    @staticmethod
    def _question_type(text: str) -> str:
        if any(m in text for m in _EXPLAIN_MARKERS):
            return "explain"
        if any(m in text for m in _PROVE_MARKERS):
            return "prove"
        return "compute"

    @staticmethod
    def _target_property(text: str) -> str:
        for stem, prop in _PROPERTY_STEMS:
            if stem in text:
                return prop
        return "value"
```

Modify `dbse/membrane/__init__.py` to export the adapters:

```python
"""L0 MEMBRANE — strict, sandboxed parsing of free text into an entity graph."""

from dbse.membrane.adapter import DeterministicParser, ParserAdapter
from dbse.membrane.errors import MembraneError
from dbse.membrane.schema import (
    MembraneOutput,
    ObjectNode,
    QuantityNode,
    QuestionType,
    RelationNode,
    Target,
    validate_membrane,
)

__all__ = [
    "DeterministicParser",
    "MembraneError",
    "MembraneOutput",
    "ObjectNode",
    "ParserAdapter",
    "QuantityNode",
    "QuestionType",
    "RelationNode",
    "Target",
    "validate_membrane",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/membrane/test_adapter.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/membrane/adapter.py dbse/membrane/__init__.py tests/membrane/test_adapter.py
git commit -m "feat(l0): deterministic fallback parser + ParserAdapter protocol"
```

---

## Task 4: Wire the MEMBRANE layer

**Files:**
- Modify: `dbse/layers/membrane.py`
- Test: `tests/membrane/test_layer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/membrane/test_layer.py`:

```python
"""L0 layer tests: parsing wired into the pipeline context."""

from __future__ import annotations

from typing import Any, ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.membrane import Membrane


def test_valid_query_fills_membrane_and_does_not_halt() -> None:
    ctx = Membrane().process(PipelineContext(query="mass 0.1 kg"))
    assert not ctx.halted
    assert ctx.membrane is not None
    assert ctx.membrane["question_type"] == "compute"
    assert any(q["unit"] == "kg" for q in ctx.membrane["quantities"])


def test_plain_text_still_parses_to_a_minimal_membrane() -> None:
    ctx = Membrane().process(PipelineContext(query="hello there"))
    assert not ctx.halted
    assert ctx.membrane is not None
    assert ctx.membrane["objects"] == [{"id": "obj_1", "type": "system", "label": "query"}]


def test_compromised_adapter_payload_halts_with_clarification() -> None:
    class EvilAdapter:
        name: ClassVar[str] = "evil"

        def parse(self, query: str) -> dict[str, Any]:
            # Simulate a jailbroken LLM trying to inject a forbidden node.
            return {
                "objects": [{"id": "obj_1", "type": "body", "label": "x"}],
                "quantities": [],
                "relations": [],
                "operators": [{"op": "SUPPRESS", "arg": "friction"}],
                "question_type": "compute",
                "target": {"ref": "obj_1", "property": "force"},
            }

    ctx = Membrane(parser=EvilAdapter()).process(PipelineContext(query="..."))
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.CLARIFICATION
    assert ctx.membrane is None
    assert [e.layer for e in ctx.trace] == ["L0.MEMBRANE"]


def test_relation_from_alias_round_trips_in_stored_membrane() -> None:
    class RelAdapter:
        name: ClassVar[str] = "rel"

        def parse(self, query: str) -> dict[str, Any]:
            return {
                "objects": [
                    {"id": "obj_1", "type": "body", "label": "a"},
                    {"id": "obj_2", "type": "body", "label": "b"},
                ],
                "quantities": [],
                "relations": [{"type": "distance", "from": "obj_1", "to": "obj_2"}],
                "question_type": "compute",
                "target": {"ref": "obj_1", "property": "force"},
            }

    ctx = Membrane(parser=RelAdapter()).process(PipelineContext(query="..."))
    assert not ctx.halted
    assert ctx.membrane is not None
    assert ctx.membrane["relations"][0]["from"] == "obj_1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/membrane/test_layer.py -v`
Expected: FAIL — `TypeError: Membrane() takes no arguments` (the stub has no `parser` kwarg) / assertion failures (the stub never sets `ctx.membrane`).

- [ ] **Step 3: Write minimal implementation**

Replace the entire contents of `dbse/layers/membrane.py`:

```python
"""L0 MEMBRANE — parse free text into a strictly-validated entity graph.

The LLM (or, in tests, the deterministic fallback) runs in a sandbox: its output
is validated against the strict Pydantic schema before anything downstream sees
it. A schema violation halts the pipeline with ``CLARIFICATION`` instead of
silently "completing" the input — the v5.0 prompt-injection mitigation.
"""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.membrane import (
    DeterministicParser,
    MembraneError,
    ParserAdapter,
    validate_membrane,
)


class Membrane:
    """L0 layer: parse + strict-validate the query into ``ctx.membrane``."""

    name: ClassVar[str] = "L0.MEMBRANE"

    def __init__(self, parser: ParserAdapter | None = None) -> None:
        self._parser: ParserAdapter = parser if parser is not None else DeterministicParser()

    def process(self, ctx: PipelineContext) -> PipelineContext:
        try:
            raw = self._parser.parse(ctx.query)
            output = validate_membrane(raw)
        except MembraneError as exc:
            ctx.record(self.name, note="schema-violation")
            ctx.halt(HaltReason.CLARIFICATION, str(exc))
            return ctx
        ctx.membrane = output.model_dump(by_alias=True, mode="json")
        ctx.record(self.name, note="parsed", question_type=output.question_type.value)
        return ctx
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/membrane/test_layer.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Run the existing pipeline-skeleton tests (regression)**

Run: `python -m pytest tests/test_pipeline_skeleton.py -v`
Expected: PASS — the apple query still runs through every layer without halting (it parses to a minimal membrane; `from` alias and `mode="json"` keep the dump JSON-clean).

- [ ] **Step 6: Commit**

```bash
git add dbse/layers/membrane.py tests/membrane/test_layer.py
git commit -m "feat(l0): wire MEMBRANE layer (parse, validate, halt on violation)"
```

---

## Task 5: The L0.5 STS classifier (`dbse/sts`)

**Files:**
- Create: `dbse/sts/__init__.py`
- Create: `dbse/sts/classifier.py`
- Create: `tests/sts/__init__.py`
- Test: `tests/sts/test_classifier.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sts/__init__.py` (empty file):

```python
```

Create `tests/sts/test_classifier.py`:

```python
"""L0.5 unit tests: the rule-based query classifier and routing."""

from __future__ import annotations

import pytest

from dbse.sts import ROUTES, QueryType, classify


def test_physics_compute_when_quantities_present() -> None:
    assert classify("the force on a 0.1 kg apple", has_quantities=True) is QueryType.PHYSICS_COMPUTE


def test_physics_compute_detects_inline_quantity_without_flag() -> None:
    # A bare number+unit in the text is enough.
    assert classify("how fast after 5 s") is QueryType.PHYSICS_COMPUTE


def test_math_prove() -> None:
    assert classify("prove that sqrt(2) is irrational") is QueryType.MATH_PROVE


def test_definition() -> None:
    assert classify("what is entropy") is QueryType.DEFINITION


def test_opinion() -> None:
    assert classify("what is the best programming language?") is QueryType.OPINION


def test_opinion_beats_definition_when_both_markers_present() -> None:
    # "what is" (definition) AND "best" (opinion) -> opinion wins (checked first).
    assert classify("what is the most beautiful equation?") is QueryType.OPINION


def test_ambiguous_when_no_signal() -> None:
    assert classify("apple") is QueryType.AMBIGUOUS


def test_routes_cover_every_query_type() -> None:
    assert set(ROUTES) == set(QueryType)
    assert ROUTES[QueryType.PHYSICS_COMPUTE] == "full_pipeline"
    assert ROUTES[QueryType.MATH_PROVE] == "nucleus_only"
    assert ROUTES[QueryType.DEFINITION] == "expression_only"
    assert ROUTES[QueryType.OPINION] == "unhandled"
    assert ROUTES[QueryType.AMBIGUOUS] == "model_lattice"


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("compute the force on a 2 kg mass", QueryType.PHYSICS_COMPUTE),
        ("prove the theorem", QueryType.MATH_PROVE),
        ("define momentum", QueryType.DEFINITION),
        ("which is the best phone", QueryType.OPINION),
        ("banana", QueryType.AMBIGUOUS),
    ],
)
def test_reference_queries_route_correctly(query: str, expected: QueryType) -> None:
    assert classify(query) is expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/sts/test_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dbse.sts'`.

- [ ] **Step 3: Write minimal implementation**

Create `dbse/sts/classifier.py`:

```python
"""L0.5 STS TYPING — rule-based query classification (no LLM).

Classification happens before any expensive analysis and decides the route:

| QueryType        | route             |
|------------------|-------------------|
| PHYSICS_COMPUTE  | full_pipeline     |
| MATH_PROVE       | nucleus_only      |
| DEFINITION       | expression_only   |
| OPINION          | unhandled         |
| AMBIGUOUS        | model_lattice     |

Markers are checked in a deliberate order: OPINION first (a subjective query that
also says "what is ..." is still an opinion), then DEFINITION, then MATH_PROVE,
then PHYSICS_COMPUTE (quantities present, by flag or inline), else AMBIGUOUS.
"""

from __future__ import annotations

import re
from enum import StrEnum

_OPINION_MARKERS = (
    "best", "worst", "most beautiful", "should i", "do you think", "favorite",
    "favourite", "лучш", "красив", "по-твоему", "стоит ли",
)
_DEFINITION_MARKERS = (
    "what is", "what are", "define", "definition", "что такое", "определени",
)
_PROVE_MARKERS = ("prove", "theorem", "докаж", "теорем")

# A number immediately followed by a letter-led unit token (inline quantity).
_INLINE_QUANTITY = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s*[A-Za-zµμΩ]")


class QueryType(StrEnum):
    """The five strict query categories from the v5.0 spec."""

    PHYSICS_COMPUTE = "PHYSICS_COMPUTE"
    MATH_PROVE = "MATH_PROVE"
    DEFINITION = "DEFINITION"
    OPINION = "OPINION"
    AMBIGUOUS = "AMBIGUOUS"


ROUTES: dict[QueryType, str] = {
    QueryType.PHYSICS_COMPUTE: "full_pipeline",
    QueryType.MATH_PROVE: "nucleus_only",
    QueryType.DEFINITION: "expression_only",
    QueryType.OPINION: "unhandled",
    QueryType.AMBIGUOUS: "model_lattice",
}


def classify(query: str, *, has_quantities: bool = False) -> QueryType:
    """Classify ``query`` into a :class:`QueryType`.

    ``has_quantities`` lets the L0.5 layer pass the result of the (already-run) L0
    parse; even without it, an inline ``number+unit`` in the text is enough to
    treat the query as a physics computation.
    """
    text = query.casefold()
    if any(m in text for m in _OPINION_MARKERS):
        return QueryType.OPINION
    if any(m in text for m in _DEFINITION_MARKERS):
        return QueryType.DEFINITION
    if any(m in text for m in _PROVE_MARKERS):
        return QueryType.MATH_PROVE
    if has_quantities or _INLINE_QUANTITY.search(query) is not None:
        return QueryType.PHYSICS_COMPUTE
    return QueryType.AMBIGUOUS
```

Create `dbse/sts/__init__.py`:

```python
"""L0.5 STS TYPING — rule-based query classification."""

from dbse.sts.classifier import ROUTES, QueryType, classify

__all__ = ["ROUTES", "QueryType", "classify"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/sts/test_classifier.py -v`
Expected: PASS (8 + 5 parametrized = 13 passed).

- [ ] **Step 5: Commit**

```bash
git add dbse/sts/__init__.py dbse/sts/classifier.py tests/sts/__init__.py tests/sts/test_classifier.py
git commit -m "feat(l0.5): rule-based STS query classifier and routing map"
```

---

## Task 6: Wire the STS TYPING layer

**Files:**
- Modify: `dbse/layers/sts_typing.py`
- Test: `tests/sts/test_layer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sts/test_layer.py`:

```python
"""L0.5 layer tests: classification wired into the pipeline context."""

from __future__ import annotations

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.membrane import Membrane
from dbse.layers.sts_typing import StsTyping


def _after_membrane(query: str) -> PipelineContext:
    return Membrane().process(PipelineContext(query=query))


def test_physics_query_sets_type_and_route_without_halting() -> None:
    ctx = StsTyping().process(_after_membrane("force on a 0.1 kg mass"))
    assert not ctx.halted
    assert ctx.sts_type == "PHYSICS_COMPUTE"
    route_entry = next(e for e in ctx.trace if e.layer == "L0.5.STS_TYPING")
    assert route_entry.payload["route"] == "full_pipeline"


def test_opinion_query_halts_unhandled() -> None:
    ctx = StsTyping().process(_after_membrane("what is the best language?"))
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.UNHANDLED
    assert ctx.sts_type == "OPINION"


def test_definition_query_sets_type_and_does_not_halt() -> None:
    ctx = StsTyping().process(_after_membrane("what is entropy"))
    assert not ctx.halted
    assert ctx.sts_type == "DEFINITION"


def test_uses_membrane_quantities_as_the_has_quantities_signal() -> None:
    # "mass 0.1 kg" parses to a quantity; classifier should see PHYSICS_COMPUTE.
    ctx = StsTyping().process(_after_membrane("mass 0.1 kg"))
    assert ctx.sts_type == "PHYSICS_COMPUTE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/sts/test_layer.py -v`
Expected: FAIL — the stub never sets `ctx.sts_type` (assertions fail).

- [ ] **Step 3: Write minimal implementation**

Replace the entire contents of `dbse/layers/sts_typing.py`:

```python
"""L0.5 STS TYPING — classify the query and decide the route.

Runs after L0 MEMBRANE. Stores the query type in ``ctx.sts_type`` and the route
in the trace payload. ``OPINION`` queries are out of scope and halt the pipeline
with ``UNHANDLED``; every other type is recorded and the conveyor continues
(real route-based skipping arrives with the downstream layers).
"""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.sts import ROUTES, QueryType, classify


class StsTyping:
    """L0.5 layer: rule-based query classification + routing."""

    name: ClassVar[str] = "L0.5.STS_TYPING"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        has_quantities = bool(ctx.membrane and ctx.membrane.get("quantities"))
        qtype = classify(ctx.query, has_quantities=has_quantities)
        ctx.sts_type = qtype.value
        ctx.record(self.name, note="classified", route=ROUTES[qtype])
        if qtype is QueryType.OPINION:
            ctx.halt(HaltReason.UNHANDLED, "Opinion queries are out of scope (L0.5).")
        return ctx
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/sts/test_layer.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Run the existing pipeline-skeleton tests (regression)**

Run: `python -m pytest tests/test_pipeline_skeleton.py -v`
Expected: PASS — the apple query still traverses all ten layers without halting (it is not an opinion query).

- [ ] **Step 6: Commit**

```bash
git add dbse/layers/sts_typing.py tests/sts/test_layer.py
git commit -m "feat(l0.5): wire STS TYPING layer (classify, route, halt on OPINION)"
```

---

## Task 7: Adversarial prompt-injection corpus (QA-gate level 5)

**Files:**
- Create: `tests/membrane/test_adversarial.py`

- [ ] **Step 1: Write the test**

Create `tests/membrane/test_adversarial.py`:

```python
"""L0 adversarial tests (QA-gate level 5): prompt-injection mitigation.

Each case simulates a compromised LLM emitting a payload that tries to escape the
sandbox. The strict schema must reject every one with MembraneError, and the layer
must turn that into a CLARIFICATION halt — never a silent "completion".
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.membrane import Membrane
from dbse.membrane import MembraneError, validate_membrane

_BASE: dict[str, Any] = {
    "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
    "quantities": [],
    "relations": [],
    "question_type": "compute",
    "target": {"ref": "obj_1", "property": "force"},
}

# Each payload is the base with one injection applied.
_ATTACKS: dict[str, dict[str, Any]] = {
    "forbidden_operator_node": {**_BASE, "operators": [{"op": "SUPPRESS", "arg": "friction"}]},
    "forbidden_invariant_node": {**_BASE, "invariants": [{"law": "g = -9.81"}]},
    "forbidden_context_node": {**_BASE, "context": {"assume": "no air"}},
    "question_type_command_injection": {**_BASE, "question_type": "compute; DROP friction"},
    "extra_field_on_target": {**_BASE, "target": {"ref": "obj_1", "property": "f", "x": 1}},
    "suppress_field_on_quantity": {
        **_BASE,
        "objects": [{"id": "obj_1", "type": "body", "label": "apple"}],
        "quantities": [
            {"ref": "obj_1", "property": "g", "value": -9.81, "unit": "m/s^2", "hidden": True},
        ],
    },
    "injected_unit_garbage": {
        **_BASE,
        "quantities": [{"ref": "obj_1", "property": "mass", "value": 1, "unit": "SUPPRESS"}],
    },
    "dangling_reference": {
        **_BASE,
        "quantities": [{"ref": "ghost", "property": "mass", "value": 1, "unit": "kg"}],
    },
}


@pytest.mark.parametrize("name", sorted(_ATTACKS))
def test_injection_payloads_are_rejected_by_schema(name: str) -> None:
    with pytest.raises(MembraneError):
        validate_membrane(_ATTACKS[name])


@pytest.mark.parametrize("name", sorted(_ATTACKS))
def test_injection_payloads_halt_the_layer_with_clarification(name: str) -> None:
    class Attacker:
        name: ClassVar[str] = "attacker"

        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def parse(self, query: str) -> dict[str, Any]:
            return self._payload

    ctx = Membrane(parser=Attacker(_ATTACKS[name])).process(PipelineContext(query="x"))
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.CLARIFICATION
    assert ctx.membrane is None
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/membrane/test_adversarial.py -v`
Expected: PASS (8 + 8 = 16 passed).

- [ ] **Step 3: Commit**

```bash
git add tests/membrane/test_adversarial.py
git commit -m "test(l0): adversarial prompt-injection corpus (forbidden nodes, refs, units)"
```

---

## Task 8: Parsing-accuracy corpus (QA-gate level 7, deterministic stand-in)

> Level 7 (LLM-eval of parsing accuracy) is a *soft* gate and ultimately needs a
> labeled set scored against a real LLM. Here we ship the labeled set and a
> **deterministic** accuracy check against the fallback parser (no network), so
> the corpus and the harness exist now; swapping in a real provider later is a
> drop-in via `ParserAdapter`.

**Files:**
- Create: `cases/parse/membrane_parse.jsonl`
- Create: `tests/membrane/test_parse_accuracy.py`

- [ ] **Step 1: Create the labeled corpus**

Create `cases/parse/membrane_parse.jsonl` (one JSON object per line; units chosen to resolve via L1):

```jsonl
{"query": "an apple of mass 0.1 kg", "expected_quantities": [[0.1, "kg"]], "question_type": "compute"}
{"query": "the Earth has mass 5.972e24 kg", "expected_quantities": [[5.972e24, "kg"]], "question_type": "compute"}
{"query": "gravity is 9.81 m/s^2", "expected_quantities": [[9.81, "m/s^2"]], "question_type": "compute"}
{"query": "a force of 10 N over a distance of 2 m", "expected_quantities": [[10.0, "N"], [2.0, "m"]], "question_type": "compute"}
{"query": "energy of 5 J released in 3 s", "expected_quantities": [[5.0, "J"], [3.0, "s"]], "question_type": "compute"}
{"query": "what is energy", "expected_quantities": [], "question_type": "explain"}
{"query": "prove that 2 is prime", "expected_quantities": [], "question_type": "prove"}
{"query": "a current of 2 A through 5 ohm", "expected_quantities": [[2.0, "A"], [5.0, "ohm"]], "question_type": "compute"}
```

- [ ] **Step 2: Write the test**

Create `tests/membrane/test_parse_accuracy.py`:

```python
"""L0 parsing-accuracy harness (QA-gate level 7, deterministic stand-in).

Scores the deterministic fallback parser against a labeled corpus. The corpus is
curated to live within the deterministic parser's capabilities, so this is a hard
assertion here; with a real LLM adapter the same harness becomes a soft gate.
"""

from __future__ import annotations

import json
from pathlib import Path

from dbse.membrane import DeterministicParser

_CORPUS = Path(__file__).resolve().parents[2] / "cases" / "parse" / "membrane_parse.jsonl"


def _load() -> list[dict]:
    lines = [ln for ln in _CORPUS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


def test_corpus_is_non_empty() -> None:
    assert len(_load()) >= 8


def test_quantity_extraction_is_exact_on_the_corpus() -> None:
    parser = DeterministicParser()
    for case in _load():
        raw = parser.parse(case["query"])
        got = sorted((q["value"], q["unit"]) for q in raw["quantities"])
        want = sorted((float(v), u) for v, u in case["expected_quantities"])
        assert got == want, f"quantities mismatch for {case['query']!r}: {got} != {want}"


def test_question_type_matches_the_corpus() -> None:
    parser = DeterministicParser()
    for case in _load():
        raw = parser.parse(case["query"])
        assert raw["question_type"] == case["question_type"], case["query"]
```

- [ ] **Step 3: Run test to verify it passes**

Run: `python -m pytest tests/membrane/test_parse_accuracy.py -v`
Expected: PASS (3 passed).

> If `test_quantity_extraction_is_exact_on_the_corpus` fails for a line, the corpus
> and parser disagree — fix the *corpus* line (only use units that resolve in
> `dbse/dimensional/units.py`) or the parser regex, not the assertion.

- [ ] **Step 4: Run the full suite + quality gate**

Run: `ruff check . ; mypy ; python -m pytest -q`
Expected: `All checks passed!`, `Success: no issues found`, all tests pass (Stages 0–2 + the new L0/L0.5 tests).

> If `ruff` flags the `_BASE`-spread dicts (`{**_BASE, ...}`) or the `dict` bare
> annotation in tests, add the precise type (`dict[str, Any]`) — the test bodies
> above already annotate them. If `mypy` flags `ctx.membrane.get(...)` in the STS
> layer, note `ctx.membrane` is `dict[str, Any] | None` and the `bool(ctx.membrane and ...)`
> short-circuit narrows it; keep that form.

- [ ] **Step 5: Commit**

```bash
git add cases/parse/membrane_parse.jsonl tests/membrane/test_parse_accuracy.py
git commit -m "test(l0): labeled parsing corpus + deterministic accuracy harness"
```

---

## Task 9: Update status docs

**Files:**
- Modify: `README.md` (Status section)
- Modify: `docs/spec-notes.md` (record Stage 3 decisions)

- [ ] **Step 1: Update README status**

In `README.md`, append to the "Статус" section:

```markdown
- Этап 3 — L0 MEMBRANE + L0.5 STS Typing: ✅ строгая Pydantic-схема выхода
  (`dbse/membrane/`, `extra="forbid"`, валидация ссылок и единиц через L1
  `parse_unit`), детерминированный fallback-парсер, провайдер-агностичный
  `ParserAdapter`; rule-based классификатор запросов (`dbse/sts/`). Слои
  `L0.MEMBRANE`/`L0.5.STS_TYPING` подключены: схема-violation → `CLARIFICATION`,
  `OPINION` → `UNHANDLED`. **Закрывает уязвимость №2 (Prompt Injection).**
```

- [ ] **Step 2: Record Stage 3 decisions in spec-notes**

In `docs/spec-notes.md`, add a new section after the L1.5 block:

```markdown
## L0 / L0.5 (Stage 3) — принятые решения
- **Pydantic v2** — первая runtime-зависимость (спека §2/§6 требует строгую
  Pydantic-схему). Добавлен `pydantic.mypy` plugin (strict mypy). До этого
  `dependencies = []`.
- **Схема — граница песочницы.** `extra="forbid"` на всех моделях ⇒ LLM не может
  сгенерировать `INVARIANT`/`CONTEXT`/`OPERATOR` или любое off-schema поле;
  `question_type` — закрытый enum; единицы валидируются через L1 `parse_unit`
  (переиспользование, не дублирование); ссылки (`ref`/`from`/`to`/`target.ref`)
  обязаны резолвиться в объявленный `OBJECT`. Любой выход за схему →
  `MembraneError` → слой `halt(CLARIFICATION)` (никакого «молчаливого
  дополнения»).
- **Детерминированный fallback-парсер** прогоняет все тесты (без сети/LLM).
  Реальный LLM-провайдер — вне Stage 3; зашит только seam `ParserAdapter` +
  детерминированная реализация. Парсер не бросает на обычном NL: вытаскивает
  `value+unit` (единицы — через L1), отбрасывает нерезолвимое, всегда отдаёт
  схема-валидный минимум (один `obj_1`).
- **Routing** (`dbse/sts/ROUTES`) пока только записывается в trace и обрабатывает
  `OPINION → UNHANDLED`; реальный пропуск слоёв по маршруту — позже (downstream-
  слои ещё заглушки). Порядок маркеров классификатора: OPINION → DEFINITION →
  MATH_PROVE → PHYSICS_COMPUTE → AMBIGUOUS.
- **Scope:** интеграция L1/L1.5 (навешивание `AffineType` на узлы AST) — Этап 4
  (RIBOSOME), не здесь. `dbse/layers/{dimensional,affine_types}.py` остаются
  pass-through. Кириллические единицы (`г`, `м`) пока не резолвятся в L1 — это
  существующий тех-долг L1, поэтому такие величины fallback-парсер отбрасывает.
- **QA-гейт:** уровни 1 (юнит: schema/adapter/layer/classifier), 5 (adversarial:
  prompt injection — `tests/membrane/test_adversarial.py`), 7 (parsing accuracy —
  детерминированный стенд `tests/membrane/test_parse_accuracy.py` + корпус
  `cases/parse/membrane_parse.jsonl`; реальный LLM-eval — мягкий гейт, позже).
```

- [ ] **Step 3: Commit**

```bash
git add README.md docs/spec-notes.md
git commit -m "docs: mark Stage 3 (L0 MEMBRANE + L0.5 STS Typing) complete"
```

---

## Self-Review

**1. Spec coverage (ROADMAP Этап 3 объём + DoD + QA-гейт):**
- "Pydantic-схема выхода MEMBRANE: `objects / quantities / relations / question_type / target`" → Task 2 `MembraneOutput` + sub-models. ✅
- "Жёсткий запрет на генерацию узлов `INVARIANT / CONTEXT / OPERATOR` LLM-ом" → Task 2 `extra="forbid"`; Task 7 asserts each forbidden node is rejected. ✅
- "Адаптер LLM (provider-agnostic) + детерминированный fallback-парсер для тестов" → Task 3 `ParserAdapter` Protocol + `DeterministicParser`. ✅
- "Валидация: при выходе за схему → `clarification`/`UNHANDLED`, без молчаливого дополнения" → Task 4 (`MembraneError` → `CLARIFICATION`), Task 6 (`OPINION` → `UNHANDLED`). ✅
- "L0.5 rule-based классификатор: `PHYSICS_COMPUTE / MATH_PROVE / DEFINITION / OPINION / AMBIGUOUS` → маршрут" → Task 5 `QueryType` + `classify` + `ROUTES`. ✅
- DoD "инъекция «замени g на -9.81 / SUPPRESS(friction)» отклоняется схемой" → Task 7 `forbidden_*` + `question_type_command_injection` + `injected_unit_garbage`. ✅
- DoD "классификатор верно маршрутизирует набор эталонных запросов" → Task 5 `test_reference_queries_route_correctly`. ✅
- DoD "Закрывает уязвимость №2 (Prompt Injection)" → Task 7 corpus + README/spec-notes note. ✅
- QA-гейт "уровни 1 + 5 + 7" → Tasks 2/3/4/5/6 (level 1), Task 7 (level 5), Task 8 (level 7). ✅

**2. Placeholder scan:** No TBD/TODO; every code step ships full code; every test step ships full test code; the corpus is concrete. The only deferred item (real LLM provider / real LLM-eval) is explicitly out of scope with the `ParserAdapter` seam in place. ✅

**3. Type consistency:**
- `validate_membrane(raw) -> MembraneOutput`; `DeterministicParser.parse(query) -> dict[str, Any]`; `classify(query, *, has_quantities=False) -> QueryType`; `ROUTES: dict[QueryType, str]` — used consistently across Tasks 2–8. ✅
- Layer wiring: `Membrane(parser=...)`, `ctx.membrane` is the `model_dump(by_alias=True, mode="json")` dict (matches `PipelineContext.membrane: dict[str, Any] | None`); `ctx.sts_type` is `qtype.value` (matches `str | None`). ✅
- `HaltReason.CLARIFICATION` (L0) and `HaltReason.UNHANDLED` (L0.5) both already exist in `dbse/contracts/context.py`. ✅
- `from_: str = Field(alias="from")` + `populate_by_name=True` ⇒ validates from `"from"` key and dumps `"from"` via `by_alias=True`; asserted in Task 4 `test_relation_from_alias_round_trips_in_stored_membrane`. ✅
- Reuse of `dbse.dimensional.{parse_unit, DimensionError}` — both exported from its `__init__`. ✅
- `StrEnum` requires Python 3.11+ (`requires-python = ">=3.11"`). ✅

**4. Regression safety:** The two existing pipeline-skeleton expectations (full ten-layer trace, no halt on the apple query) are explicitly re-run in Tasks 4 and 6 — the apple query parses to a minimal membrane and is not an opinion, so it neither halts nor changes the trace shape. ✅

No gaps found.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-l0-membrane-l0_5-sts-typing.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session with checkpoints for review.

Which approach?
