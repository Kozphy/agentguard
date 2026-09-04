import { ipcMain } from "electron";
import { IpcChannels } from "../../shared/ipc-channels.js";
import { createIpcHandlers, type MainServices } from "./handlers.js";

export type { MainServices } from "./handlers.js";

/**
 * Registers typed IPC handlers.
 * All privileged operations stay in the main process.
 */
export function registerIpcHandlers(services: MainServices): void {
  const handlers = createIpcHandlers(services);

  ipcMain.removeHandler(IpcChannels.workspaceSelect);
  ipcMain.removeHandler(IpcChannels.workspaceGet);
  ipcMain.removeHandler(IpcChannels.workspaceGetStatus);
  ipcMain.removeHandler(IpcChannels.agentsList);
  ipcMain.removeHandler(IpcChannels.agentsDetect);

  ipcMain.handle(IpcChannels.workspaceSelect, () => handlers[IpcChannels.workspaceSelect]());
  ipcMain.handle(IpcChannels.workspaceGet, () => handlers[IpcChannels.workspaceGet]());
  ipcMain.handle(IpcChannels.workspaceGetStatus, () =>
    handlers[IpcChannels.workspaceGetStatus](),
  );
  ipcMain.handle(IpcChannels.agentsList, () => handlers[IpcChannels.agentsList]());
  ipcMain.handle(
    IpcChannels.agentsDetect,
    (_event, request: { adapterId: string }) => handlers[IpcChannels.agentsDetect](request),
  );
}
