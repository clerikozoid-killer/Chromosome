"""Mentor must not mutate Core axioms."""

from __future__ import annotations


def test_mentor_modules_do_not_expose_core_mutator() -> None:
    import dbse.mentor.run as run_mod
    import dbse.mentor.verdict as verdict_mod

    assert not hasattr(run_mod, "mutate_core")
    assert not hasattr(verdict_mod, "mutate_core")
    from dbse.knowledge.core import CORE

    assert CORE.__frozen__ is True
