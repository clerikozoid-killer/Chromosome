"""L7 fallback stylist tests."""

from __future__ import annotations

from dbse.expression.fallback import style_fallback


def test_style_fallback_prefixes_skeleton() -> None:
    sk = "Масса 0.100 kg."
    out = style_fallback(sk)
    assert sk in out.eli5
    assert sk in out.academic
    assert sk in out.business


def test_style_fallback_business_includes_numeric_result() -> None:
    sk = "Сила 0.981 N."
    out = style_fallback(sk, value=0.980665, unit="N")
    assert "0.981" in out.business
    assert "N" in out.business
