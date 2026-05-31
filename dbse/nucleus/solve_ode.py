"""First-order linear ODE solver."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from dbse.contracts.ast import AST, ASTNode
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.monitor import ContinuousInvariantMonitor


@dataclass
class OdeResult:
    state_var: str
    t0: float
    t_end: float
    _t: np.ndarray
    _y: np.ndarray

    def at(self, t: float) -> float:
        return float(np.interp(t, self._t, self._y))


def _extract_linear_ode(root: ASTNode) -> tuple[str, float, float]:
    """Return (state, constant, linear_coeff) from first EQ/DERIV node."""
    for node in root.children:
        if node.kind != "OPERATOR" or node.op != "EQ":
            continue
        lhs, rhs = node.children
        if lhs.op != "DERIV" or lhs.children[0].kind != "SYMBOL":
            continue
        state = str(lhs.children[0].value)
        constant, linear_coeff = _linear_combo_coeffs(rhs)
        return state, constant, linear_coeff
    raise NucleusError("No LinearODE_Order1 equation found in AST")


def _linear_combo_coeffs(node: ASTNode) -> tuple[float, float]:
    constant = 0.0
    linear_coeff = 0.0
    if node.kind == "CONST":
        return float(node.value), 0.0
    if node.kind == "SYMBOL":
        return 0.0, 1.0
    if node.op == "ADD":
        for child in node.children:
            c, k = _linear_combo_coeffs(child)
            constant += c
            linear_coeff += k
    elif node.op == "MUL" and len(node.children) == 2:
        a, b = node.children
        if a.kind == "CONST" and b.kind == "SYMBOL":
            return 0.0, float(a.value)
        if b.kind == "CONST" and a.kind == "SYMBOL":
            return 0.0, float(b.value)
    elif node.op == "NEG":
        c, k = _linear_combo_coeffs(node.children[0])
        return -c, -k
    return constant, linear_coeff


def solve_linear_ode_1(
    ast: AST,
    *,
    t_end: float = 10.0,
    v0: float = 0.0,
    monitor: ContinuousInvariantMonitor | None = None,
) -> OdeResult:
    state, constant, linear_coeff = _extract_linear_ode(ast.root)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        return np.array([constant + linear_coeff * y[0]])

    def event(_t: float, y: np.ndarray) -> float:
        if monitor is None:
            return 1.0
        ok = monitor.check_invariants(float(_t), {state: float(y[0])})
        return 1.0 if ok else 0.0

    event.terminal = True  # type: ignore[attr-defined]
    event.direction = 0  # type: ignore[attr-defined]

    sol = solve_ivp(
        rhs,
        (0.0, t_end),
        [v0],
        method="RK45",
        dense_output=True,
        events=[event] if monitor else None,
    )
    t_grid = sol.t
    y_grid = sol.y[0]
    return OdeResult(state_var=state, t0=0.0, t_end=t_end, _t=t_grid, _y=y_grid)
