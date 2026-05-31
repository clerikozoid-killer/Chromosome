"""L5 NUCLEUS — SymPy/Z3 + Continuous Invariant Monitor."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.contracts.proof import Proof, ProofLevel
from dbse.nucleus.constants import STANDARD_GRAVITY
from dbse.nucleus.errors import NucleusError
from dbse.nucleus.monitor import ContinuousInvariantMonitor
from dbse.nucleus.quantities import membrane_quantities_si
from dbse.nucleus.select_solver import SolverKind, select_solver
from dbse.nucleus.solve_algebraic import solve_algebraic
from dbse.nucleus.solve_ode import solve_linear_ode_1
from dbse.nucleus.tinfo import assign_proof_level, compute_tinfo
from dbse.nucleus.z3_verify import verify_weight_force
from dbse.ribosome.cache import CacheEntry, SemanticCache


class Nucleus:
    """L5 layer: algebraic solve, proof assembly, cache store on miss."""

    name: ClassVar[str] = "L5.NUCLEUS"

    def __init__(
        self,
        cache: SemanticCache | None = None,
        *,
        cache_secret: str = "dev-cache-secret",
        core_version: str = "core-dev",
    ) -> None:
        self._cache = cache or SemanticCache(secret=cache_secret)
        self._cache_secret = cache_secret
        self._core_version = core_version

    def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.solution is not None:
            ctx.record(self.name, note="skipped:already-solved")
            return ctx
        if ctx.ast is None:
            ctx.record(self.name, note="skipped:no-ast")
            return ctx
        try:
            kind = select_solver(ctx.ast)
        except NucleusError as exc:
            ctx.record(self.name, note="solve-error", error=str(exc))
            ctx.halt_message = str(exc)
            return ctx
        if kind is SolverKind.ODE:
            invariants = ctx.invariants or []
            monitor = ContinuousInvariantMonitor(invariants)
            t_end = float(ctx.config.get("ode_t_end", 10.0))
            v0 = float(ctx.config.get("ode_v0", 0.0))
            try:
                ode_result = solve_linear_ode_1(ctx.ast, t_end=t_end, v0=v0, monitor=monitor)
                if not monitor.violations:
                    monitor.check_invariants(
                        t_end,
                        {ode_result.state_var: ode_result.at(t_end)},
                    )
            except NucleusError as exc:
                ctx.record(self.name, note="solve-error", error=str(exc))
                ctx.halt_message = str(exc)
                return ctx
            if monitor.violations:
                v0iol = monitor.violations[0]
                proof = Proof(
                    level=ProofLevel.P3,
                    violations=list(monitor.violations),
                    solver_path=["ode:scipy", "monitor:critical_violation"],
                )
                ctx.proof = proof
                ctx.halt(
                    HaltReason.MODEL_BREAKDOWN,
                    f"Инвариант '{v0iol.invariant}' нарушен в t={v0iol.time}. "
                    "Возможно, требуется релятивистская/нелинейная модель.",
                )
                ctx.record(self.name, note="model-breakdown", violation=v0iol.invariant)
                return ctx
            ctx.solution = {
                "value": ode_result.at(t_end),
                "unit": "m/s",
                "symbolic": f"{ode_result.state_var}(t)",
                "numeric_steps": [
                    {"step": 1, "expression": f"d({ode_result.state_var})/dt = ..."},
                    {
                        "step": 2,
                        "expression": (
                            f"{ode_result.state_var}({t_end})"
                            f" ≈ {ode_result.at(t_end):.4f}"
                        ),
                    },
                ],
                "ode_series": {"t": ode_result._t.tolist(), "y": ode_result._y.tolist()},
            }
            proof = Proof(solver_path=["ode:scipy", "ode:symbolic_fallback"])
            level, confidence = assign_proof_level(proof)
            proof.level = level
            proof.tinfo = compute_tinfo(proof)
            proof.confidence = confidence
            ctx.proof = proof
            ctx.record(self.name, note="solved-ode", proof_level=level.value)
            return ctx
        solver_path: list[str] = []
        required = str(ctx.config.get("required_proof_level", "P2"))
        try:
            result = solve_algebraic(ctx)
        except NucleusError as exc:
            ctx.record(self.name, note="solve-error", error=str(exc))
            ctx.halt_message = str(exc)
            return ctx
        solver_path.extend(result.solver_path)
        proof = Proof(solver_path=solver_path)
        quantities = membrane_quantities_si(ctx.membrane) if ctx.membrane else {}
        if required in ("P1", "VERIFIED_NUMERIC", "P0", "AXIOMATIC_PROOF"):
            ok, z3_steps = verify_weight_force(
                mass=quantities.get("mass", 0.0),
                g=float(ctx.config.get("gravity", STANDARD_GRAVITY)),
                force=result.value,
                budget_ms=int(ctx.config.get("z3_budget_ms", 100)),
            )
            proof.z3_steps = z3_steps
            if ok:
                proof.solver_path.append("z3:verified")
            else:
                proof.solver_path.append("domain_switch:z3-timeout")
        level, confidence = assign_proof_level(proof)
        if "z3:verified" in proof.solver_path:
            level = ProofLevel.P1
        tinfo = compute_tinfo(proof)
        proof.level = level
        proof.tinfo = tinfo
        proof.confidence = confidence
        ctx.solution = {
            "value": result.value,
            "unit": result.unit,
            "symbolic": result.symbolic,
            "numeric_steps": result.numeric_steps,
        }
        ctx.proof = proof
        digest = ctx.ast.canonical_hash
        if digest is not None:
            self._cache.put(
                digest,
                CacheEntry(
                    ast=ctx.ast,
                    solution=ctx.solution,
                    proof_level=level.value,
                    tinfo=tinfo,
                ),
                core_version=self._core_version,
            )
        ctx.record(
            self.name,
            note="solved",
            proof_level=level.value,
            tinfo=tinfo,
            invariants_pending=bool(ctx.invariants),
        )
        return ctx
