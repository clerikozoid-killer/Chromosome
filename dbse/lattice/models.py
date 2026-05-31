"""L2 Model Lattice data structures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelNode:
    model_id: str
    prior: float
    likelihood: float
    posterior: float
    clarification: str = ""


@dataclass(frozen=True, slots=True)
class ModelLattice:
    nodes: tuple[ModelNode, ...]
    total_entropy: float
    dominant_model: ModelNode
    ambiguity_temperature: float  # T_ambig in [0, 1]
