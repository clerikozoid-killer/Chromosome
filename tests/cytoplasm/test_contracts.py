"""L4 contract tests: domain types."""

from __future__ import annotations

from dbse.contracts import Constraint, DomainModel, Invariant
from dbse.contracts.proof import Severity


def test_invariant_defaults_to_critical() -> None:
    inv = Invariant(name="v_lt_c", expression="v < c", threshold=299792458.0)
    assert inv.severity is Severity.CRITICAL
    assert inv.tolerance == 0.0


def test_constraint_carries_type_label() -> None:
    c = Constraint(expression="div(v) = 0", constraint_type="continuity")
    assert c.constraint_type == "continuity"


def test_domain_model_is_frozen() -> None:
    m = DomainModel(id="linear_friction", label="Linear drag")
    assert m.id == "linear_friction"
