"""Judge pipeline results against case expectations."""

from __future__ import annotations

from dataclasses import dataclass

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.contracts.proof import ProofLevel
from dbse.mentor.cases import Case


@dataclass(frozen=True, slots=True)
class Verdict:
    case_id: str
    passed: bool
    category: str
    detail: str


def _proof_level_str(level: ProofLevel | str) -> str:
    if isinstance(level, ProofLevel):
        return level.name
    return str(level)


def judge(ctx: PipelineContext, case: Case) -> Verdict:
    if ctx.halt_reason is HaltReason.AMBIGUITY_HALT:
        return Verdict(case.id, False, "ambiguity", "unexpected ambiguity halt")
    if ctx.halt_reason is HaltReason.CLARIFICATION:
        return Verdict(case.id, False, "parse", ctx.halt_message)
    if case.oracle == "metamorphic":
        if ctx.halted and ctx.halt_reason is not HaltReason.NONE:
            return Verdict(
                case.id,
                False,
                "solver",
                f"unexpected halt: {ctx.halt_reason.value}",
            )
        return Verdict(case.id, True, "ok", "metamorphic pipeline smoke")
    if ctx.solution is None:
        return Verdict(case.id, False, "solver", "no solution")
    exp = case.expected
    if "value" in exp:
        val = float(ctx.solution.get("value", 0))
        tol = float(exp.get("tolerance", 1e-6))
        if abs(val - float(exp["value"])) > tol:
            return Verdict(case.id, False, "solver", f"value {val} != {exp['value']}")
    if "unit" in exp and str(ctx.solution.get("unit", "")) != str(exp["unit"]):
        return Verdict(
            case.id,
            False,
            "solver",
            f"unit {ctx.solution.get('unit')!r} != {exp['unit']!r}",
        )
    if ctx.proof and case.proof_level:
        lvl = _proof_level_str(ctx.proof.level)
        if lvl != case.proof_level and case.proof_level != "P2":
            return Verdict(case.id, False, "solver", f"proof {lvl}")
    return Verdict(case.id, True, "ok", "passed")
