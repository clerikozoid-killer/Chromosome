"""L7 Pydantic output schema for constrained styling."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExpressionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eli5: str
    academic: str
    business: str
    metaphors_used: list[str] = Field(default_factory=list)
