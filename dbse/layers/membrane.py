"""L0 MEMBRANE — LLM parser (sandbox). Stub for Stage 0; logic in Stage 3."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class Membrane(PassThroughLayer):
    name: ClassVar[str] = "L0.MEMBRANE"
