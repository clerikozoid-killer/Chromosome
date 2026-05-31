"""L3 RIBOSOME — AST compiler + canonical hash + cache."""

from __future__ import annotations

from typing import ClassVar

from dbse.contracts.context import PipelineContext
from dbse.ribosome.cache import SemanticCache
from dbse.ribosome.compile import compile_membrane
from dbse.ribosome.errors import RibosomeError
from dbse.ribosome.hash import annotate_ast


class Ribosome:
    """L3 layer: compile MEMBRANE → AST, hash, cache lookup/store."""

    name: ClassVar[str] = "L3.RIBOSOME"

    def __init__(
        self,
        cache: SemanticCache | None = None,
        *,
        cache_secret: str = "dev-cache-secret",
        core_version: str = "core-dev",
    ) -> None:
        self._cache = cache or SemanticCache(secret=cache_secret)
        self._core_version = core_version

    def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.membrane is None:
            ctx.record(self.name, note="skipped:no-membrane")
            return ctx
        try:
            raw_ast = compile_membrane(ctx.membrane)
            ast = annotate_ast(raw_ast)
        except RibosomeError as exc:
            ctx.record(self.name, note="compile-error")
            ctx.halt_message = str(exc)
            return ctx
        ctx.ast = ast
        digest = ast.canonical_hash
        if digest is not None:
            hit = self._cache.get(digest, core_version=self._core_version)
            if hit is not None:
                ctx.solution = hit.solution
                ctx.record(
                    self.name,
                    note="cache-hit",
                    hash=digest,
                    hits=hit.hits,
                    proof_level=hit.proof_level,
                )
                return ctx
        ctx.record(
            self.name,
            note="compiled",
            hash=digest,
            structure_class=ast.structure_class,
        )
        return ctx
