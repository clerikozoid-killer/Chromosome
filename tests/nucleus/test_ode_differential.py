"""Differential: SciPy vs SymPy dsolve for dv/dt = -k*v."""

from __future__ import annotations

import pytest
import sympy as sp

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.solve_ode import solve_linear_ode_1


def test_scipy_matches_sympy_exponential_decay() -> None:
    k = 0.2
    t_end = 3.0
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(
                kind="OPERATOR",
                op="MUL",
                children=(ASTNode(kind="CONST", value=-k), ASTNode(kind="SYMBOL", value="v")),
            ),
        ),
    )
    root = ASTNode(kind="OBJECT", op="o", children=(eq,))
    ast = AST(root=root, structure_class="LinearODE_Order1")
    numeric = solve_linear_ode_1(ast, t_end=t_end, v0=1.0).at(t_end)
    t = sp.Symbol("t")
    v = sp.Function("v")
    analytic = sp.dsolve(sp.Eq(v(t).diff(t), -k * v(t)), v(t), ics={v(0): 1})
    expected = float(analytic.rhs.subs(t, t_end))
    assert numeric == pytest.approx(expected, rel=1e-5)
