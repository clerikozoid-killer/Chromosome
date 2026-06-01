"""L0 parser adapters.

``ParserAdapter`` is the provider-agnostic seam: a real LLM provider plugs in here
later. ``DeterministicParser`` is the network-free fallback used for tests and
non-standard input — it extracts ``value+unit`` pairs (validated through the L1
unit parser), infers a coarse ``question_type``, and emits a schema-valid payload.
It can only ever produce the allowed node kinds, so it is injection-safe by
construction.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, Protocol, runtime_checkable

from dbse.dimensional import DimensionError, parse_unit

# A number (int / float / scientific) followed by a unit token (Latin or Cyrillic).
_NUMBER_UNIT = re.compile(
    r"(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
    r"(?P<unit>[A-Za-zµμΩ\u0430-\u044f\u0410-\u042f]+"
    r"(?:\^-?\d+)?(?:[*/][A-Za-zµμΩ\u0430-\u044f\u0410-\u042f]+(?:\^-?\d+)?)*)"
)

# question_type markers, checked in this order.
_PROVE_MARKERS = ("prove", "theorem", "докаж", "теорем")
_EXPLAIN_MARKERS = ("what is", "what are", "define", "definition", "что такое", "определени")

# property stems → canonical property (EN + RU), matched against the words just
# before a number.
_PROPERTY_STEMS: tuple[tuple[str, str], ...] = (
    ("mass", "mass"),
    ("масс", "mass"),
    ("distance", "distance"),
    ("расстояни", "distance"),
    ("velocit", "velocity"),
    ("speed", "velocity"),
    ("скорост", "velocity"),
    ("force", "force"),
    ("сил", "force"),
    ("energy", "energy"),
    ("энерг", "energy"),
    ("time", "time"),
    ("врем", "time"),
)

_OBJECT: dict[str, str] = {"id": "obj_1", "type": "system", "label": "query"}

# Cyrillic unit tokens → Latin (longest match first).
_CYRILLIC_UNIT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("кг/с", "kg/s"),
    ("кг", "kg"),
    ("м/с²", "m/s^2"),
    ("м/с^2", "m/s^2"),
    ("м/с", "m/s"),
    ("г/с", "g/s"),
    ("г", "g"),
    ("м", "m"),
    ("с", "s"),
    ("Н", "N"),
    ("Дж", "J"),
)


def _latin_unit(unit: str) -> str:
    out = unit
    for src, dst in _CYRILLIC_UNIT_REPLACEMENTS:
        out = out.replace(src, dst)
    return out


@runtime_checkable
class ParserAdapter(Protocol):
    """A parser that turns a raw query into an (unvalidated) membrane payload."""

    name: ClassVar[str]

    def parse(self, query: str) -> dict[str, Any]:
        """Return a dict to be validated by :func:`validate_membrane`."""
        ...


class DeterministicParser:
    """Rule-based, network-free fallback parser."""

    name: ClassVar[str] = "deterministic"

    def parse(self, query: str) -> dict[str, Any]:
        text = query.casefold()
        quantities = self._extract_quantities(query, text)
        return {
            "objects": [dict(_OBJECT)],
            "quantities": quantities,
            "relations": [],
            "question_type": self._question_type(text),
            "target": {"ref": "obj_1", "property": self._target_property(text)},
        }

    def _extract_quantities(self, query: str, text: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for match in _NUMBER_UNIT.finditer(query):
            unit = _latin_unit(match.group("unit"))
            try:
                parse_unit(unit)
            except DimensionError:
                continue  # unit does not resolve in L1 — drop the pair
            out.append(
                {
                    "ref": "obj_1",
                    "property": self._property_before(text, match.start()),
                    "value": float(match.group("value")),
                    "unit": unit,
                }
            )
        return out

    @staticmethod
    def _property_before(text: str, index: int) -> str:
        window = text[max(0, index - 24) : index]
        for stem, prop in _PROPERTY_STEMS:
            if stem in window:
                return prop
        return "value"

    @staticmethod
    def _question_type(text: str) -> str:
        if any(m in text for m in _EXPLAIN_MARKERS):
            return "explain"
        if any(m in text for m in _PROVE_MARKERS):
            return "prove"
        return "compute"

    @staticmethod
    def _target_property(text: str) -> str:
        # Questions asking for force/weight (RU+EN) even when mass is also mentioned.
        if any(
            marker in text
            for marker in ("силой", "сила", " force", "force ", "weight", "вес")
        ):
            return "force"
        for stem, prop in _PROPERTY_STEMS:
            if stem in text:
                return prop
        return "value"
