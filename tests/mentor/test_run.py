"""Mentor batch run tests."""

from __future__ import annotations

from pathlib import Path

from dbse.mentor.run import run_cases


def test_run_cases_writes_verdict_file(tmp_path: Path) -> None:
    cases_dir = Path("cases")
    verdicts_dir = tmp_path / "verdicts"
    verdicts = run_cases(cases_dir, verdicts_dir)
    assert len(verdicts) >= 1
    apple = next(v for v in verdicts if v.case_id == "apple_weight")
    assert apple.passed
    files = list(verdicts_dir.glob("*.jsonl"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "apple_weight" in content
