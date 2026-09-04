import type { IpcContractMap, IpcRequest, IpcResponse } from "./ipc-contracts.js";

/**
 * API exposed to the renderer via contextBridge.
 * No Node, filesystem, or spawn primitives are included.
 */
export interface AgentGuardDesktopApi {
  selectWorkspace: () => Promise<IpcResponse<"workspace:select">>;
  getWorkspace: () => Promise<IpcResponse<"workspace:get">>;
  getWorkspaceStatus: () => Promise<IpcResponse<"workspace:getStatus">>;
  listAgents: () => Promise<IpcResponse<"agents:list">>;
  detectAgent: (
    request: IpcRequest<"agents:detect">,
  ) => Promise<IpcResponse<"agents:detect">>;
}

export type { IpcContractMap };
