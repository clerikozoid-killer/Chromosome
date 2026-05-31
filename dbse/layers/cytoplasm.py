"""L4 CYTOPLASM — epigenetics + domain plugins. Stub; logic in Stage 5."""

from __future__ import annotations

from typing import ClassVar

from dbse.layers.base import PassThroughLayer


class Cytoplasm(PassThroughLayer):
    name: ClassVar[str] = "L4.CYTOPLASM"
