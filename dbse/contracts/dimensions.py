"""L1 contract: physical dimensions in the SI basis.

A :class:`Dimension` is a vector of rational exponents over the seven SI base
quantities ``[M, L, T, I, Θ, N, J]``. Rationals (not just ints) are used so that
roots (e.g. ``sqrt(area)``) remain representable.

Only the *type* and its algebra live here. Unit parsing and the actual L1 layer
logic arrive in Stage 1; this module is a frozen contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

BASIS: tuple[str, ...] = ("M", "L", "T", "I", "Theta", "N", "J")
"""Human-readable names of the seven SI base quantities, in canonical order."""

_RANK = len(BASIS)

Exponent = Fraction | int


@dataclass(frozen=True, slots=True)
class Dimension:
    """A vector of rational exponents over the SI base quantities.

    The seven components correspond, in order, to ``BASIS``:
    mass, length, time, electric current, temperature, amount, luminous intensity.
    """

    exponents: tuple[Fraction, Fraction, Fraction, Fraction, Fraction, Fraction, Fraction]

    @classmethod
    def of(cls, *exponents: Exponent) -> Dimension:
        """Build a dimension from up to seven exponents (missing ones are zero)."""
        if len(exponents) > _RANK:
            raise ValueError(f"Dimension takes at most {_RANK} exponents, got {len(exponents)}")
        padded = tuple(Fraction(e) for e in exponents) + (Fraction(0),) * (_RANK - len(exponents))
        return cls(padded)  # type: ignore[arg-type]

    @property
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exponents)

    def __mul__(self, other: Dimension) -> Dimension:
        return Dimension(
            tuple(a + b for a, b in zip(self.exponents, other.exponents, strict=True))  # type: ignore[arg-type]
        )

    def __truediv__(self, other: Dimension) -> Dimension:
        return Dimension(
            tuple(a - b for a, b in zip(self.exponents, other.exponents, strict=True))  # type: ignore[arg-type]
        )

    def __pow__(self, power: Exponent) -> Dimension:
        p = Fraction(power)
        return Dimension(tuple(e * p for e in self.exponents))  # type: ignore[arg-type]

    def __str__(self) -> str:
        if self.is_dimensionless:
            return "[1]"
        parts = [
            f"{name}^{exp}"
            for name, exp in zip(BASIS, self.exponents, strict=True)
            if exp != 0
        ]
        return "[" + " ".join(parts) + "]"


DIMENSIONLESS = Dimension.of()
