"""L0.5 layer tests: classification wired into the pipeline context."""

from __future__ import annotations

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.membrane import Membrane
from dbse.layers.sts_typing import StsTyping


def _after_membrane(query: str) -> PipelineContext:
    return Membrane().process(PipelineContext(query=query))


def test_physics_query_sets_type_and_route_without_halting() -> None:
    ctx = StsTyping().process(_after_membrane("force on a 0.1 kg mass"))
    assert not ctx.halted
    assert ctx.sts_type == "PHYSICS_COMPUTE"
    route_entry = next(e for e in ctx.trace if e.layer == "L0.5.STS_TYPING")
    assert route_entry.payload["route"] == "full_pipeline"


def test_opinion_query_halts_unhandled() -> None:
    ctx = StsTyping().process(_after_membrane("what is the best language?"))
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.UNHANDLED
    assert ctx.sts_type == "OPINION"


def test_definition_query_sets_type_and_does_not_halt() -> None:
    ctx = StsTyping().process(_after_membrane("what is entropy"))
    assert not ctx.halted
    assert ctx.sts_type == "DEFINITION"


def test_uses_membrane_quantities_as_the_has_quantities_signal() -> None:
    # "mass 0.1 kg" parses to a quantity; classifier should see PHYSICS_COMPUTE.
    ctx = StsTyping().process(_after_membrane("mass 0.1 kg"))
    assert ctx.sts_type == "PHYSICS_COMPUTE"
