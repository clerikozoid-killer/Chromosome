"""Adversarial: ODE drift v > c → P3."""

from __future__ import annotations

from dbse.contracts import PipelineContext, ProofLevel
from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.domain import Invariant
from dbse.contracts.proof import Severity
from dbse.layers.nucleus import Nucleus


def test_ode_v_exceeds_c_halts_model_breakdown() -> None:
    # dv/dt = 2c; v(t)=2ct exceeds c when t > 0.5s
    c = 299_792_458.0
    eq = ASTNode(
        kind="OPERATOR",
        op="EQ",
        children=(
            ASTNode(kind="OPERATOR", op="DERIV", children=(ASTNode(kind="SYMBOL", value="v"),)),
            ASTNode(kind="CONST", value=2.0 * c),
        ),
    )
    ast = AST(
        root=ASTNode(kind="OBJECT", op="obj_1", children=(eq,)),
        structure_class="LinearODE_Order1",
    )
    ctx = PipelineContext(
        query="relativistic breach",
        ast=ast,
        invariants=[
            Invariant(name="v_lt_c", expression="v < c", threshold=c, severity=Severity.CRITICAL),
        ],
        config={"ode_t_end": 0.6, "ode_v0": 0.0},
    )
    out = Nucleus().process(ctx)
    assert out.halted
    assert out.proof is not None
    assert out.proof.level is ProofLevel.P3
    assert out.proof.violations
