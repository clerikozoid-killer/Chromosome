"""L2 CONTEXT MODEL LATTICE — P(Model | Context), T_ambig."""

from __future__ import annotations

from typing import Any, ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.lattice.classify import build_lattice
from dbse.lattice.models import ModelLattice as LatticeResult


def _lattice_to_dict(lat: LatticeResult) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "model_id": n.model_id,
                "prior": n.prior,
                "likelihood": n.likelihood,
                "posterior": n.posterior,
                "clarification": n.clarification,
            }
            for n in lat.nodes
        ],
        "total_entropy": lat.total_entropy,
        "dominant_model": lat.dominant_model.model_id,
        "ambiguity_temperature": lat.ambiguity_temperature,
        "candidates": [
            {
                "model": n.model_id,
                "probability": n.posterior,
                "clarification": n.clarification,
            }
            for n in sorted(lat.nodes, key=lambda x: -x.posterior)
        ],
    }


class ModelLattice:
    """L2 layer: context disambiguation via model lattice + T_ambig."""

    name: ClassVar[str] = "L2.MODEL_LATTICE"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        domain_hint = str(ctx.config.get("domain_hint", ""))
        lat = build_lattice(
            ctx.query,
            sts_type=ctx.sts_type,
            domain_hint=domain_hint,
        )
        ctx.model_lattice = _lattice_to_dict(lat)
        t = lat.ambiguity_temperature
        dominant = lat.dominant_model.model_id
        ctx.record(
            self.name,
            note="lattice-built",
            ambiguity_temperature=t,
            dominant_model=dominant,
        )

        if t >= 0.6:
            top = sorted(lat.nodes, key=lambda n: -n.posterior)[:3]
            parts = [
                f"{n.model_id} ({n.posterior:.0%}): {n.clarification}"
                for n in top
                if n.clarification
            ]
            msg = "Недостаточно контекста. Возможные интерпретации: " + "; ".join(parts)
            ctx.halt(HaltReason.AMBIGUITY_HALT, msg)
            ctx.record(self.name, note="ambiguity-halt", temperature=t)
            return ctx

        if t >= 0.3:
            top2 = sorted(lat.nodes, key=lambda n: -n.posterior)[:2]
            ctx.record(
                self.name,
                note="top-2-candidates",
                candidates=[n.model_id for n in top2],
                probabilities=[n.posterior for n in top2],
            )

        return ctx
