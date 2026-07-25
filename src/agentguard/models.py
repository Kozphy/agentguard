from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class Decision(StrEnum):
    ALLOW = "allow"
    PREVIEW = "preview"
    BLOCK = "block"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyResult(BaseModel):
    decision: Decision
    risk: RiskLevel
    reasons: list[str] = Field(default_factory=list)


class ChangePlan(BaseModel):
    task: str
    repository: Path
    files: list[Path] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    policy: PolicyResult
