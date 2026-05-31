"""L1.5 operators over affine types.

A tiny enum shared by the compatibility checker now and by the L3 AST compiler
(Stage 4) later. Kept separate from the rules so both can import it without a
cycle.
"""

from __future__ import annotations

from enum import Enum


class Operator(Enum):
    """Binary operators whose semantic legality L1.5 decides."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    DOT = "dot"
    CROSS = "cross"
