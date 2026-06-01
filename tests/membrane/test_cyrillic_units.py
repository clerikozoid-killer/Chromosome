"""L0 parser: Cyrillic SI unit aliases."""

from __future__ import annotations

from dbse.membrane import DeterministicParser


def test_cyrillic_gram_parsed_as_mass() -> None:
    raw = DeterministicParser().parse("масса 100г")
    assert len(raw["quantities"]) == 1
    assert raw["quantities"][0]["unit"] == "g"
    assert raw["quantities"][0]["value"] == 100.0
