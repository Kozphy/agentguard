/**
 * Typed IPC channel names.
 * Renderer may only invoke these through the preload bridge.
 */
export const IpcChannels = {
  workspaceSelect: "workspace:select",
  workspaceGet: "workspace:get",
  workspaceGetStatus: "workspace:getStatus",
  agentsList: "agents:list",
  agentsDetect: "agents:detect",
} as const;

export type IpcChannel = (typeof IpcChannels)[keyof typeof IpcChannels];
