"""L3 RIBOSOME — AST compiler + canonical hash + cache. Stub; logic in Stage 4."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class Ribosome(PassThroughLayer):
    name: ClassVar[str] = "L3.RIBOSOME"
