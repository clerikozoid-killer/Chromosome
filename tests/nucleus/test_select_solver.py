"""L5 unit tests: solver routing and quantity extraction."""

from __future__ import annotations

import pytest

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.select_solver import SolverKind, select_solver


def test_select_solver_algebraic_quantities() -> None:
    ast = AST(root=ASTNode(kind="OBJECT", op="obj_1", children=()))
    ast = AST(root=ast.root, structure_class="Algebraic_Quantities")
    assert select_solver(ast) is SolverKind.ALGEBRAIC


def test_select_solver_ode() -> None:
    ast = AST(root=ASTNode(kind="OBJECT", op="obj_1"), structure_class="LinearODE_Order1")
    assert select_solver(ast) is SolverKind.ODE


def test_select_solver_unknown_raises() -> None:
    ast = AST(root=ASTNode(kind="OBJECT", op="obj_1"), structure_class="Unknown")
    with pytest.raises(NucleusError):
        select_solver(ast)


def test_membrane_quantities_si_converts_mass() -> None:
    membrane = {
        "quantities": [
            {"ref": "obj_1", "property": "mass", "value": 100.0, "unit": "g"},
        ]
    }
    q = membrane_quantities_si(membrane)
    assert q["mass"] == pytest.approx(0.1)
