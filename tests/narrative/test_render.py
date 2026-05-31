"""L6 render tests."""

from __future__ import annotations

from dbse.narrative.models import NarrativeGraph, NarrativeNode
from dbse.narrative.render import to_text
from dbse.narrative.templates import template_for_quantity


def test_to_text_renders_force_without_forbidden_words() -> None:
    spec = template_for_quantity("force")
    node = NarrativeNode(
        node_id="q_force_0",
        template=spec.template,
        bindings={"value": "0.981", "unit": "N", "mass": "0.1 kg", "property": "force"},
        allowed_verbs=spec.allowed_verbs,
        forbidden_metaphors=spec.forbidden_metaphors,
    )
    graph = NarrativeGraph(nodes=(node,))
    text = to_text(graph)
    assert "Гравитационная сила" in text
    assert "0.981" in text
    for bad in spec.forbidden_metaphors:
        assert bad not in text


def test_to_text_joins_multiple_nodes() -> None:
    mass_spec = template_for_quantity("mass")
    force_spec = template_for_quantity("force")
    nodes = (
        NarrativeNode(
            "q_mass_0",
            mass_spec.template,
            {"property": "mass", "value": "0.100", "unit": "kg", "mass": ""},
            mass_spec.allowed_verbs,
            mass_spec.forbidden_metaphors,
        ),
        NarrativeNode(
            "q_force_1",
            force_spec.template,
            {"property": "force", "value": "0.981", "unit": "N", "mass": "0.1 kg"},
            force_spec.allowed_verbs,
            force_spec.forbidden_metaphors,
        ),
    )
    text = to_text(NarrativeGraph(nodes=nodes))
    assert "Масса тела" in text
    assert "Гравитационная сила" in text
