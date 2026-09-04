import { IpcChannels } from "../../shared/ipc-channels.js";
import type { IpcRequest, IpcResponse } from "../../shared/ipc-contracts.js";
import { AgentAdapterError } from "../agents/adapter.js";
import type { AgentRegistry } from "../agents/registry.js";
import { GitError } from "../git/errors.js";
import type { GitService } from "../git/service.js";
import type { WorkspaceService } from "../workspace/service.js";
import { err, ok } from "./result.js";

export interface MainServices {
  workspace: WorkspaceService;
  git: GitService;
  agents: AgentRegistry;
}

export type IpcHandlers = {
  [IpcChannels.workspaceSelect]: () => Promise<IpcResponse<"workspace:select">>;
  [IpcChannels.workspaceGet]: () => Promise<IpcResponse<"workspace:get">>;
  [IpcChannels.workspaceGetStatus]: () => Promise<IpcResponse<"workspace:getStatus">>;
  [IpcChannels.agentsList]: () => Promise<IpcResponse<"agents:list">>;
  [IpcChannels.agentsDetect]: (
    request: IpcRequest<"agents:detect">,
  ) => Promise<IpcResponse<"agents:detect">>;
};

/**
 * Pure handler map — testable without Electron.
 * registerIpcHandlers wires these to ipcMain.
 */
export function createIpcHandlers(services: MainServices): IpcHandlers {
  return {
    [IpcChannels.workspaceSelect]: async () => {
      try {
        const workspace = await services.workspace.selectWorkspace();
        if (workspace === null) {
          return err("CANCELLED", "Repository selection cancelled");
        }
        return ok(workspace);
      } catch (error) {
        return mapError(error);
      }
    },

    [IpcChannels.workspaceGet]: async () => {
      return ok(services.workspace.getWorkspace());
    },

    [IpcChannels.workspaceGetStatus]: async () => {
      const workspace = services.workspace.getWorkspace();
      if (!workspace) {
        return err("NO_WORKSPACE", "No repository is open");
      }
      try {
        const status = await services.git.getStatus(workspace.path);
        return ok(status);
      } catch (error) {
        return mapError(error);
      }
    },

    [IpcChannels.agentsList]: async () => {
      return ok(services.agents.list());
    },

    [IpcChannels.agentsDetect]: async (request) => {
      try {
        const adapter = services.agents.get(request.adapterId);
        const detected = await adapter.detect();
        return ok(detected);
      } catch (error) {
        return mapError(error);
      }
    },
  };
}

function mapError(error: unknown) {
  if (error instanceof GitError) {
    return err(error.code, error.message);
  }
  if (error instanceof AgentAdapterError) {
    return err(error.code, error.message);
  }
  return err(
    "INTERNAL",
    error instanceof Error ? error.message : "Unexpected internal error",
  );
}
