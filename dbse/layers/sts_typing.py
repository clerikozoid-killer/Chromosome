"""L0.5 STS TYPING — rule-based query classifier. Stub; logic in Stage 3."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class StsTyping(PassThroughLayer):
    name: ClassVar[str] = "L0.5.STS_TYPING"
