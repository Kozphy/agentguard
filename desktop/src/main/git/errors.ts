export class GitError extends Error {
  readonly code: "NOT_A_GIT_REPOSITORY" | "GIT_COMMAND_FAILED";

  constructor(code: GitError["code"], message: string) {
    super(message);
    this.name = "GitError";
    this.code = code;
  }
}
