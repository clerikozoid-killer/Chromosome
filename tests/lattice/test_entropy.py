"""L2 entropy tests."""

from __future__ import annotations

import pytest

from dbse.lattice.entropy import ambiguity_temperature
from dbse.lattice.models import ModelLattice, ModelNode


def _lat(posts: list[float]) -> ModelLattice:
    nodes = tuple(
        ModelNode(f"m{i}", 1.0, 1.0, p, "") for i, p in enumerate(posts)
    )
    dom = max(nodes, key=lambda n: n.posterior)
    base = ModelLattice(
        nodes=nodes, total_entropy=0.0, dominant_model=dom, ambiguity_temperature=0.0
    )
    t = ambiguity_temperature(base)
    return ModelLattice(nodes=nodes, total_entropy=t, dominant_model=dom, ambiguity_temperature=t)


def test_uniform_distribution_max_temperature() -> None:
    lat = _lat([0.25, 0.25, 0.25, 0.25])
    assert lat.ambiguity_temperature == pytest.approx(1.0, rel=1e-6)


def test_dominant_model_low_temperature() -> None:
    lat = _lat([0.97, 0.01, 0.01, 0.01])
    assert lat.ambiguity_temperature < 0.3
