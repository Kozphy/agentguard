import { describe, expect, it } from "vitest";
import { FakeAgentAdapter } from "../src/main/agents/fake-adapter.js";
import { AgentRegistry } from "../src/main/agents/registry.js";
import type { CommandResult, CommandRunner } from "../src/main/git/runner.js";
import { GitService } from "../src/main/git/service.js";
import { createIpcHandlers } from "../src/main/ipc/handlers.js";
import { IpcChannels } from "../src/shared/ipc-channels.js";
import type { IpcContractMap } from "../src/shared/ipc-contracts.js";
import {
  WorkspaceService,
  type DirectoryPicker,
} from "../src/main/workspace/service.js";

function stubRunner(table: Record<string, CommandResult>): CommandRunner {
  return async (_command, args) => {
    const key = args.join(" ");
    return table[key] ?? { code: 1, stdout: "", stderr: `unexpected: ${key}` };
  };
}

class ScriptedPicker implements DirectoryPicker {
  constructor(private readonly paths: Array<string | null>) {}

  async pickDirectory(): Promise<string | null> {
    return this.paths.shift() ?? null;
  }
}

function buildServices(options?: {
  pickerPaths?: Array<string | null>;
  runner?: CommandRunner;
  adapters?: FakeAgentAdapter[];
}) {
  const git = new GitService(
    options?.runner ??
      stubRunner({
        "rev-parse --is-inside-work-tree": { code: 0, stdout: "true\n", stderr: "" },
        "status --short": { code: 0, stdout: "?? desktop/\n", stderr: "" },
        "rev-parse --abbrev-ref HEAD": { code: 0, stdout: "main\n", stderr: "" },
      }),
  );
  const workspace = new WorkspaceService(
    git,
    new ScriptedPicker(options?.pickerPaths ?? ["C:\\agentguard"]),
  );
  const agents = new AgentRegistry(options?.adapters ?? [new FakeAgentAdapter()]);
  return { git, workspace, agents };
}

describe("IPC contracts", () => {
  it("exposes only the Phase 1 channel set", () => {
    const channels = Object.values(IpcChannels).sort();
    expect(channels).toEqual(
      [
        "agents:detect",
        "agents:list",
        "workspace:get",
        "workspace:getStatus",
        "workspace:select",
      ].sort(),
    );

    const contractKeys = Object.keys({
      "workspace:select": true,
      "workspace:get": true,
      "workspace:getStatus": true,
      "agents:list": true,
      "agents:detect": true,
    } satisfies Record<keyof IpcContractMap, true>).sort();
    expect(contractKeys).toEqual(channels);
  });
});

describe("createIpcHandlers", () => {
  it("selects a workspace and returns git status through typed results", async () => {
    const handlers = createIpcHandlers(buildServices());

    const selected = await handlers[IpcChannels.workspaceSelect]();
    expect(selected.ok).toBe(true);
    if (!selected.ok) {
      return;
    }
    expect(selected.value.path).toBe("C:\\agentguard");

    const current = await handlers[IpcChannels.workspaceGet]();
    expect(current).toEqual({
      ok: true,
      value: { path: "C:\\agentguard", isGitRepository: true },
    });

    const status = await handlers[IpcChannels.workspaceGetStatus]();
    expect(status.ok).toBe(true);
    if (!status.ok) {
      return;
    }
    expect(status.value.branch).toBe("main");
    expect(status.value.entries).toEqual([{ code: "??", path: "desktop/" }]);
  });

  it("returns CANCELLED when directory picking is aborted", async () => {
    const handlers = createIpcHandlers(buildServices({ pickerPaths: [null] }));
    const result = await handlers[IpcChannels.workspaceSelect]();
    expect(result).toEqual({
      ok: false,
      error: { code: "CANCELLED", message: "Repository selection cancelled" },
    });
  });

  it("returns NO_WORKSPACE when status is requested too early", async () => {
    const handlers = createIpcHandlers(buildServices({ pickerPaths: [] }));
    const result = await handlers[IpcChannels.workspaceGetStatus]();
    expect(result.ok).toBe(false);
    if (result.ok) {
      return;
    }
    expect(result.error.code).toBe("NO_WORKSPACE");
  });

  it("lists adapters and detects the fake agent", async () => {
    const handlers = createIpcHandlers(
      buildServices({
        adapters: [new FakeAgentAdapter({ id: "fake", version: "1.2.3-test" })],
      }),
    );

    const listed = await handlers[IpcChannels.agentsList]();
    expect(listed.ok).toBe(true);
    if (!listed.ok) {
      return;
    }
    expect(listed.value[0]?.id).toBe("fake");

    const detected = await handlers[IpcChannels.agentsDetect]({ adapterId: "fake" });
    expect(detected).toEqual({
      ok: true,
      value: {
        available: true,
        version: "1.2.3-test",
        detail: "Synthetic adapter for tests",
      },
    });
  });

  it("maps unknown adapters to AGENT_NOT_FOUND", async () => {
    const handlers = createIpcHandlers(buildServices({ adapters: [] }));
    const result = await handlers[IpcChannels.agentsDetect]({ adapterId: "codex" });
    expect(result.ok).toBe(false);
    if (result.ok) {
      return;
    }
    expect(result.error.code).toBe("AGENT_NOT_FOUND");
  });

  it("maps non-git selection failures to typed errors", async () => {
    const handlers = createIpcHandlers(
      buildServices({
        pickerPaths: ["/tmp/not-git"],
        runner: stubRunner({
          "rev-parse --is-inside-work-tree": { code: 128, stdout: "", stderr: "fatal" },
        }),
      }),
    );
    const result = await handlers[IpcChannels.workspaceSelect]();
    expect(result.ok).toBe(false);
    if (result.ok) {
      return;
    }
    expect(result.error.code).toBe("NOT_A_GIT_REPOSITORY");
  });
});
