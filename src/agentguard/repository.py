from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class RepositoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def run(command: list[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(command, completed.returncode, completed.stdout, completed.stderr)


def ensure_git_repository(path: Path) -> None:
    result = run(["git", "rev-parse", "--is-inside-work-tree"], path)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RepositoryError(f"Not a Git repository: {path}")


def status(path: Path) -> str:
    ensure_git_repository(path)
    result = run(["git", "status", "--short"], path)
    if result.returncode != 0:
        raise RepositoryError(result.stderr.strip() or "Unable to read Git status")
    return result.stdout


def diff(path: Path) -> str:
    ensure_git_repository(path)
    result = run(["git", "diff", "--no-ext-diff"], path)
    if result.returncode != 0:
        raise RepositoryError(result.stderr.strip() or "Unable to read Git diff")
    return result.stdout
