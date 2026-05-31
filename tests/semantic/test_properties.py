"""L1.5 property-based laws (QA-gate level 2): reflexivity and symmetry."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dbse.semantic import Operator, affine, compatible

_SCALAR_TAGS = ["Energy", "Work", "Heat", "Power", "Length", "Mass", "Time"]
_VECTOR_TAGS = ["Force", "Velocity", "Momentum", "Torque"]
_ALL_TAGS = _SCALAR_TAGS + _VECTOR_TAGS
_ADDITIVE = [Operator.ADD, Operator.SUBTRACT]


@given(st.sampled_from(_ALL_TAGS), st.sampled_from(_ADDITIVE))
def test_addition_is_reflexive(tag: str, op: Operator) -> None:
    # A quantity is always addable to itself.
    assert compatible(affine(tag), affine(tag), op)


@given(
    st.sampled_from(_ALL_TAGS),
    st.sampled_from(_ALL_TAGS),
    st.sampled_from(_ADDITIVE),
)
def test_additive_compatibility_is_symmetric(a: str, b: str, op: Operator) -> None:
    # compatible(a, b) iff compatible(b, a) for + and -.
    assert compatible(affine(a), affine(b), op) == compatible(affine(b), affine(a), op)


@given(st.sampled_from(_ALL_TAGS), st.sampled_from(_ALL_TAGS))
def test_multiplication_is_always_compatible(a: str, b: str) -> None:
    assert compatible(affine(a), affine(b), Operator.MULTIPLY)
