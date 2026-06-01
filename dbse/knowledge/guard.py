"""Guard Core axioms against CRISPR-style hypothesis/constraint attacks."""

from __future__ import annotations

import re

from dbse.knowledge.core import CORE
from dbse.knowledge.errors import CoreViolationError

_CRISPR = re.compile(r"F\s*=\s*m\s*\*\s*a\s*(?:\^|\*\*)?\s*2", re.I)


def assert_no_core_violation(text: str) -> None:
    compact = text.replace(" ", "")
    if _CRISPR.search(compact):
        raise CoreViolationError("Hypothesis contradicts newton_2 Core axiom")
    lowered = text.casefold()
    if "contradict" in lowered:
        for ax in CORE.axioms.values():
            ax_compact = ax.statement.replace(" ", "").casefold()
            if ax_compact in lowered.replace(" ", ""):
                raise CoreViolationError(f"Explicit contradiction of {ax.statement}")
