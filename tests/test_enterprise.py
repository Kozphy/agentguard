import httpx
import pytest

from agentguard.enterprise import EnterpriseAIControlPlane, RemediationRequest


def request() -> RemediationRequest:
    return RemediationRequest(
        request_id="req-1",
        asset_id="pc-001",
        problem_type="proxy_drift",
        action="reset_proxy",
        risk="high",
        evidence=[{"source": "diagnostic", "status": "failed"}],
    )


def test_blocked_eval_never_executes() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/api/v1/gates/evaluate"
        return httpx.Response(200, json={"decision": "block", "reasons": ["unsafe"]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    plane = EnterpriseAIControlPlane(
        evalforge_url="http://evalforge",
        executor_url="http://executor",
        client=client,
    )
    with pytest.raises(PermissionError, match="blocked"):
        plane.run(request())


def test_review_requires_human_approval() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/api/v1/gates/evaluate":
            return httpx.Response(
                200,
                json={"decision": "review", "requires_human_review": True},
            )
        raise AssertionError("executor must not be called without approval")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    plane = EnterpriseAIControlPlane(
        evalforge_url="http://evalforge",
        executor_url="http://executor",
        client=client,
    )
    with pytest.raises(PermissionError, match="Human approval"):
        plane.run(request())


def test_approved_review_executes_and_verifies() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/api/v1/gates/evaluate":
            return httpx.Response(
                200,
                json={"decision": "review", "requires_human_review": True},
            )
        if req.url.path == "/api/v1/remediation/execute":
            return httpx.Response(
                200,
                json={
                    "execution_id": "exec-1",
                    "status": "success",
                    "before_state": {"proxy": "bad"},
                    "after_state": {"proxy": "clean"},
                    "verification": {"connectivity": "pass"},
                    "rollback_performed": False,
                },
            )
        raise AssertionError(req.url.path)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    plane = EnterpriseAIControlPlane(
        evalforge_url="http://evalforge",
        executor_url="http://executor",
        client=client,
    )
    result = plane.run(request(), approved_by="it-admin")
    assert result.status == "success"
    assert result.verification["connectivity"] == "pass"
