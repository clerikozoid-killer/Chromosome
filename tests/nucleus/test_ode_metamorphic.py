"""Metamorphic: k→0 in dv/dt = g - k*v → free fall v≈g*t."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.solve_ode import solve_linear_ode_1


def _ode_ast(g: float, k: float) -> AST:
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(
                kind="OPERATOR",
                op="ADD",
                children=(
                    ASTNode(kind="CONST", value=g),
                    ASTNode(
                        kind="OPERATOR",
                        op="MUL",
                        children=(ASTNode(kind="CONST", value=-k), ASTNode(kind="SYMBOL", value="v")),
                    ),
                ),
            ),
        ),
    )
    return AST(root=ASTNode(kind="OBJECT", op="obj_1", children=(eq,)), structure_class="LinearODE_Order1")


def test_k_to_zero_approaches_free_fall() -> None:
    g = STANDARD_GRAVITY
    k_small = 1e-9
    t = 0.5
    result = solve_linear_ode_1(_ode_ast(g, k_small), t_end=t, v0=0.0)
    assert result.at(t) == pytest.approx(g * t, rel=1e-3)
