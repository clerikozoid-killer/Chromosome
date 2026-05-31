"""The object that flows through every layer of the pipeline.

Each layer reads from and writes to a :class:`PipelineContext`, never mutating
upstream inputs destructively beyond its own slot. A layer may set ``halted`` to
stop the conveyor early (Early Pruning) — e.g. on dimensional error, semantic
mismatch, prompt injection, or high ambiguity temperature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from dbse.contracts.ast import AST
from dbse.contracts.proof import Proof


class HaltReason(Enum):
    """Why the pipeline stopped before producing a full answer."""

    NONE = "none"
    UNHANDLED = "unhandled"                 # L0.5: out of scope (e.g. OPINION)
    CLARIFICATION = "clarification"         # L0: failed schema / needs user input
    DIMENSION_ERROR = "dimension_error"     # L1
    SEMANTIC_MISMATCH = "semantic_mismatch"  # L1.5
    AMBIGUITY_HALT = "ambiguity_halt"       # L2: T_ambig too high
    MODEL_BREAKDOWN = "model_breakdown"     # L5: invariant violated
    CORE_VIOLATION = "core_violation"       # L11: attempt to mutate Core


@dataclass(slots=True)
class TraceEntry:
    """One record of a layer having processed the context."""

    layer: str
    note: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineContext:
    """Mutable carrier threaded through all layers L0..L7."""

    query: str
    config: dict[str, Any] = field(default_factory=dict)

    # Per-stage outputs (filled progressively; ``None`` until the owning layer runs).
    membrane: dict[str, Any] | None = None       # L0
    sts_type: str | None = None                  # L0.5
    ast: AST | None = None                        # L3
    model_lattice: dict[str, Any] | None = None  # L2
    solution: dict[str, Any] | None = None       # L5
    proof: Proof | None = None                   # L5
    narrative: dict[str, Any] | None = None      # L6
    expression: dict[str, Any] | None = None     # L7

    # Control flow.
    halted: bool = False
    halt_reason: HaltReason = HaltReason.NONE
    halt_message: str = ""

    # Observability: ordered record of which layers touched the context.
    trace: list[TraceEntry] = field(default_factory=list)

    def record(self, layer: str, note: str = "", **payload: Any) -> None:
        """Append a trace entry for ``layer``."""
        self.trace.append(TraceEntry(layer=layer, note=note, payload=dict(payload)))

    def halt(self, reason: HaltReason, message: str = "") -> None:
        """Stop the pipeline early with a structured reason."""
        self.halted = True
        self.halt_reason = reason
        self.halt_message = message
