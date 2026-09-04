import type { AgentGuardDesktopApi } from "../shared/api";

declare global {
  interface Window {
    agentguard: AgentGuardDesktopApi;
  }
}

export {};
