"""L5 monitor tests."""

from __future__ import annotations

from dbse.contracts.domain import Invariant
from dbse.contracts.proof import Severity
from dbse.nucleus.monitor import ContinuousInvariantMonitor


def test_monitor_passes_when_invariant_satisfied() -> None:
    inv = Invariant(name="v_lt_c", expression="v < c", threshold=10.0, severity=Severity.CRITICAL)
    mon = ContinuousInvariantMonitor([inv])
    assert mon.check_invariants(0.0, {"v": 5.0}) is True
    assert mon.violations == []


def test_monitor_records_critical_violation() -> None:
    inv = Invariant(name="v_lt_c", expression="v < c", threshold=10.0, severity=Severity.CRITICAL)
    mon = ContinuousInvariantMonitor([inv])
    assert mon.check_invariants(1.0, {"v": 11.0}) is False
    assert len(mon.violations) == 1
    assert mon.violations[0].invariant == "v_lt_c"
    assert mon.violations[0].time == 1.0
