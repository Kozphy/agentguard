# AgentGuard

**A governed, local-first coding agent that makes AI-assisted software changes auditable, testable, policy-controlled, and reversible.**

AgentGuard is not another chatbot wrapper. It is an experimental execution and control layer for local coding models and repository automation.

## Why this project exists

Coding agents can modify files and execute commands quickly, but speed creates operational risk. AgentGuard applies a software-change-control workflow:

```text
Observe → Plan → Policy → Sandbox → Execute → Verify → Approve → Apply → Audit → Replay
```

The initial MVP provides:

- local Ollama integration;
- read-only repository analysis;
- sensitive-file protection;
- shell-command policy decisions: `allow`, `preview`, or `block`;
- Git status and diff inspection;
- append-only JSONL audit events;
- automated tests, linting, typing, and GitHub Actions CI.

## What makes this an AI agent engineering project

The target system is built around explicit agent primitives rather than an unrestricted prompt loop:

| Agent capability | AgentGuard implementation |
|---|---|
| Planning | Schema-validated `ChangePlan` with assumptions, files, tools, checks, risk, and rollback |
| Tool calling | Registered typed tools; the model never executes arbitrary shell text directly |
| Memory and state | Explicit run state machine and immutable configuration snapshots |
| Guardrails | Path rules, command policy, change budgets, timeouts, and deny-by-default controls |
| Environment | Isolated Git worktree for proposed changes |
| Verification | pytest, Ruff, mypy, Semgrep, secret scanning, and policy checks |
| Human-in-the-loop | Approval packet containing plan, diff, evidence, warnings, and blast radius |
| Observability | Structured events, hashes, timings, tool results, model metadata, and artifacts |
| Evaluation | Benchmarks for task success, damage rate, policy violations, rollback, cost, and latency |
| Recovery | Commit-based apply, deterministic replay, and one-command rollback |

See the detailed [AI agent engineering roadmap](docs/agent-engineering-roadmap.md).

## Current safety boundary

AgentGuard v0.1 does **not** autonomously modify files or run arbitrary commands. The first release deliberately establishes policy and evidence boundaries before write capabilities are introduced.

This is a feature, not a missing demo shortcut: the project adds execution only after structured plans, sandboxing, validation, verification, approval, and rollback contracts exist.

## Target architecture

```text
CLI / future API and review dashboard
                  │
                  ▼
          Run state machine
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
 Repository   Model planner   Policy engine
 inspector    + tool calls    + budgets
     │            │            │
     └────────────┼────────────┘
                  ▼
          Git worktree sandbox
                  │
                  ▼
          Controlled executor
                  │
                  ▼
          Verification gates
                  │
                  ▼
       Human approval / rejection
                  │
                  ▼
       Apply · Audit · Replay · Rollback
```

Policy enforcement remains inside AgentGuard. LangGraph, MCP, Ollama, or cloud model adapters may orchestrate requests, but they are not treated as the security boundary.

## Requirements

- Python 3.11+
- Git
- Ollama for the `ask` command

## Installation

```bash
git clone https://github.com/Kozphy/agentguard.git
cd agentguard
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Local model setup

```bash
ollama pull qwen2.5-coder:7b
```

## Usage

Inspect a repository:

```bash
agentguard inspect C:\path\to\repo
```

Ask a local model for a read-only assessment:

```bash
agentguard ask "Identify the highest-risk reliability issue and propose one small fix." --repo C:\path\to\repo
```

Evaluate file access:

```bash
agentguard check-path src/app.py
agentguard check-path .env
```

Evaluate a command:

```bash
agentguard check-command "pytest -q"
agentguard check-command "git push origin main"
agentguard check-command "rm -rf /"
```

View repository changes:

```bash
agentguard show-diff C:\path\to\repo
```

Audit records are written to:

```text
<repository>/.agentguard/audit.jsonl
```

## Development

```bash
ruff check .
mypy src
pytest --cov=agentguard
```

## Delivery roadmap

### Milestone 1 — Plan

- [ ] Schema-validated model-generated change plans
- [ ] Typed tool registry and argument validation
- [ ] Explicit run state machine
- [ ] Reject undeclared writes, unknown tools, path traversal, and malformed output

### Milestone 2 — Sandbox and execute

- [ ] Git worktree sandbox creation
- [ ] File allowlists, denylists, and change-size budgets
- [ ] Approved command execution without `shell=True`
- [ ] Time, output, retry, file-count, and line-count limits

### Milestone 3 — Verify and approve

- [ ] Automated pytest, Ruff, mypy, Semgrep, dependency, and secret gates
- [ ] Human approval queue and reviewer evidence packet
- [ ] Commit-based apply and one-command rollback

### Milestone 4 — Evaluate and integrate

- [ ] Evaluation harness for success, policy violations, and damage rates
- [ ] Hash-chained audit manifests and deterministic replay
- [ ] FastAPI backend and minimal review dashboard
- [ ] Optional MCP read-only server and LangGraph orchestration adapter

## Evaluation contract

A coding agent is not considered successful merely because its patch looks plausible. AgentGuard will measure:

- task success rate;
- policy violation rate;
- unrelated-change or damage rate;
- first-pass verification rate;
- human override rate;
- rollback success rate;
- valid tool-call rate;
- latency, model calls, and token cost.

Adversarial cases will include repository prompt injection, test tampering, secret access, path traversal, command injection, excessive changes, and attempts to weaken verification.

## Security model

AgentGuard follows deny-by-default principles for sensitive resources. It should never be treated as a complete security boundary until isolation, resource controls, and adversarial testing are implemented.

The model is treated as an untrusted planner. Every external effect must pass through deterministic validation and policy enforcement.

## Portfolio positioning

This project demonstrates:

- AI agent engineering and structured tool calling;
- state-machine and workflow orchestration;
- local model integration;
- developer tooling and Git automation;
- testing, CI/CD, and evaluation engineering;
- technology risk and software change controls;
- auditability, observability, and replay;
- human-in-the-loop system design.

### Three-minute recruiter demo

1. Request one small bug fix.
2. Display the structured plan and policy decision.
3. Show a dangerous command being blocked.
4. Execute the approved tools in an isolated worktree.
5. Show the diff and verification evidence.
6. Approve a local commit.
7. Replay the audit trail or roll back.
8. Display benchmark success and damage metrics.

## License

MIT
