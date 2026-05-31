"""Build a ModelLattice from query text."""

from __future__ import annotations

from dbse.lattice.catalog import CANDIDATES
from dbse.lattice.entropy import ambiguity_temperature
from dbse.lattice.models import ModelLattice, ModelNode


def _likelihood(query: str, keywords: tuple[str, ...]) -> float:
    q = query.casefold()
    score = 1.0
    for kw in keywords:
        if kw in q:
            score += 2.0
    return score


def build_lattice(
    query: str,
    *,
    sts_type: str | None = None,
    domain_hint: str = "",
) -> ModelLattice:
    nodes: list[ModelNode] = []
    for spec in CANDIDATES:
        like = _likelihood(query, spec.keywords)
        if sts_type == "PHYSICS_COMPUTE" and domain_hint:
            if spec.model_id != "classical_gravitation":
                like *= 0.05
            else:
                like *= 5.0
        nodes.append(
            ModelNode(
                model_id=spec.model_id,
                prior=spec.prior,
                likelihood=like,
                posterior=0.0,
                clarification=spec.clarification,
            )
        )
    total = sum(n.prior * n.likelihood for n in nodes) or 1.0
    normed: list[ModelNode] = []
    for n in nodes:
        post = (n.prior * n.likelihood) / total
        normed.append(
            ModelNode(
                model_id=n.model_id,
                prior=n.prior,
                likelihood=n.likelihood,
                posterior=post,
                clarification=n.clarification,
            )
        )
    dominant = max(normed, key=lambda x: x.posterior)
    lat = ModelLattice(
        nodes=tuple(normed),
        total_entropy=0.0,
        dominant_model=dominant,
        ambiguity_temperature=0.0,
    )
    t = ambiguity_temperature(lat)
    return ModelLattice(
        nodes=tuple(normed),
        total_entropy=t,
        dominant_model=dominant,
        ambiguity_temperature=t,
    )
