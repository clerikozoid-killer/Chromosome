"""L4 contract: domain constraints, invariants, and model descriptors."""

from __future__ import annotations

from dataclasses import dataclass, field

from dbse.contracts.proof import Severity


@dataclass(frozen=True, slots=True)
class Constraint:
    expression: str
    constraint_type: str
    boundary: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Invariant:
    name: str
    expression: str
    threshold: float | None = None
    severity: Severity = Severity.CRITICAL
    tolerance: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DomainModel:
    id: str
    label: str
    metadata: dict[str, str] = field(default_factory=dict)
