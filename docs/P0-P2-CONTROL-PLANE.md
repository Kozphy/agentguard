# Kozphy Agent Control Plane — P0/P1/P2 foundation

Status: **prototype only**, not a 24/7 production service. This change adds
offline primitives to AgentGuard, not live Orca/Paseo/Emdash/T3/Aperant connections.

## Existing components (observed from repository documentation)

- `Kozphy/ai-company-os`: local API, worker, scheduler, signed workflow_run
  webhook intake and local evidence. Its high-risk outbox dispatch is disabled.
- `Kozphy/ci-failure-orchestrator`: diagnosis, disposable-worktree verification,
  deterministic policy escalation and draft-PR-at-most design.
- `Kozphy/EvalForge`: deterministic finance evaluation, regression gates and
  evidence manifests; real results should not be inferred from synthetic fixtures.
- `Kozphy/orca-integration-bootstrap`: Windows configuration/doctor tool,
  **not** a cross-agent orchestration engine.

## P0 — Single task contract and fail-closed policy (implemented prototype)

`control_plane.Task` carries task ID, repository, stage, operation and
canonical payload SHA-256. `validate_task` restricts stages/operations.
`authorize_action` rejects **every** write, PR creation, merge, deploy,
credential, or unknown action. Existing sensitive paths and commands remain
under AgentGuard's own policies.

## P1 — Reproducible evidence handoff (implemented prototype)

`complete` requires a nonempty structured evidence object and persists its
canonical hash. Only the current worker lease holder may complete the task.
This **does not verify** that external CI or EvalForge actually ran; an
independent verifier is needed before upgrading any status to VERIFIED.

## P2 — Durable local queue (implemented prototype)

SQLite persists queued/leased/done tasks; duplicate tasks are idempotent,
conflicting IDs fail, and expired leases may be reclaimed. This is **not**
an always-on hosted service. It requires an independently supervised process
and a powered-on host. It has no GitHub webhook receiver, automatic retries,
dead-letter queue, heartbeat, multi-repo permissions, telemetry, or remote UI.

## Proposed adapters (NOT implemented)

```text
GitHub webhook (verify signature + replay defense)
  -> ai-company-os signed intake
  -> trusted event normalization / authorization
  -> AgentGuard local queue (this prototype)
  -> read-only diagnosis in ci-failure-orchestrator
  -> EvalForge evidence and independent CI status verification
  -> human review and separately authorized scoped patch
  -> optional Draft PR; never automatic merge or deployment
```

Orca, Paseo, Emdash, Aperant and T3 Code may be provider-specific executors
only after checking documented APIs and securing the host. Do not exchange
raw secrets between their processes. No automatic shell execution or
GitHub write permissions are introduced here.

## Verification

```bash
python -m pytest tests/test_control_plane.py -q
python -m pytest -q
ruff check .
mypy src
```

The above checks must run in a trusted environment. A green CI run is
independent evidence and has **not** been assumed here.

## Risks and next acceptance gates

1. Add an allowlisted event ingestion adapter with validated signed payloads,
   task-scoped authorizations and replay window tests.
2. Add controlled read-only adapters for real diagnosis/evaluation with
   strict timeouts, redaction and captured command/CI provenance.
3. Add claim/retry/heartbeat crash recovery tests, queue bounds and
   dead-letter handling before 24/7 operation.
4. Implement approval storage with signed/expiring human intent, and enforce
   permissions at the GitHub App level before any write-capable mode.
5. Validate GitHub Rulesets and bypass paths separately; this prototype cannot
   read or modify them. Keep all merges and deployments human-only.

Rollback: close the draft PR or delete this feature branch.
