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


class LinearOde1(BaseModel):
    """First-order linear ODE: d(state)/dt = constant + linear_coeff * state."""

    model_config = _STRICT

    object_ref: str
    state: str
    constant: float = 0.0
    linear_coeff: float = 0.0


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
    equations: list[LinearOde1] = Field(default_factory=list)
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
        for eq in self.equations:
            if eq.object_ref not in known:
                dangling.append(eq.object_ref)
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
