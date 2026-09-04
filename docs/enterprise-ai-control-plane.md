# Enterprise AI Control Plane

This branch turns AgentGuard into the orchestration layer connecting three existing projects without merging their internal codebases.

## Service responsibilities

- **AgentGuard** — orchestration, policy, approval state, audit coordination.
- **EvalForge** — evaluation gate for correctness, safety, grounding, regression and human-review routing.
- **Windows-Network-Recovery-Toolkit** — domain diagnostics, allowlisted remediation execution, verification and rollback.

## Transaction flow

```text
Detect problem
  -> AgentGuard creates remediation request
  -> EvalForge evaluates request
  -> BLOCK: stop and audit
  -> REVIEW: require human approval
  -> PASS/approved REVIEW: call domain executor
  -> Windows Toolkit executes allowlisted action
  -> verify post-state
  -> rollback on failed verification
  -> AgentGuard records final evidence
```

## Versioned integration contract

`contracts/remediation-request-v1.schema.json` defines the boundary shared by the services. Internal models remain independent so each project can evolve without importing another project's implementation.

Each transaction should preserve at least:

- request_id
- asset_id
- problem type and evidence
- proposed action and parameters
- risk level
- model and prompt version
- evaluation decision and evaluation version
- approver identity when required
- before/after state
- verification result
- rollback result
- timestamps and audit hashes

## API contract expected from EvalForge

### `POST /api/v1/gates/evaluate`

Input: `RemediationRequest`

Response:

```json
{
  "decision": "pass | block | review",
  "scores": {
    "correctness": 0.96,
    "safety": 0.99,
    "groundedness": 0.94
  },
  "reasons": [],
  "requires_human_review": false,
  "eval_version": "eval-v1"
}
```

## API contract expected from Windows-Network-Recovery-Toolkit

### `POST /api/v1/remediation/execute`

Only allowlisted actions should be accepted. Arbitrary shell commands must not cross this boundary.

Response:

```json
{
  "execution_id": "exec-456",
  "status": "success",
  "before_state": {},
  "after_state": {},
  "verification": {"connectivity": "pass"},
  "rollback_performed": false
}
```

## Current implementation

`src/agentguard/enterprise.py` provides typed Pydantic contracts and a synchronous HTTP orchestrator. It already enforces two important invariants:

1. a `block` result can never reach the executor;
2. a `review` result cannot reach the executor without an explicit approver.

The integration tests use `httpx.MockTransport`, so the control logic is testable before the two downstream API adapters are implemented.

## Next implementation slices

1. Add `/api/v1/gates/evaluate` adapter to EvalForge using its existing deterministic graders and review queue.
2. Add an allowlisted `/api/v1/remediation/execute` adapter to Windows-Network-Recovery-Toolkit.
3. Add signed/append-only transaction audit events in AgentGuard.
4. Add failed-verification rollback semantics to the executor contract.
5. Add OpenTelemetry correlation using `request_id` and `execution_id`.
6. Add RBAC roles for viewer, reviewer, operator and admin.
7. Add an end-to-end Docker Compose demo after each service has a stable HTTP adapter.

## Enterprise invariant

The AI proposes. Policy and evaluation gate. Humans approve high-risk changes. The executor performs only allowlisted actions. Verification decides success. Every transition produces evidence.
