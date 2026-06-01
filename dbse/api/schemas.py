"""Pydantic request models for /api/v5 endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SolveContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain_hint: str | None = None
    precision: str = "standard"


class SolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    context: SolveContext | None = None
    required_proof_level: str = "P2"
    output_formats: list[str] = Field(default_factory=lambda: ["json"])


class ClarifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
