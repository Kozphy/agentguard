import { describe, expect, it } from "vitest";
import { GitError } from "../src/main/git/errors.js";
import type { CommandResult, CommandRunner } from "../src/main/git/runner.js";
import { GitService } from "../src/main/git/service.js";
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

class FakePicker implements DirectoryPicker {
  constructor(private readonly path: string | null) {}

  async pickDirectory(): Promise<string | null> {
    return this.path;
  }
}

describe("WorkspaceService", () => {
  it("returns null when the picker is cancelled", async () => {
    const git = new GitService(stubRunner({}));
    const workspace = new WorkspaceService(git, new FakePicker(null));
    await expect(workspace.selectWorkspace()).resolves.toBeNull();
    expect(workspace.getWorkspace()).toBeNull();
  });

  it("stores a validated Git repository", async () => {
    const git = new GitService(
      stubRunner({
        "rev-parse --is-inside-work-tree": { code: 0, stdout: "true\n", stderr: "" },
      }),
    );
    const workspace = new WorkspaceService(git, new FakePicker("C:\\repo"));
    const selected = await workspace.selectWorkspace();
    expect(selected).toEqual({ path: "C:\\repo", isGitRepository: true });
    expect(workspace.getWorkspace()?.path).toBe("C:\\repo");
  });

  it("rejects non-Git directories", async () => {
    const git = new GitService(
      stubRunner({
        "rev-parse --is-inside-work-tree": { code: 128, stdout: "", stderr: "fatal" },
      }),
    );
    const workspace = new WorkspaceService(git, new FakePicker("/tmp/plain"));
    await expect(workspace.selectWorkspace()).rejects.toBeInstanceOf(GitError);
    expect(workspace.getWorkspace()).toBeNull();
  });
});
