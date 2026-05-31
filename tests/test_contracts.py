"""Stage 0 unit + property tests for the core data contracts."""

from __future__ import annotations

from fractions import Fraction

from hypothesis import given
from hypothesis import strategies as st

from dbse.contracts import (
    DIMENSIONLESS,
    AffineType,
    Dimension,
    HaltReason,
    PipelineContext,
    Proof,
    ProofLevel,
)

# A few named dimensions used across the suite.
MASS = Dimension.of(1)
LENGTH = Dimension.of(0, 1)
TIME = Dimension.of(0, 0, 1)
FORCE = Dimension.of(1, 1, -2)        # [M L T^-2]
ENERGY = Dimension.of(1, 2, -2)       # [M L^2 T^-2]


def test_dimension_of_pads_to_seven() -> None:
    assert len(MASS.exponents) == 7
    assert DIMENSIONLESS.is_dimensionless


def test_dimension_multiplication_adds_exponents() -> None:
    # force * length == energy
    assert FORCE * LENGTH == ENERGY


def test_dimension_division_subtracts_exponents() -> None:
    assert ENERGY / LENGTH == FORCE


def test_dimension_power_scales_exponents() -> None:
    assert Dimension.of(0, 2) == LENGTH ** 2
    assert Dimension.of(0, Fraction(1, 2)) == LENGTH ** Fraction(1, 2)


def test_dimensionless_is_multiplicative_identity() -> None:
    assert FORCE * DIMENSIONLESS == FORCE


# --- Property-based laws (Stage 0 seeds the L1 invariants) -------------------

_exp = st.integers(min_value=-4, max_value=4)
_dims = st.builds(Dimension.of, *([_exp] * 7))


@given(_dims, _dims)
def test_property_mul_is_exponentwise_addition(a: Dimension, b: Dimension) -> None:
    product = a * b
    for ea, eb, ep in zip(a.exponents, b.exponents, product.exponents, strict=True):
        assert ep == ea + eb


@given(_dims)
def test_property_unit_conversion_invariance(a: Dimension) -> None:
    # Multiplying then dividing by the same dimension is identity (analogue of
    # converting units back and forth: the dimension signature is unchanged).
    assert (a * LENGTH) / LENGTH == a


@given(_dims, _dims)
def test_property_mul_commutes(a: Dimension, b: Dimension) -> None:
    assert a * b == b * a


# --- AffineType --------------------------------------------------------------

def test_affine_type_distinguishes_semantics_at_equal_dimension() -> None:
    energy = AffineType(ENERGY, "Energy", tensor_rank=0)
    torque = AffineType(ENERGY, "Torque", tensor_rank=1)
    # Same dimension, but the affine types are not equal — this is the whole
    # point of L1.5 (compatibility rules land in Stage 2).
    assert energy.dimension == torque.dimension
    assert energy != torque


def test_affine_type_is_hashable_and_frozen() -> None:
    a = AffineType(ENERGY, "Energy")
    assert {a: 1}[a] == 1


# --- Proof / context ---------------------------------------------------------

def test_proof_defaults() -> None:
    p = Proof()
    assert p.level is ProofLevel.P2
    assert p.tinfo == 0.0
    assert p.violations == []


def test_context_halt_sets_structured_reason() -> None:
    ctx = PipelineContext(query="x")
    ctx.halt(HaltReason.DIMENSION_ERROR, "bad units")
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.DIMENSION_ERROR
    assert ctx.halt_message == "bad units"
