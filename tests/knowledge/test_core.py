"""L11 CoreTruthLayer tests."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from dbse.knowledge.core import CORE, CoreTruthLayer


def test_core_axioms_are_immutable_mapping() -> None:
    assert isinstance(CORE.axioms, MappingProxyType)
    assert "newton_2" in CORE.axioms
    with pytest.raises(TypeError):
        CORE.axioms["evil"] = CORE.axioms["newton_2"]  # type: ignore[index]


def test_version_token_is_stable_eight_hex_chars() -> None:
    t1 = CoreTruthLayer.version_token()
    t2 = CoreTruthLayer.version_token()
    assert t1 == t2
    assert len(t1) == 8
    assert all(c in "0123456789abcdef" for c in t1)
