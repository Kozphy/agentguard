import { dialog } from "electron";
import type { WorkspaceInfo } from "../../shared/types.js";
import { GitError } from "../git/errors.js";
import type { GitService } from "../git/service.js";

export interface DirectoryPicker {
  pickDirectory(): Promise<string | null>;
}

export class ElectronDirectoryPicker implements DirectoryPicker {
  async pickDirectory(): Promise<string | null> {
    const result = await dialog.showOpenDialog({
      properties: ["openDirectory"],
      title: "Open Git repository",
    });
    if (result.canceled || result.filePaths.length === 0) {
      return null;
    }
    return result.filePaths[0] ?? null;
  }
}

/**
 * Holds the currently opened workspace.
 * Selection validates that the path is a Git repository (read-only check).
 */
export class WorkspaceService {
  private current: WorkspaceInfo | null = null;

  constructor(
    private readonly git: GitService,
    private readonly picker: DirectoryPicker,
  ) {}

  getWorkspace(): WorkspaceInfo | null {
    return this.current;
  }

  async selectWorkspace(): Promise<WorkspaceInfo | null> {
    const selected = await this.picker.pickDirectory();
    if (selected === null) {
      return null;
    }

    try {
      await this.git.ensureGitRepository(selected);
    } catch (error) {
      if (error instanceof GitError) {
        throw error;
      }
      throw new GitError(
        "GIT_COMMAND_FAILED",
        error instanceof Error ? error.message : "Failed to validate repository",
      );
    }

    this.current = {
      path: selected,
      isGitRepository: true,
    };
    return this.current;
  }

  /** Test helper to set workspace without a dialog. */
  setWorkspaceForTests(info: WorkspaceInfo | null): void {
    this.current = info;
  }
}
