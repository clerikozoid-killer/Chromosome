"""L5 ODE solver tests."""

from __future__ import annotations

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.solve_ode import OdeResult, solve_linear_ode_1


def _falling_body_ast() -> AST:
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(
                kind="OPERATOR",
                op="ADD",
                children=(
                    ASTNode(kind="CONST", value=9.80665),
                    ASTNode(
                        kind="OPERATOR",
                        op="MUL",
                        children=(
                            ASTNode(kind="CONST", value=-0.1),
                            ASTNode(kind="SYMBOL", value="v"),
                        ),
                    ),
                ),
            ),
        ),
    )
    root = ASTNode(kind="OBJECT", op="obj_1", children=(eq,))
    return AST(root=root, structure_class="LinearODE_Order1")


def test_solve_dvdt_g_minus_kv() -> None:
    result = solve_linear_ode_1(_falling_body_ast(), t_end=5.0, v0=0.0)
    assert isinstance(result, OdeResult)
    assert result.state_var == "v"
    assert result.at(5.0) > 0.0
    assert result.at(5.0) < 100.0  # sub-relativistic for this model
