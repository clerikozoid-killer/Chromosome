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
