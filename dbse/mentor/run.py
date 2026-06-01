"""Batch-run case bank and write verdict JSONL."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from dbse.mentor.cases import load_cases
from dbse.mentor.verdict import Verdict, judge
from dbse.pipeline import Pipeline


def run_cases(cases_dir: Path, verdicts_dir: Path) -> list[Verdict]:
    pipeline = Pipeline()
    verdicts: list[Verdict] = []
    for path in sorted(cases_dir.rglob("**/*.jsonl")):
        if "parse" in path.parts:
            continue
        for case in load_cases(path):
            config: dict[str, str] = {}
            if case.domain_hint:
                config["domain_hint"] = case.domain_hint
            ctx = pipeline.run(case.query, config=config)
            verdicts.append(judge(ctx, case))
    out = verdicts_dir / f"{date.today().isoformat()}.jsonl"
    verdicts_dir.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for verdict in verdicts:
            handle.write(
                json.dumps(
                    {
                        "case_id": verdict.case_id,
                        "passed": verdict.passed,
                        "category": verdict.category,
                        "detail": verdict.detail,
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
    return verdicts
