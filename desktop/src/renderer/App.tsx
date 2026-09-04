import { useEffect, useState } from "react";
import type { AgentAdapterInfo, GitStatusSnapshot, WorkspaceInfo } from "../shared/types";
import { WorkspacePanel } from "./features/workspace/WorkspacePanel";
import { AgentsPanel } from "./features/agents/AgentsPanel";
import { TasksPlaceholder } from "./features/tasks/TasksPlaceholder";
import { TerminalPlaceholder } from "./features/terminal/TerminalPlaceholder";
import { DiffPlaceholder } from "./features/diff/DiffPlaceholder";
import { AppShell } from "./components/AppShell";
import { StatusBanner } from "./components/StatusBanner";

export function App() {
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [status, setStatus] = useState<GitStatusSnapshot | null>(null);
  const [agents, setAgents] = useState<AgentAdapterInfo[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      const [workspaceResult, agentsResult] = await Promise.all([
        window.agentguard.getWorkspace(),
        window.agentguard.listAgents(),
      ]);
      if (workspaceResult.ok) {
        setWorkspace(workspaceResult.value);
      }
      if (agentsResult.ok) {
        setAgents(agentsResult.value);
      }
    })();
  }, []);

  async function handleOpenRepository() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await window.agentguard.selectWorkspace();
      if (!result.ok) {
        if (result.error.code !== "CANCELLED") {
          setMessage(result.error.message);
        }
        return;
      }
      setWorkspace(result.value);
      const statusResult = await window.agentguard.getWorkspaceStatus();
      if (statusResult.ok) {
        setStatus(statusResult.value);
      } else {
        setStatus(null);
        setMessage(statusResult.error.message);
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleRefreshStatus() {
    setBusy(true);
    setMessage(null);
    try {
      const statusResult = await window.agentguard.getWorkspaceStatus();
      if (!statusResult.ok) {
        setMessage(statusResult.error.message);
        return;
      }
      setStatus(statusResult.value);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <header className="hero">
        <p className="eyebrow">AgentGuard Workbench · Phase 1</p>
        <h1>Governed multi-agent engineering</h1>
        <p className="lede">
          Observe repositories through typed IPC. Policy, verification, and audit remain
          in the Python AgentGuard package.
        </p>
      </header>

      {message ? <StatusBanner tone="error">{message}</StatusBanner> : null}

      <div className="grid">
        <WorkspacePanel
          workspace={workspace}
          status={status}
          busy={busy}
          onOpen={handleOpenRepository}
          onRefresh={handleRefreshStatus}
        />
        <AgentsPanel agents={agents} />
        <TasksPlaceholder />
        <TerminalPlaceholder />
        <DiffPlaceholder />
      </div>
    </AppShell>
  );
}
