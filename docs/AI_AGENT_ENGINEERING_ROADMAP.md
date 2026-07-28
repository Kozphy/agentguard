# AgentGuard AI Agent Engineering Roadmap

## Goal

Turn AgentGuard from a read-only policy prototype into a governed coding-agent runtime that can plan, use tools, verify changes, request human approval, and replay every decision.

The project should demonstrate practical AI agent engineering rather than a chatbot wrapper.

## Target workflow

```text
User request
    ↓
Task intake + risk classification
    ↓
Planner creates a structured change plan
    ↓
Policy engine evaluates files, commands, budgets, and permissions
    ↓
Sandboxed tool execution in a Git worktree
    ↓
Verifier runs tests, lint, typing, and security checks
    ↓
Human approval for risky or uncertain actions
    ↓
Commit / rollback
    ↓
Signed audit record + deterministic replay
```

## Core agent state

Use an explicit state object rather than hidden conversational memory.

```python
class AgentState(TypedDict):
    task_id: str
    user_request: str
    repo_path: str
    risk_level: str
    plan: list[dict]
    current_step: int
    tool_calls: list[dict]
    changed_files: list[str]
    verification_results: list[dict]
    approval_status: str
    final_status: str
    limitations: list[str]
```

Recommended states:

```text
RECEIVED
→ PLANNED
→ POLICY_CHECKED
→ SANDBOX_READY
→ EXECUTING
→ VERIFYING
→ WAITING_APPROVAL
→ COMMITTED | ROLLED_BACK | BLOCKED | FAILED
```

## Phase 1 — Structured planning and tool calling

Deliverables:

- Pydantic models for `ChangePlan`, `PlanStep`, `ToolRequest`, and `ToolResult`.
- A planner interface supporting Ollama first and optional hosted providers later.
- JSON-schema validation for every model-generated plan.
- Tool registry with explicit names, argument schemas, timeouts, and risk levels.
- Initial tools:
  - `read_file`
  - `list_files`
  - `search_code`
  - `git_diff`
  - `run_tests`
- No direct shell tool exposed to the model.

Acceptance criteria:

- Invalid plans are rejected deterministically.
- Every tool call has a unique ID and audit event.
- The model cannot invoke unregistered tools.

## Phase 2 — Sandboxed execution

Deliverables:

- Temporary Git worktree per task.
- File allowlists and deny lists.
- Maximum changed-file and changed-line budgets.
- Command templates rather than arbitrary shell strings.
- Timeout, output-size, and exit-code controls.
- One-command rollback by deleting the worktree or resetting the task branch.

Acceptance criteria:

- Main working tree is never modified during execution.
- `.env`, credentials, private keys, and Git internals are denied by default.
- Budget violations move the task to `BLOCKED`.

## Phase 3 — Verification agent

The verifier must be independent from the planner. It should evaluate evidence, not merely agree with the original model.

Verification gates:

- `pytest`
- Ruff
- mypy
- Semgrep or another static scanner
- changed-file policy
- diff-size budget
- secret scanning
- optional repository-specific commands

Output schema:

```json
{
  "gate": "pytest",
  "status": "pass",
  "command": ["pytest", "-q"],
  "exit_code": 0,
  "duration_ms": 1842,
  "evidence_path": ".agentguard/evidence/task-123/pytest.txt"
}
```

Acceptance criteria:

- Failed mandatory gates prevent commit.
- Verification evidence is stored separately from LLM commentary.
- The final report distinguishes facts, model judgments, and limitations.

## Phase 4 — Human approval and policy escalation

Approval rules should be based on risk, not on whether the model sounds confident.

Require approval for:

- dependency changes;
- CI/CD or infrastructure files;
- authentication and authorization code;
- database migrations;
- more than the configured change budget;
- network access;
- destructive commands;
- unresolved verifier findings.

Provide a FastAPI approval API:

```text
GET  /tasks/{task_id}
GET  /tasks/{task_id}/evidence
POST /tasks/{task_id}/approve
POST /tasks/{task_id}/reject
POST /tasks/{task_id}/rollback
```

## Phase 5 — Evaluation harness

Integrate AgentGuard with EvalForge concepts to measure whether the agent is useful and safe.

Benchmark dimensions:

- task success rate;
- test pass rate;
- policy violation rate;
- unnecessary-file-change rate;
- rollback rate;
- human override rate;
- latency;
- token and model cost;
- false allow / false block rate;
- damage rate under adversarial prompts.

Create benchmark fixtures for:

1. safe bug fix;
2. dependency update;
3. prompt-injection text inside a repository file;
4. request to reveal `.env`;
5. destructive shell request;
6. oversized refactor;
7. failing test with misleading model explanation;
8. ambiguous task requiring clarification or human review.

## Phase 6 — MCP adapter

Add MCP only after the internal tool contract is stable.

Expose safe read-only tools first. Do not expose unrestricted shell execution.

Potential MCP tools:

- repository inspection;
- policy evaluation;
- task status;
- verification evidence;
- audit replay.

The MCP layer should translate requests into AgentGuard's existing tool registry rather than bypass policy checks.

## Suggested package layout

```text
src/agentguard/
├── api/
├── agents/
│   ├── planner.py
│   └── verifier.py
├── audit/
├── execution/
│   ├── sandbox.py
│   └── worktree.py
├── models/
├── policy/
├── providers/
├── tools/
├── verification/
└── workflow/
    ├── engine.py
    └── state.py
```

## Recommended implementation order

1. Structured plan schemas.
2. Internal tool registry.
3. Explicit workflow state machine.
4. Git worktree sandbox.
5. Verification gates.
6. Human approval API.
7. Evaluation harness.
8. MCP adapter.
9. Web dashboard.
10. Multi-agent experiments only after the single-agent workflow is reliable.

## What not to prioritize yet

- A large multi-agent team with role-playing agents.
- A polished chat UI before execution safety exists.
- Autonomous production deployment.
- Unrestricted browser or shell control.
- Vector databases without a concrete retrieval requirement.

## Portfolio demonstration

A strong three-minute demo should show:

1. User submits a small repository task.
2. Planner produces a validated plan.
3. Policy blocks access to a sensitive file.
4. Agent changes an allowed file inside a worktree.
5. Tests and static checks run.
6. A risky action waits for human approval.
7. The final diff, evidence, audit chain, and rollback command are displayed.

This demonstrates Python, LLM tool calling, agent state, policy enforcement, sandboxing, verification, human-in-the-loop design, evaluation, API design, Git automation, and AI governance in one coherent project.
