from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TemplateSpec:
    template: str
    allowed_verbs: tuple[str, ...]
    forbidden_metaphors: tuple[str, ...]


_QUANTITY: dict[str, TemplateSpec] = {
    "force": TemplateSpec(
        "Гравитационная сила {value} {unit} действует на тело массой {mass}.",
        ("действует", "составляет"),
        ("хочет", "пытается", "любит", "стремится"),
    ),
    "mass": TemplateSpec(
        "Масса тела {value} {unit}.",
        ("равна", "составляет"),
        ("хочет", "тяжелеет от желания"),
    ),
}


def template_for_quantity(property_name: str) -> TemplateSpec:
    return _QUANTITY.get(
        property_name,
        TemplateSpec(
            "{property} = {value} {unit}",
            ("равно",),
            ("хочет",),
        ),
    )
