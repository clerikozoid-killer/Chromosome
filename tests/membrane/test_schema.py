"""L0 unit tests: the MEMBRANE output schema and MembraneError."""

from __future__ import annotations

from typing import Any

import pytest

from dbse.membrane import MembraneError


def test_membrane_error_is_a_value_error() -> None:
    assert issubclass(MembraneError, ValueError)
    with pytest.raises(MembraneError):
        raise MembraneError("boom")


from dbse.membrane import (
    MembraneOutput,
    QuestionType,
    validate_membrane,
)

_VALID: dict[str, Any] = {
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
