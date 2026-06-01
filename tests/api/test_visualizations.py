"""L12 Mermaid visualization tests."""

from __future__ import annotations

from dbse.api.visualizations import proof_trace_mermaid
from dbse.contracts.ast import AST, ASTNode
from dbse.contracts.context import PipelineContext


def test_proof_trace_mermaid_includes_layers_and_hash() -> None:
    ctx = PipelineContext(
        query="q",
        ast=AST(root=ASTNode(kind="OBJECT", op="obj_1"), canonical_hash="abcd1234"),
    )
    ctx.record("L0.MEMBRANE", note="parsed")
    ctx.record("L3.RIBOSOME", note="compiled")
    mermaid = proof_trace_mermaid(ctx)
    assert "graph TD" in mermaid
    assert "L0.MEMBRANE" in mermaid
    assert "abcd1234" in mermaid
    assert "L0 --> L1" in mermaid
