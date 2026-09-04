import httpx

from agentguard.enterprise import EnterpriseAIControlPlane, RemediationRequest


def test_review_then_preview_execution_contract() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/api/v1/gates/evaluate":
            return httpx.Response(
                200,
                json={
                    "decision": "review",
                    "scores": {
                        "safety": 0.65,
                        "groundedness": 1.0,
                        "evidence_coverage": 1.0,
                    },
                    "reasons": ["High-risk action requires explicit human approval."],
                    "requires_human_review": True,
                    "eval_version": "enterprise-gate-v1",
                },
            )
        if request.url.path == "/api/v1/remediation/execute":
            payload = __import__("json").loads(request.content)
            assert payload["approved_by"] == "operator@example.com"
            return httpx.Response(
                200,
                json={
                    "execution_id": "preview-1",
                    "status": "previewed",
                    "before_state": {"proxy_enable": 1},
                    "after_state": {
                        "mutation_applied": False,
                        "approved_by": "operator@example.com",
                    },
                    "verification": {
                        "mode": "dry_run",
                        "can_execute": False,
                        "rollback_plan_present": True,
                    },
                    "rollback_performed": False,
                },
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    control_plane = EnterpriseAIControlPlane(
        evalforge_url="http://evalforge",
        executor_url="http://windows-toolkit",
        client=client,
    )
    request = RemediationRequest(
        request_id="req-1",
        asset_id="endpoint-1",
        problem_type="proxy_drift",
        evidence=[{"signal": "proxy_enabled"}, {"signal": "direct_path_ok"}],
        action="disable_wininet_proxy",
        risk="high",
    )

    result = control_plane.run(request, approved_by="operator@example.com")

    assert result.status == "previewed"
    assert result.after_state["mutation_applied"] is False
    assert calls == ["/api/v1/gates/evaluate", "/api/v1/remediation/execute"]
