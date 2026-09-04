# AgentGuard Workbench Architecture

Local-first governed multi-agent engineering workbench built on top of the
existing Python AgentGuard control layer.

## Product goal

A desktop application where a human can open a Git repository, launch one or
more coding-agent backends in isolated worktrees, compare their candidate
changes, verify them, pass proposed actions through AgentGuard policy, and only
then approve a commit or draft PR — with an append-only audit trail.

## Non-negotiable control loop

```text
Observe → Plan → Policy → Preview → Verify → Approve → Audit → Replay
```

The desktop UI orchestrates this loop. It does **not** replace it.

## Authority split

| Concern | Authority | Location |
|---------|-----------|----------|
| Path / command policy | Python AgentGuard | `src/agentguard/policy.py` |
| Append-only audit | Python AgentGuard | `src/agentguard/audit.py` |
| Verification gates (future) | Python AgentGuard + configured commands | TBD |
| Workspace / worktree / process / terminal OS ops | Electron **main** | `desktop/src/main/` |
| UI state and presentation | Electron **renderer** | `desktop/src/renderer/` |
| Agent CLI protocol differences | `AgentAdapter` implementations | `desktop/src/main/agents/` |

The renderer never spawns processes, never touches the filesystem for privileged
operations, and never bypasses AgentGuard policy.

## Phase model

### Phase 1 (this iteration) — scaffold and observe

- Architecture document
- Electron + React + TypeScript desktop scaffold
- Typed IPC contracts
- Repository selection
- Read-only Git status
- `AgentAdapter` interface + `FakeAgentAdapter`
- Unit tests and development scripts
- README development instructions

Explicitly **out of scope** for Phase 1:

- Real AI agent execution
- `node-pty`
- Creating / deleting Git worktrees
- Agent file mutation
- Arbitrary command execution
- Push / PR flows

### Phase 2 (recommended next)

- `node-pty` managed terminals behind main-process IPC
- Worktree create/list/remove (still policy-gated)
- First real adapter (Codex CLI or Claude Code) behind `AgentAdapter`
- Stream terminal output to the UI
- Diff inspection per worktree
- Bridge to Python `evaluate_paths` / `evaluate_command` / `AuditLog`

### Later phases

- Multi-agent comparison UI
- Configurable verification command runners
- Human approval queue before apply / commit / draft PR
- Replay of audit events
- Adapters: Codex, Claude Code, OpenCode, Cursor CLI, OpenClaw

## Desktop layout

```text
desktop/
  package.json
  tsconfig*.json
  vite.config.ts
  src/
    main/
      index.ts
      workspace/          # open / hold current repository
      worktrees/          # Phase 2+
      agents/             # AgentAdapter + FakeAgentAdapter
      terminal/           # Phase 2+ node-pty
      git/                # read-only Git helpers
      ipc/                # typed channels + handlers
    preload/
      index.ts            # contextBridge only
    renderer/
      App.tsx
      components/
      features/
        workspace/
        tasks/            # Phase 2+ UI shells
        agents/
        terminal/
        diff/
  tests/
```

## Process boundaries

```text
┌─────────────────────────────┐
│ Renderer (React)            │
│  - no Node, no spawn        │
│  - calls window.agentguard  │
└──────────────┬──────────────┘
               │ contextBridge + ipcRenderer.invoke
┌──────────────▼──────────────┐
│ Preload                     │
│  - exposes typed API only   │
└──────────────┬──────────────┘
               │ ipcMain.handle
┌──────────────▼──────────────┐
│ Main                        │
│  - dialogs, Git, adapters   │
│  - deny-by-default          │
│  - later: pty, worktrees    │
└──────────────┬──────────────┘
               │ future: spawn / stdio bridge
┌──────────────▼──────────────┐
│ Python AgentGuard           │
│  policy · audit · verify    │
└─────────────────────────────┘
```

## AgentAdapter contract

```ts
interface AgentAdapter {
  readonly id: string;
  readonly displayName: string;
  detect(): Promise<AgentDetectResult>;
  start(options: AgentStartOptions): Promise<void>;
  send(input: string): Promise<void>;
  stop(): Promise<void>;
  getStatus(): AgentStatus;
}
```

Adapters are registered in the main process. The UI only sees adapter metadata
and status through IPC. No adapter is tightly coupled to the UI.

Phase 1 ships `FakeAgentAdapter` for contract tests. Future adapters:

- `CodexAdapter`
- `ClaudeCodeAdapter`
- `OpenCodeAdapter`
- `CursorAdapter`
- `OpenClawAdapter`

## Reused AgentGuard capabilities

| Python module | Reuse in workbench |
|---------------|--------------------|
| `policy.evaluate_paths` | Gate file access before agent tools (Phase 2+) |
| `policy.evaluate_command` | Gate shell / verification / git write commands |
| `models.Decision` / `PolicyResult` | Mirrored as TS types for IPC payloads |
| `audit.AuditLog` | Shared evidence trail under `.agentguard/` |
| `repository.status` / `diff` | Behavioral reference for desktop Git helpers |
| CLI `check-path` / `check-command` | Stable subprocess API until a richer bridge exists |
| Control-loop vocabulary | Product and UI language |

Phase 1 Git status in Electron mirrors `repository.status` (read-only
`git status --short`) and does **not** reimplement policy.

## Security requirements (standing)

Deny by default. Never:

- read `.env` files automatically;
- access SSH / private credentials;
- execute deployment commands;
- push to the default branch automatically;
- merge pull requests automatically;
- bypass AgentGuard command / path policy;
- disable existing security tests;
- silently weaken CI or verification gates;
- expose Node / spawn APIs to the renderer.

## Integration risks

1. **Dual Git implementations** — desktop main and Python `repository.py` both
   speak Git. Keep desktop Phase 1 read-only and align semantics; prefer a Python
   bridge for policy-sensitive operations later.
2. **Rich CLI vs machine JSON** — only `check-path` / `check-command` emit JSON
   today. A `--json` flag or stdio RPC will be needed before the UI relies on
   `inspect` / `show-diff` parsing.
3. **Electron privilege creep** — every new OS capability must land behind a
   typed IPC channel with explicit allowlisting.
4. **Agent CLI diversity** — adapters must absorb protocol differences so the
   core loop stays agent-agnostic.
5. **Audit completeness** — desktop actions must eventually write through
   `AuditLog` or an equivalent append-only store; Phase 1 does not yet write
   audit events from Electron.
6. **CI surface** — Python CI must remain green; desktop checks are additive.

## Testing strategy

- **Python**: existing `pytest` policy and audit tests remain authoritative for
  security decisions.
- **Desktop**: Vitest unit tests for `AgentAdapter` / `FakeAgentAdapter`, IPC
  contract shapes, and injectable Git service behavior.
- **Forbidden in Phase 1 tests**: spawning real agents, mutating repositories,
  or weakening Python gates.
