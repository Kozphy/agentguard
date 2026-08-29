# AgentGuard

**A governed, local-first coding agent that makes AI-assisted software changes auditable, testable, and reversible.**

AgentGuard is not another chatbot wrapper. It is an experimental control layer for local coding models and repository automation.

## Why this project exists

Coding agents can modify files and execute commands quickly, but speed creates operational risk. AgentGuard applies a software-change-control workflow:

```text
Observe → Plan → Policy → Preview → Verify → Repair → Re-verify → Approve → Audit
```

The current MVP provides:

- local Ollama integration;
- read-only repository analysis;
- sensitive-file protection;
- shell-command policy decisions: `allow`, `preview`, or `block`;
- Git status and diff inspection;
- deterministic pytest/Ruff/mypy verification gates;
- allowlisted AI patch generation for existing files;
- bounded verify/repair retry loops;
- automatic rollback when the repair budget is exhausted or the loop errors;
- append-only JSONL audit events;
- GitHub Actions CI.

## Safety boundaries

Repair mode deliberately remains constrained:

- the working tree must start clean;
- the user must explicitly allowlist each editable file with `--file`;
- sensitive paths are blocked by policy;
- the model may modify existing allowlisted files only;
- new files, deletion, and rename operations are rejected;
- generated patches must pass `git apply --check` before application;
- pytest, Ruff, and mypy are run after every repair attempt;
- unsuccessful repair attempts are rolled back;
- a successful repair is left in `preview` state for human review before commit or push.

## Architecture

```text
User task
   │
   ├── Repository inspector
   ├── Policy engine
   ├── Ollama repair agent
   │       │
   │       └── allowlisted unified diff
   │
   ├── Deterministic verifier
   │       ├── pytest
   │       ├── Ruff
   │       └── mypy
   │
   ├── FAIL → repair again (bounded)
   ├── PASS → human preview/review
   └── JSONL audit trail
```

## Requirements

- Python 3.11+
- Git
- Ollama for AI analysis and repair

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

Run deterministic verification:

```bash
agentguard verify C:\path\to\repo
```

Run a governed repair loop against explicitly allowed files:

```bash
agentguard repair "Fix the failing parser tests" \
  --repo C:\path\to\repo \
  --file src/parser.py \
  --file src/validation.py \
  --max-rounds 2
```

The repair flow is:

```text
Baseline verification
        ↓ FAIL
Ollama generates allowlisted patch
        ↓
git apply --check
        ↓
pytest + Ruff + mypy
   ↙ FAIL       PASS ↘
repair again      preview for human review
   ↓
repair budget exhausted
   ↓
rollback
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

- [x] File allowlists for repair mode
- [x] Automated pytest/Ruff/mypy verification gates
- [x] Bounded AI repair loop
- [x] Rollback of unsuccessful AI repair attempts
- [ ] Structured model-generated change plans
- [ ] Git worktree sandbox creation
- [ ] Change-size budgets
- [ ] Semgrep verification gate
- [ ] Human approval queue
- [ ] One-command rollback for approved changes
- [ ] FastAPI backend and web dashboard
- [ ] Evaluation harness for agent success and damage rates
- [ ] Signed audit manifests and deterministic replay

## Security model

AgentGuard follows deny-by-default principles for sensitive resources. Repair mode is intentionally narrow and should not be treated as a complete security boundary until worktree sandboxing, adversarial testing, and stronger patch validation are implemented.

## Portfolio positioning

This project demonstrates:

- AI agent engineering
- deterministic verification and repair loops
- developer tooling
- Git and CI/CD automation
- technology risk and change controls
- auditability and observability
- human-in-the-loop system design

## License

MIT
