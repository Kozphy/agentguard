import type {
  AgentAdapterInfo,
  AgentDetectResult,
  GitStatusSnapshot,
  Result,
  WorkspaceInfo,
} from "./types.js";

/** Request/response contracts for Phase 1 IPC. */
export interface IpcContractMap {
  "workspace:select": {
    request: void;
    response: Result<WorkspaceInfo>;
  };
  "workspace:get": {
    request: void;
    response: Result<WorkspaceInfo | null>;
  };
  "workspace:getStatus": {
    request: void;
    response: Result<GitStatusSnapshot>;
  };
  "agents:list": {
    request: void;
    response: Result<AgentAdapterInfo[]>;
  };
  "agents:detect": {
    request: { adapterId: string };
    response: Result<AgentDetectResult>;
  };
}

export type IpcRequest<C extends keyof IpcContractMap> = IpcContractMap[C]["request"];
export type IpcResponse<C extends keyof IpcContractMap> = IpcContractMap[C]["response"];
