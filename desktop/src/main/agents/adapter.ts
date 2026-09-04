import type {
  AgentDetectResult,
  AgentStartOptions,
  AgentStatus,
} from "../../shared/types.js";

/**
 * Agent backend abstraction.
 * Implementations absorb CLI-specific protocol differences.
 * Phase 1: FakeAgentAdapter only — no real agent execution.
 */
export interface AgentAdapter {
  readonly id: string;
  readonly displayName: string;

  detect(): Promise<AgentDetectResult>;
  start(options: AgentStartOptions): Promise<void>;
  send(input: string): Promise<void>;
  stop(): Promise<void>;
  getStatus(): AgentStatus;
}

export class AgentAdapterError extends Error {
  readonly code: "AGENT_INVALID_STATE" | "AGENT_NOT_FOUND";

  constructor(code: AgentAdapterError["code"], message: string) {
    super(message);
    this.name = "AgentAdapterError";
    this.code = code;
  }
}
