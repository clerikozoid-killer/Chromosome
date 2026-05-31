"""L0 layer tests: parsing wired into the pipeline context."""

from __future__ import annotations

from typing import Any, ClassVar

from dbse.contracts.context import HaltReason, PipelineContext
from dbse.layers.membrane import Membrane


def test_valid_query_fills_membrane_and_does_not_halt() -> None:
    ctx = Membrane().process(PipelineContext(query="mass 0.1 kg"))
    assert not ctx.halted
    assert ctx.membrane is not None
    assert ctx.membrane["question_type"] == "compute"
    assert any(q["unit"] == "kg" for q in ctx.membrane["quantities"])


def test_plain_text_still_parses_to_a_minimal_membrane() -> None:
    ctx = Membrane().process(PipelineContext(query="hello there"))
    assert not ctx.halted
    assert ctx.membrane is not None
    assert ctx.membrane["objects"] == [{"id": "obj_1", "type": "system", "label": "query"}]


def test_compromised_adapter_payload_halts_with_clarification() -> None:
    class EvilAdapter:
        name: ClassVar[str] = "evil"

        def parse(self, query: str) -> dict[str, Any]:
            # Simulate a jailbroken LLM trying to inject a forbidden node.
            return {
                "objects": [{"id": "obj_1", "type": "body", "label": "x"}],
                "quantities": [],
                "relations": [],
                "operators": [{"op": "SUPPRESS", "arg": "friction"}],
                "question_type": "compute",
                "target": {"ref": "obj_1", "property": "force"},
            }

    ctx = Membrane(parser=EvilAdapter()).process(PipelineContext(query="..."))
    assert ctx.halted
    assert ctx.halt_reason is HaltReason.CLARIFICATION
    assert ctx.membrane is None
    assert [e.layer for e in ctx.trace] == ["L0.MEMBRANE"]


def test_relation_from_alias_round_trips_in_stored_membrane() -> None:
    class RelAdapter:
        name: ClassVar[str] = "rel"

        def parse(self, query: str) -> dict[str, Any]:
            return {
                "objects": [
                    {"id": "obj_1", "type": "body", "label": "a"},
                    {"id": "obj_2", "type": "body", "label": "b"},
                ],
                "quantities": [],
                "relations": [{"type": "distance", "from": "obj_1", "to": "obj_2"}],
                "question_type": "compute",
                "target": {"ref": "obj_1", "property": "force"},
            }

    ctx = Membrane(parser=RelAdapter()).process(PipelineContext(query="..."))
    assert not ctx.halted
    assert ctx.membrane is not None
    assert ctx.membrane["relations"][0]["from"] == "obj_1"
