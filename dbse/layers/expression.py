"""L7 EXPRESSION GENES — constrained LLM styling. Stub; logic in Stage 10."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class Expression(PassThroughLayer):
    name: ClassVar[str] = "L7.EXPRESSION"
