import type {
  AgentDetectResult,
  AgentStartOptions,
  AgentStatus,
} from "../../shared/types.js";
import { AgentAdapterError, type AgentAdapter } from "./adapter.js";

export interface FakeAgentAdapterOptions {
  id?: string;
  displayName?: string;
  available?: boolean;
  version?: string;
}

/**
 * In-memory adapter for contract tests and UI scaffolding.
 * Does not spawn processes or touch the filesystem.
 */
export class FakeAgentAdapter implements AgentAdapter {
  readonly id: string;
  readonly displayName: string;

  private status: AgentStatus = "idle";
  private readonly available: boolean;
  private readonly version: string;
  private readonly inbox: string[] = [];
  private lastStartOptions: AgentStartOptions | null = null;

  constructor(options: FakeAgentAdapterOptions = {}) {
    this.id = options.id ?? "fake";
    this.displayName = options.displayName ?? "Fake Agent";
    this.available = options.available ?? true;
    this.version = options.version ?? "0.0.0-fake";
  }

  async detect(): Promise<AgentDetectResult> {
    if (!this.available) {
      return {
        available: false,
        detail: "Fake agent intentionally unavailable",
      };
    }
    return {
      available: true,
      version: this.version,
      detail: "Synthetic adapter for tests",
    };
  }

  async start(options: AgentStartOptions): Promise<void> {
    if (this.status === "running" || this.status === "starting") {
      throw new AgentAdapterError(
        "AGENT_INVALID_STATE",
        `Cannot start adapter '${this.id}' while status is '${this.status}'`,
      );
    }
    this.status = "starting";
    this.lastStartOptions = options;
    this.inbox.length = 0;
    this.status = "running";
  }

  async send(input: string): Promise<void> {
    if (this.status !== "running") {
      throw new AgentAdapterError(
        "AGENT_INVALID_STATE",
        `Cannot send to adapter '${this.id}' while status is '${this.status}'`,
      );
    }
    this.inbox.push(input);
  }

  async stop(): Promise<void> {
    if (this.status === "idle" || this.status === "stopped") {
      this.status = "stopped";
      return;
    }
    this.status = "stopping";
    this.status = "stopped";
  }

  getStatus(): AgentStatus {
    return this.status;
  }

  /** Test helper — not part of AgentAdapter. */
  getInbox(): readonly string[] {
    return [...this.inbox];
  }

  /** Test helper — not part of AgentAdapter. */
  getLastStartOptions(): AgentStartOptions | null {
    return this.lastStartOptions;
  }
}
