# AgentGuard — AI Agent Engineering Roadmap

## Objective

Turn AgentGuard from a read-only coding assistant into a governed execution agent that can propose, preview, verify, approve, apply, audit, and roll back small repository changes.

The project should demonstrate practical AI agent engineering rather than only prompt wrapping:

- structured planning;
- tool calling;
- explicit state transitions;
- policy enforcement;
- sandboxed execution;
- human-in-the-loop approval;
- deterministic verification;
- evaluation and observability;
- reversible changes.

## Target workflow

```text
REQUEST
  ↓
OBSERVE repository state
  ↓
PLAN structured change proposal
  ↓
POLICY allow / preview / block
  ↓
SANDBOX isolated Git worktree
  ↓
EXECUTE approved tools
  ↓
VERIFY tests / lint / typing / security checks
  ↓
APPROVE human decision
  ↓
APPLY commit or reject
  ↓
AUDIT append-only evidence
  ↓
REPLAY / ROLLBACK
```

## State model

Every run should have an explicit state:

```text
CREATED
→ OBSERVED
→ PLANNED
→ POLICY_CHECKED
→ SANDBOX_READY
→ EXECUTING
→ VERIFYING
→ WAITING_APPROVAL
→ APPLIED
```

Terminal states:

```text
BLOCKED | FAILED | REJECTED | ROLLED_BACK
```

Invalid transitions must fail closed and be written to the audit log.

## Phase 1 — Structured plans and tool contracts

### Deliverables

- `ChangePlan` Pydantic model containing:
  - goal;
  - assumptions;
  - files to read;
  - files proposed for modification;
  - commands proposed;
  - expected verification checks;
  - risk level;
  - rollback strategy.
- Typed tool interfaces:
  - `read_file`;
  - `search_text`;
  - `list_files`;
  - `git_diff`;
  - `run_verification`.
- JSON-schema validation for model output.
- Reject unknown tools, malformed arguments, absolute paths, path traversal, and undeclared writes.

### Acceptance criteria

- A model cannot directly execute shell text.
- Every action maps to a registered tool with validated arguments.
- The same plan can be serialized and replayed deterministically.

## Phase 2 — Git worktree sandbox

### Deliverables

- Create a temporary Git worktree per run.
- Record base commit SHA and worktree path.
- Enforce file allowlists, sensitive-path denylists, and maximum change budgets.
- Prevent writes outside the worktree.
- Add timeout and output-size limits for subprocesses.

### Default policy

| Action | Decision |
|---|---|
| Read normal repository file | allow |
| Read `.env`, private keys, credentials | block |
| Run `pytest`, Ruff, mypy | allow in sandbox |
| Modify declared source/test files | preview |
| Change CI, dependency, auth, or deployment files | require approval |
| Network access, package installation, Git push | block by default |
| Destructive shell command | block |

## Phase 3 — Controlled execution

### Deliverables

- Tool executor with per-tool permissions.
- Command allowlist using argument arrays rather than `shell=True`.
- Resource limits:
  - timeout;
  - maximum stdout/stderr bytes;
  - maximum files changed;
  - maximum inserted/deleted lines;
  - maximum retry count.
- Idempotency key for every tool call.
- No automatic retry for write operations unless explicitly safe.

## Phase 4 — Verification and human approval

### Verification gates

Run only checks detected in the repository or explicitly configured:

- pytest;
- Ruff;
- mypy;
- Semgrep;
- dependency audit;
- secret scanning;
- changed-file policy checks.

Store each result with command, exit code, duration, truncated output hash, and artifact path.

### Approval packet

The reviewer should receive:

- original request;
- structured plan;
- policy decisions;
- unified diff;
- verification results;
- unresolved warnings;
- estimated blast radius;
- rollback instructions.

Approval choices:

```text
APPROVE | REJECT | REQUEST_CHANGES
```

## Phase 5 — Audit, replay, and rollback

### Audit event envelope

Each event should include:

```json
{
  "event_id": "uuid",
  "run_id": "uuid",
  "timestamp": "RFC3339",
  "actor": "human|model|system",
  "event_type": "PLAN_CREATED",
  "input_hash": "sha256",
  "output_hash": "sha256",
  "previous_event_hash": "sha256",
  "policy_version": "string",
  "model_config": {},
  "payload": {}
}
```

Add hash chaining and a signed run manifest later. Replay must verify the original base SHA, configuration snapshot, plan, tool inputs, and artifact hashes.

Rollback should use Git commits or worktree disposal, not ad hoc reverse prompts.

## Phase 6 — Evaluation harness

AgentGuard needs measurable engineering quality.

### Benchmark case fields

- repository fixture;
- task description;
- permitted files;
- forbidden files;
- expected tests;
- expected policy decision;
- maximum change size;
- gold outcome.

### Core metrics

| Metric | Meaning |
|---|---|
| Task success rate | Required behavior implemented and checks pass |
| Policy violation rate | Forbidden action attempted or performed |
| Damage rate | Unrelated or harmful changes introduced |
| Human override rate | Reviewer reverses the agent decision |
| First-pass verification rate | Passes checks without retry |
| Rollback success rate | Original state restored correctly |
| Tool-call validity | Calls accepted by schemas and policy |
| Cost and latency | Tokens, model calls, wall-clock duration |

Include adversarial cases for prompt injection in repository files, path traversal, secret access, command injection, excessive diffs, and test tampering.

## Phase 7 — API, UI, and interoperability

After the local execution core is reliable:

- FastAPI service for runs, plans, approvals, events, and artifacts;
- minimal review dashboard;
- OpenTelemetry-compatible tracing;
- provider-neutral model adapter;
- optional MCP server exposing safe read-only tools first;
- optional LangGraph adapter for orchestration experiments.

LangGraph and MCP are integration layers, not the security boundary. Policy enforcement must remain inside AgentGuard's executor.

## Recommended repository structure

```text
src/agentguard/
├── domain/
│   ├── models.py
│   ├── states.py
│   └── events.py
├── planning/
│   ├── schemas.py
│   └── planner.py
├── tools/
│   ├── registry.py
│   ├── filesystem.py
│   ├── git.py
│   └── verification.py
├── policy/
│   ├── engine.py
│   └── rules.py
├── execution/
│   ├── sandbox.py
│   ├── executor.py
│   └── limits.py
├── approval/
│   └── service.py
├── audit/
│   ├── writer.py
│   └── hashing.py
├── evaluation/
│   ├── cases.py
│   ├── runner.py
│   └── metrics.py
└── cli.py
```

## Portfolio demo

A strong three-minute demonstration:

1. Ask AgentGuard to make one small bug fix.
2. Show the generated structured plan.
3. Show one dangerous command being blocked.
4. Run the approved change in an isolated worktree.
5. Display the diff and verification evidence.
6. Approve and create a local commit.
7. Replay the audit trail or roll back the commit.
8. Display benchmark metrics from the same task.

This proves software engineering, agent orchestration, controls, evaluation, and operational reliability in one project.
