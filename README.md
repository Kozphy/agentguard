# AgentGuard

**A governed, local-first coding agent that makes AI-assisted software changes auditable, testable, and reversible.**

AgentGuard is not another chatbot wrapper. It is an experimental control layer for local coding models and repository automation.

## Why this project exists

Coding agents can modify files and execute commands quickly, but speed creates operational risk. AgentGuard applies a software-change-control workflow:

```text
Observe → Plan → Policy → Preview → Verify → Approve → Audit → Replay
```

The initial MVP provides:

- local Ollama integration;
- read-only repository analysis;
- sensitive-file protection;
- shell-command policy decisions: `allow`, `preview`, or `block`;
- Git status and diff inspection;
- append-only JSONL audit events;
- automated tests, linting, typing, and GitHub Actions CI.

## Non-goals for v0.1

AgentGuard does **not** autonomously modify files or run arbitrary commands yet. The first release deliberately establishes policy and evidence boundaries before adding write capabilities.

## Architecture

```text
CLI / future web dashboard
        │
        ├── Repository inspector
        ├── Policy engine
        ├── Ollama read-only analysis
        ├── Verification gates
        └── JSONL audit trail
```

## Requirements

- Python 3.11+
- Git
- Ollama for the `ask` command

## Installation

```bash
git clone https://github.com/YOUR-USERNAME/agentguard.git
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

## Roadmap

- [ ] Structured model-generated change plans
- [ ] Git worktree sandbox creation
- [ ] File allowlists and change-size budgets
- [ ] Approved command execution with timeout controls
- [ ] Automated pytest/Ruff/mypy/Semgrep verification gates
- [ ] Human approval queue
- [ ] One-command rollback
- [ ] FastAPI backend and web dashboard
- [ ] Evaluation harness for agent success and damage rates
- [ ] Signed audit manifests and deterministic replay

## Security model

AgentGuard follows deny-by-default principles for sensitive resources. It should never be treated as a complete security boundary until sandboxing and adversarial testing are implemented.

## Portfolio positioning

This project demonstrates:

- AI agent engineering
- developer tooling
- Git and CI/CD automation
- technology risk and change controls
- auditability and observability
- human-in-the-loop system design

## License

MIT
