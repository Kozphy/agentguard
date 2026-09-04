/** Decision vocabulary mirrored from Python AgentGuard models. */
export type PolicyDecision = "allow" | "preview" | "block";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface PolicyResult {
  decision: PolicyDecision;
  risk: RiskLevel;
  reasons: string[];
}

export interface WorkspaceInfo {
  path: string;
  isGitRepository: boolean;
}

export interface GitStatusEntry {
  /** Two-character porcelain status code, e.g. " M", "??". */
  code: string;
  path: string;
}

export interface GitStatusSnapshot {
  repositoryPath: string;
  branch: string | null;
  clean: boolean;
  entries: GitStatusEntry[];
  raw: string;
}

export type AgentStatus =
  | "idle"
  | "starting"
  | "running"
  | "stopping"
  | "stopped"
  | "error";

export interface AgentDetectResult {
  available: boolean;
  version?: string;
  detail?: string;
}

export interface AgentStartOptions {
  workspacePath: string;
  worktreePath?: string;
  taskPrompt: string;
}

export interface AgentAdapterInfo {
  id: string;
  displayName: string;
  status: AgentStatus;
}

export type AppErrorCode =
  | "CANCELLED"
  | "NOT_A_GIT_REPOSITORY"
  | "GIT_COMMAND_FAILED"
  | "NO_WORKSPACE"
  | "AGENT_NOT_FOUND"
  | "AGENT_INVALID_STATE"
  | "INTERNAL";

export interface AppError {
  code: AppErrorCode;
  message: string;
}

export type Result<T> = { ok: true; value: T } | { ok: false; error: AppError };
