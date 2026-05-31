"""L6 SEMANTIC NARRATIVE GRAPH — deterministic text skeleton. Stub; logic in Stage 9."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class NarrativeGraph(PassThroughLayer):
    name: ClassVar[str] = "L6.NARRATIVE"
