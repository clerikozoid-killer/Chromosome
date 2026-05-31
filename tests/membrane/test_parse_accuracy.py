"""L0 parsing-accuracy harness (QA-gate level 7, deterministic stand-in).

Scores the deterministic fallback parser against a labeled corpus. The corpus is
curated to live within the deterministic parser's capabilities, so this is a hard
assertion here; with a real LLM adapter the same harness becomes a soft gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dbse.membrane import DeterministicParser

_CORPUS = Path(__file__).resolve().parents[2] / "cases" / "parse" / "membrane_parse.jsonl"


def _load() -> list[dict[str, Any]]:
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
