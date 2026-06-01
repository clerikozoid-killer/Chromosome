"""L11 adversarial CRISPR corpus (QA level 5)."""

from __future__ import annotations

import pytest

from dbse.knowledge.errors import CoreViolationError
from dbse.knowledge.guard import assert_no_core_violation

CRISPR_PAYLOADS = [
    "F=m*a^2",
    "F = m * a ^ 2",
    "F=m*a**2",
]


@pytest.mark.parametrize("payload", CRISPR_PAYLOADS)
def test_crispr_payloads_rejected(payload: str) -> None:
    with pytest.raises(CoreViolationError):
        assert_no_core_violation(payload)
