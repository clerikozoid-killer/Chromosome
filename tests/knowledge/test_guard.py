"""L11 Core guard tests."""

from __future__ import annotations

import pytest

from dbse.knowledge.errors import CoreViolationError
from dbse.knowledge.guard import assert_no_core_violation


def test_guard_rejects_newton_crispr_variant() -> None:
    with pytest.raises(CoreViolationError, match="newton_2"):
        assert_no_core_violation("F = m * a^2")


def test_guard_rejects_explicit_contradiction() -> None:
    with pytest.raises(CoreViolationError, match="contradiction"):
        assert_no_core_violation("contradict F = m*a in this model")


def test_guard_allows_benign_constraint() -> None:
    assert_no_core_violation("F = m * a")
