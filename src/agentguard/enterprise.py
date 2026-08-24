from __future__ import annotations

from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel, Field


class GateDecision(StrEnum):
    PASS = "pass"
    BLOCK = "block"
    REVIEW = "review"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationRequest(BaseModel):
    schema_version: str = "1.0"
    request_id: str
    asset_id: str
    problem_type: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = RiskLevel.MEDIUM
    model_version: str | None = None
    prompt_version: str | None = None


class EvaluationResult(BaseModel):
    decision: GateDecision
    scores: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    eval_version: str | None = None


class ExecutionResult(BaseModel):
    execution_id: str
    status: str
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    rollback_performed: bool = False


class EnterpriseAIControlPlane:
    """Coordinates policy/evaluation/execution without coupling service internals."""

    def __init__(
        self,
        *,
        evalforge_url: str,
        executor_url: str,
        timeout_seconds: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.evalforge_url = evalforge_url.rstrip("/")
        self.executor_url = executor_url.rstrip("/")
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def evaluate(self, request: RemediationRequest) -> EvaluationResult:
        response = self.client.post(
            f"{self.evalforge_url}/api/v1/gates/evaluate",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return EvaluationResult.model_validate(response.json())

    def execute(self, request: RemediationRequest, *, approved_by: str) -> ExecutionResult:
        payload = {
            "schema_version": request.schema_version,
            "request_id": request.request_id,
            "asset_id": request.asset_id,
            "action": request.action,
            "parameters": request.parameters,
            "approved_by": approved_by,
        }
        response = self.client.post(
            f"{self.executor_url}/api/v1/remediation/execute",
            json=payload,
        )
        response.raise_for_status()
        return ExecutionResult.model_validate(response.json())

    def run(
        self,
        request: RemediationRequest,
        *,
        approved_by: str | None = None,
    ) -> ExecutionResult:
        gate = self.evaluate(request)
        if gate.decision is GateDecision.BLOCK:
            raise PermissionError("EvalForge blocked the proposed remediation")
        if (gate.decision is GateDecision.REVIEW or gate.requires_human_review) and not approved_by:
            raise PermissionError("Human approval is required before execution")
        actor = approved_by or "agentguard:auto-approved"
        return self.execute(request, approved_by=actor)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
