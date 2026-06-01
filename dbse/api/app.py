"""FastAPI production surface for DBSE v5.0 Chromosome."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException

from dbse.api.mapper import context_to_clarify_response, context_to_solve_response
from dbse.api.schemas import ClarifyRequest, SolveRequest
from dbse.api.visualizations import proof_trace_mermaid
from dbse.contracts.context import HaltReason
from dbse.pipeline import Pipeline

app = FastAPI(title="DBSE v5.0 Chromosome", version="5.0.0")


@app.post("/api/v5/solve")
def solve(body: SolveRequest) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if body.context is not None:
        config.update(body.context.model_dump())
    config["required_proof_level"] = body.required_proof_level
    ctx = Pipeline().run(body.query, config=config)
    viz: dict[str, Any] = {"mermaid": proof_trace_mermaid(ctx)}
    if ctx.ast and ctx.ast.canonical_hash:
        viz["ast_hash"] = ctx.ast.canonical_hash
    config["_visualizations"] = viz
    ctx.config = config
    rid = f"req_{uuid.uuid4().hex[:12]}"
    return context_to_solve_response(ctx, request_id=rid)


@app.post("/api/v5/clarify")
def clarify(body: ClarifyRequest) -> dict[str, Any]:
    ctx = Pipeline().run(body.query)
    if ctx.halt_reason is not HaltReason.AMBIGUITY_HALT:
        raise HTTPException(status_code=400, detail="Query is not ambiguous")
    return context_to_clarify_response(ctx)


def main() -> None:
    import uvicorn

    uvicorn.run("dbse.api.app:app", host="0.0.0.0", port=8000, reload=False)
