"""Stage 0 tests: the end-to-end conveyor wiring (all layers are stubs)."""

from __future__ import annotations

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.base import Layer, PassThroughLayer
from dbse.pipeline import Pipeline, default_layers

EXPECTED_ORDER = [
    "L0.MEMBRANE",
    "L0.5.STS_TYPING",
    "L1.DIMENSIONS",
    "L1.5.AFFINE_TYPES",
    "L2.MODEL_LATTICE",
    "L3.RIBOSOME",
    "L4.CYTOPLASM",
    "L5.NUCLEUS",
    "L6.NARRATIVE",
    "L7.EXPRESSION",
]


def test_default_pipeline_has_ten_layers_in_order() -> None:
    layers = default_layers()
    assert [layer.name for layer in layers] == EXPECTED_ORDER


def test_all_default_layers_satisfy_protocol() -> None:
    for layer in default_layers():
        assert isinstance(layer, Layer)


def _first_layer_occurrence_order(trace: list) -> list[str]:
    seen: list[str] = []
    for entry in trace:
        if entry.layer not in seen:
            seen.append(entry.layer)
    return seen


def test_pipeline_runs_through_every_layer() -> None:
    ctx = Pipeline().run("С какой силой Земля притягивает яблоко массой 100 г?")
    assert not ctx.halted
    assert _first_layer_occurrence_order(ctx.trace) == EXPECTED_ORDER


def test_early_pruning_stops_after_halt() -> None:
    class HaltingLayer(PassThroughLayer):
        name = "HALT"

        def process(self, ctx: PipelineContext) -> PipelineContext:
            ctx.record(self.name, note="halting")
            ctx.halt(HaltReason.DIMENSION_ERROR, "stop here")
            return ctx

    pipeline = Pipeline([PassThroughLayer(), HaltingLayer(), PassThroughLayer()])
    ctx = pipeline.run("x")

    assert ctx.halted
    assert ctx.halt_reason is HaltReason.DIMENSION_ERROR
    # The third layer must not have run.
    assert [entry.layer for entry in ctx.trace] == ["layer", "HALT"]


def test_context_carries_query_and_config() -> None:
    ctx = Pipeline().run("q", config={"precision": "high"})
    assert ctx.query == "q"
    assert ctx.config["precision"] == "high"
