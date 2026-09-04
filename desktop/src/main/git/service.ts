import type { GitStatusEntry, GitStatusSnapshot } from "../../shared/types.js";
import { GitError } from "./errors.js";
import { defaultCommandRunner, type CommandRunner } from "./runner.js";

/**
 * Read-only Git helpers for Phase 1.
 * Mirrors the intent of Python `agentguard.repository.status`.
 * Does not mutate the repository.
 */
export class GitService {
  constructor(private readonly run: CommandRunner = defaultCommandRunner) {}

  async ensureGitRepository(repositoryPath: string): Promise<void> {
    const result = await this.run("git", ["rev-parse", "--is-inside-work-tree"], repositoryPath);
    if (result.code !== 0 || result.stdout.trim() !== "true") {
      throw new GitError("NOT_A_GIT_REPOSITORY", `Not a Git repository: ${repositoryPath}`);
    }
  }

  async getBranch(repositoryPath: string): Promise<string | null> {
    const result = await this.run(
      "git",
      ["rev-parse", "--abbrev-ref", "HEAD"],
      repositoryPath,
    );
    if (result.code !== 0) {
      return null;
    }
    const branch = result.stdout.trim();
    return branch.length > 0 ? branch : null;
  }

  async getStatus(repositoryPath: string): Promise<GitStatusSnapshot> {
    await this.ensureGitRepository(repositoryPath);

    const result = await this.run("git", ["status", "--short"], repositoryPath);
    if (result.code !== 0) {
      throw new GitError(
        "GIT_COMMAND_FAILED",
        result.stderr.trim() || "Unable to read Git status",
      );
    }

    const raw = result.stdout;
    const entries = parseShortStatus(raw);
    const branch = await this.getBranch(repositoryPath);

    return {
      repositoryPath,
      branch,
      clean: entries.length === 0,
      entries,
      raw,
    };
  }
}

export function parseShortStatus(raw: string): GitStatusEntry[] {
  const lines = raw.split(/\r?\n/).filter((line) => line.length > 0);
  const entries: GitStatusEntry[] = [];

  for (const line of lines) {
    if (line.length < 4) {
      continue;
    }
    const code = line.slice(0, 2);
    let pathPart = line.slice(3);

    // Handle rename lines: "R  old -> new"
    const renameSeparator = " -> ";
    if (pathPart.includes(renameSeparator)) {
      pathPart = pathPart.slice(pathPart.lastIndexOf(renameSeparator) + renameSeparator.length);
    }

    entries.push({ code, path: pathPart });
  }

  return entries;
}
