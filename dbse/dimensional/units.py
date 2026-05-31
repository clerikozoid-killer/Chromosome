"""L1 named-unit registry and SI-prefix resolution.

At L1 only the *dimension* matters, not the magnitude, so SI prefixes
(kilo, milli, ...) leave the dimension unchanged — they only need to be
stripped to find the underlying unit.
"""

from __future__ import annotations

from dbse.contracts.dimensions import DIMENSIONLESS, Dimension
from dbse.dimensional.errors import DimensionError

# Named units → dimensional signature [M, L, T, I, Θ, N, J].
_UNITS: dict[str, Dimension] = {
    # dimensionless
    "1": DIMENSIONLESS,
    "rad": DIMENSIONLESS,
    "sr": DIMENSIONLESS,
    # SI base
    "kg": Dimension.of(1),
    "g": Dimension.of(1),
    "m": Dimension.of(0, 1),
    "s": Dimension.of(0, 0, 1),
    "A": Dimension.of(0, 0, 0, 1),
    "K": Dimension.of(0, 0, 0, 0, 1),
    "mol": Dimension.of(0, 0, 0, 0, 0, 1),
    "cd": Dimension.of(0, 0, 0, 0, 0, 0, 1),
    # time / length alternates (dimension only)
    "min": Dimension.of(0, 0, 1),
    "h": Dimension.of(0, 0, 1),
    "day": Dimension.of(0, 0, 1),
    "L": Dimension.of(0, 3),
    # derived — mechanical
    "N": Dimension.of(1, 1, -2),
    "J": Dimension.of(1, 2, -2),
    "W": Dimension.of(1, 2, -3),
    "Pa": Dimension.of(1, -1, -2),
    "bar": Dimension.of(1, -1, -2),
    "Hz": Dimension.of(0, 0, -1),
    "eV": Dimension.of(1, 2, -2),
    "cal": Dimension.of(1, 2, -2),
    # derived — electromagnetic
    "C": Dimension.of(0, 0, 1, 1),
    "V": Dimension.of(1, 2, -3, -1),
    "ohm": Dimension.of(1, 2, -3, -2),
    "Ω": Dimension.of(1, 2, -3, -2),
    "F": Dimension.of(-1, -2, 4, 2),
    "S": Dimension.of(-1, -2, 3, 2),
    "Wb": Dimension.of(1, 2, -2, -1),
    "H": Dimension.of(1, 2, -2, -2),
}

# SI prefixes (longest first so "da" is tried before "d").
_PREFIXES: tuple[str, ...] = (
    "da",
    "y", "z", "a", "f", "p", "n", "u", "µ", "μ",
    "m", "c", "d", "h", "k", "M", "G", "T", "P", "E", "Z", "Y",
)


def resolve(symbol: str) -> Dimension:
    """Resolve a single unit symbol (optionally prefixed) to its dimension."""
    if symbol in _UNITS:
        return _UNITS[symbol]
    for prefix in sorted(_PREFIXES, key=len, reverse=True):
        if symbol.startswith(prefix):
            rest = symbol[len(prefix):]
            if rest and rest != "1" and rest in _UNITS:
                return _UNITS[rest]
    raise DimensionError(f"Unknown unit symbol: {symbol!r}")
