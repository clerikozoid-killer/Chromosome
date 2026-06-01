"""Mentor case loader tests."""

from __future__ import annotations

from pathlib import Path

from dbse.mentor.cases import load_cases

CASES_FILE = Path("cases/physics/apple_weight.jsonl")


def test_load_cases_reads_seed_corpus() -> None:
    cases = load_cases(CASES_FILE)
    assert len(cases) >= 1
    apple = next(c for c in cases if c.id == "apple_weight")
    assert apple.domain_hint == "classical_mechanics"
    assert apple.expected["unit"] == "N"
