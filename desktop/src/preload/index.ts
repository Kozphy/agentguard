import { contextBridge, ipcRenderer } from "electron";
import type { AgentGuardDesktopApi } from "../shared/api.js";
import { IpcChannels } from "../shared/ipc-channels.js";

const api: AgentGuardDesktopApi = {
  selectWorkspace: () => ipcRenderer.invoke(IpcChannels.workspaceSelect),
  getWorkspace: () => ipcRenderer.invoke(IpcChannels.workspaceGet),
  getWorkspaceStatus: () => ipcRenderer.invoke(IpcChannels.workspaceGetStatus),
  listAgents: () => ipcRenderer.invoke(IpcChannels.agentsList),
  detectAgent: (request) => ipcRenderer.invoke(IpcChannels.agentsDetect, request),
};

contextBridge.exposeInMainWorld("agentguard", api);
