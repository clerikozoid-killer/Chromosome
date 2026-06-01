"""CLI entry point: dbse-mentor."""

from __future__ import annotations

import argparse
from pathlib import Path

from dbse.mentor.run import run_cases


def main() -> None:
    parser = argparse.ArgumentParser(prog="dbse-mentor")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_parser = sub.add_parser("run", help="Run case bank")
    run_parser.add_argument("--cases", type=Path, default=Path("cases"))
    run_parser.add_argument("--verdicts", type=Path, default=Path("verdicts"))
    args = parser.parse_args()
    if args.cmd == "run":
        verdicts = run_cases(args.cases, args.verdicts)
        passed = sum(1 for verdict in verdicts if verdict.passed)
        print(f"{passed}/{len(verdicts)} passed")


if __name__ == "__main__":
    main()
