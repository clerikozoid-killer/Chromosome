"""L1 unit-expression parser.

Grammar (no parentheses; YAGNI — named derived units cover the rest):

    expr   := factor (('*' | '/' | <implicit *>) factor)*
    factor := IDENT ('^' INT)?

Evaluation is strictly left-to-right, so "kg*m/s^2" == ((kg·m)/s²).
"""

from __future__ import annotations

import re

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional.errors import DimensionError
from dbse.dimensional.units import resolve

_TOKEN = re.compile(r"\s*(?:(?P<op>[*/^])|(?P<int>[+-]?\d+)|(?P<ident>[A-Za-zµμΩ]+))")


def parse_unit(text: str) -> Dimension:
    """Parse a unit expression into a :class:`Dimension`."""
    s = text.strip()
    if s in ("", "1", "dimensionless"):
        return DIMENSIONLESS
    return _evaluate(_tokenize(s), s)


def _tokenize(s: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if m is None or m.end() == pos:
            raise DimensionError(f"Cannot parse unit expression {s!r} near {s[pos:]!r}")
        pos = m.end()
        if m.group("op") is not None:
            tokens.append(("op", m.group("op")))
        elif m.group("int") is not None:
            tokens.append(("int", m.group("int")))
        else:
            tokens.append(("ident", m.group("ident")))
    return tokens


def _evaluate(tokens: list[tuple[str, str]], original: str) -> Dimension:
    result = DIMENSIONLESS
    op = "*"
    i = 0
    n = len(tokens)

    while i < n:
        kind, val = tokens[i]
        if kind == "op":
            if val in ("*", "/"):
                op = val
                i += 1
                continue
            raise DimensionError(f"Unexpected operator {val!r} in unit expression {original!r}")
        # kind is "ident" or "int": a factor, optionally raised to an integer power.
        # A bare integer literal (e.g. the "1" in "1/s") is a dimensionless factor.
        dim = DIMENSIONLESS if kind == "int" else resolve(val)
        i += 1
        if i < n and tokens[i] == ("op", "^"):
            i += 1
            if i >= n or tokens[i][0] != "int":
                raise DimensionError(
                    f"Expected integer exponent after '^' in unit expression {original!r}"
                )
            dim = dim ** int(tokens[i][1])
            i += 1

        result = result * dim if op == "*" else result / dim
        op = "*"  # adjacent factors multiply implicitly

    return result
