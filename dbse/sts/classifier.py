"""L0.5 STS TYPING — rule-based query classification (no LLM).

Classification happens before any expensive analysis and decides the route:

| QueryType        | route             |
|------------------|-------------------|
| PHYSICS_COMPUTE  | full_pipeline     |
| MATH_PROVE       | nucleus_only      |
| DEFINITION       | expression_only   |
| OPINION          | unhandled         |
| AMBIGUOUS        | model_lattice     |

Markers are checked in a deliberate order: OPINION first (a subjective query that
also says "what is ..." is still an opinion), then DEFINITION, then MATH_PROVE,
then PHYSICS_COMPUTE (quantities present, by flag or inline), else AMBIGUOUS.
"""

from __future__ import annotations

import re
from enum import StrEnum

_OPINION_MARKERS = (
    "best", "worst", "most beautiful", "should i", "do you think", "favorite",
    "favourite", "лучш", "красив", "по-твоему", "стоит ли",
)
_DEFINITION_MARKERS = (
    "what is", "what are", "define", "definition", "что такое", "определени",
)
_PROVE_MARKERS = ("prove", "theorem", "докаж", "теорем")

# A number immediately followed by a letter-led unit token (inline quantity).
_INLINE_QUANTITY = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s*[A-Za-zµμΩ]")


class QueryType(StrEnum):
    """The five strict query categories from the v5.0 spec."""

    PHYSICS_COMPUTE = "PHYSICS_COMPUTE"
    MATH_PROVE = "MATH_PROVE"
    DEFINITION = "DEFINITION"
    OPINION = "OPINION"
    AMBIGUOUS = "AMBIGUOUS"


ROUTES: dict[QueryType, str] = {
    QueryType.PHYSICS_COMPUTE: "full_pipeline",
    QueryType.MATH_PROVE: "nucleus_only",
    QueryType.DEFINITION: "expression_only",
    QueryType.OPINION: "unhandled",
    QueryType.AMBIGUOUS: "model_lattice",
}


def classify(query: str, *, has_quantities: bool = False) -> QueryType:
    """Classify ``query`` into a :class:`QueryType`.

    ``has_quantities`` lets the L0.5 layer pass the result of the (already-run) L0
    parse; even without it, an inline ``number+unit`` in the text is enough to
    treat the query as a physics computation.
    """
    text = query.casefold()
    if any(m in text for m in _OPINION_MARKERS):
        return QueryType.OPINION
    if any(m in text for m in _DEFINITION_MARKERS):
        return QueryType.DEFINITION
    if any(m in text for m in _PROVE_MARKERS):
        return QueryType.MATH_PROVE
    if has_quantities or _INLINE_QUANTITY.search(query) is not None:
        return QueryType.PHYSICS_COMPUTE
    return QueryType.AMBIGUOUS
