import { describe, expect, it } from "vitest";
import { GitError } from "../src/main/git/errors.js";
import type { CommandResult, CommandRunner } from "../src/main/git/runner.js";
import { GitService, parseShortStatus } from "../src/main/git/service.js";

function stubRunner(table: Record<string, CommandResult>): CommandRunner {
  return async (_command, args) => {
    const key = args.join(" ");
    const hit = table[key];
    if (!hit) {
      return { code: 1, stdout: "", stderr: `unexpected args: ${key}` };
    }
    return hit;
  };
}

describe("parseShortStatus", () => {
  it("parses porcelain short status lines", () => {
    const entries = parseShortStatus(" M src/app.py\n?? notes.txt\n");
    expect(entries).toEqual([
      { code: " M", path: "src/app.py" },
      { code: "??", path: "notes.txt" },
    ]);
  });

  it("uses the destination path for renames", () => {
    const entries = parseShortStatus("R  old.ts -> new.ts\n");
    expect(entries).toEqual([{ code: "R ", path: "new.ts" }]);
  });
});

describe("GitService", () => {
  it("returns a status snapshot for a valid repository", async () => {
    const git = new GitService(
      stubRunner({
        "rev-parse --is-inside-work-tree": { code: 0, stdout: "true\n", stderr: "" },
        "status --short": { code: 0, stdout: " M README.md\n", stderr: "" },
        "rev-parse --abbrev-ref HEAD": { code: 0, stdout: "main\n", stderr: "" },
      }),
    );

    const snapshot = await git.getStatus("/repo");
    expect(snapshot.branch).toBe("main");
    expect(snapshot.clean).toBe(false);
    expect(snapshot.entries).toEqual([{ code: " M", path: "README.md" }]);
  });

  it("throws NOT_A_GIT_REPOSITORY when rev-parse fails", async () => {
    const git = new GitService(
      stubRunner({
        "rev-parse --is-inside-work-tree": { code: 128, stdout: "", stderr: "fatal" },
      }),
    );

    await expect(git.ensureGitRepository("/not-a-repo")).rejects.toBeInstanceOf(GitError);
    await expect(git.ensureGitRepository("/not-a-repo")).rejects.toMatchObject({
      code: "NOT_A_GIT_REPOSITORY",
    });
  });

  it("marks clean trees with no entries", async () => {
    const git = new GitService(
      stubRunner({
        "rev-parse --is-inside-work-tree": { code: 0, stdout: "true\n", stderr: "" },
        "status --short": { code: 0, stdout: "", stderr: "" },
        "rev-parse --abbrev-ref HEAD": { code: 0, stdout: "main\n", stderr: "" },
      }),
    );

    const snapshot = await git.getStatus("/repo");
    expect(snapshot.clean).toBe(true);
    expect(snapshot.entries).toEqual([]);
  });
});
