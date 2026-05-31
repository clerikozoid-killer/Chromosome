"""L6 template registry tests."""

from __future__ import annotations

from dbse.narrative.models import NarrativeNode
from dbse.narrative.templates import template_for_quantity


def test_force_template_forbids_anthropomorphic_metaphors() -> None:
    spec = template_for_quantity("force")
    assert "хочет" in spec.forbidden_metaphors
    assert "действует" in spec.allowed_verbs
    assert "{value}" in spec.template


def test_narrative_node_to_dict() -> None:
    spec = template_for_quantity("mass")
    node = NarrativeNode(
        node_id="q_mass_0",
        template=spec.template,
        bindings={"property": "mass", "value": "0.100", "unit": "kg"},
        allowed_verbs=spec.allowed_verbs,
        forbidden_metaphors=spec.forbidden_metaphors,
    )
    d = node.to_dict()
    assert d["node_id"] == "q_mass_0"
    assert d["bindings"]["unit"] == "kg"


def test_unknown_property_gets_fallback_template() -> None:
    spec = template_for_quantity("velocity")
    assert "{property}" in spec.template
