"""Map PipelineContext to API response dicts (spec §5)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from dbse.contracts.context import PipelineContext
from dbse.contracts.proof import ProofLevel


def _ts() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _proof_level_str(level: ProofLevel | str) -> str:
    if isinstance(level, ProofLevel):
        return level.name
    return str(level)


def context_to_solve_response(ctx: PipelineContext, *, request_id: str) -> dict[str, Any]:
    proof = ctx.proof
    return {
        "request_id": request_id,
        "timestamp": _ts(),
        "model_lattice": ctx.model_lattice,
        "solution": ctx.solution,
        "proof": None
        if proof is None
        else {
            "level": _proof_level_str(proof.level),
            "tinfo": proof.tinfo,
            "confidence": proof.confidence,
            "solver_path": proof.solver_path,
            "violations": [
                {
                    "invariant": v.invariant,
                    "time": v.time,
                    "value": v.value,
                }
                for v in proof.violations
            ],
        },
        "expression": ctx.expression,
        "visualizations": ctx.config.get("_visualizations"),
        "halted": ctx.halted,
        "halt_reason": ctx.halt_reason.value,
    }


def context_to_clarify_response(ctx: PipelineContext) -> dict[str, Any]:
    lattice = ctx.model_lattice or {}
    return {
        "status": "clarification_needed",
        "ambiguity_temperature": lattice.get("ambiguity_temperature", 1.0),
        "candidates": lattice.get("candidates", []),
    }
