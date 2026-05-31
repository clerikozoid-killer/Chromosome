"""Entropy and ambiguity temperature for ModelLattice."""

from __future__ import annotations

import math

from dbse.lattice.models import ModelLattice


def shannon_entropy(lattice: ModelLattice) -> float:
    h = 0.0
    for node in lattice.nodes:
        p = node.posterior
        if p > 0.0:
            h -= p * math.log(p)
    return h


def ambiguity_temperature(lattice: ModelLattice) -> float:
    n = len(lattice.nodes)
    if n <= 1:
        return 0.0
    h = shannon_entropy(lattice)
    denom = math.log(n)
    if denom == 0.0:
        return 0.0
    return h / denom
