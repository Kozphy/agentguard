import type { AgentAdapterInfo } from "../../shared/types.js";
import { AgentAdapterError, type AgentAdapter } from "./adapter.js";
import { FakeAgentAdapter } from "./fake-adapter.js";

/**
 * Dependency-injected registry of agent adapters.
 * Phase 1 registers only FakeAgentAdapter.
 */
export class AgentRegistry {
  private readonly adapters = new Map<string, AgentAdapter>();

  constructor(adapters: readonly AgentAdapter[] = [new FakeAgentAdapter()]) {
    for (const adapter of adapters) {
      this.register(adapter);
    }
  }

  register(adapter: AgentAdapter): void {
    this.adapters.set(adapter.id, adapter);
  }

  get(adapterId: string): AgentAdapter {
    const adapter = this.adapters.get(adapterId);
    if (!adapter) {
      throw new AgentAdapterError("AGENT_NOT_FOUND", `Unknown adapter: ${adapterId}`);
    }
    return adapter;
  }

  list(): AgentAdapterInfo[] {
    return [...this.adapters.values()].map((adapter) => ({
      id: adapter.id,
      displayName: adapter.displayName,
      status: adapter.getStatus(),
    }));
  }
}
