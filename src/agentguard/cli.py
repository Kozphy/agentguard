from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from agentguard.audit import AuditLog
from agentguard.ollama import OllamaClient
from agentguard.policy import evaluate_command, evaluate_paths
from agentguard.repository import RepositoryError, diff, status

app = typer.Typer(help="Governed, local-first AI coding agent.", no_args_is_help=True)
console = Console()

RepositoryArgument = Annotated[Path, typer.Argument()]
RepositoryOption = Annotated[Path, typer.Option("--repo")]
ModelOption = Annotated[str, typer.Option(help="Ollama model name.")]


def _repo(value: Path) -> Path:
    return value.expanduser().resolve()


def _audit(repo: Path) -> AuditLog:
    return AuditLog(repo / ".agentguard" / "audit.jsonl")


@app.command()
def inspect(repository: RepositoryArgument = Path(".")) -> None:
    """Inspect Git state without modifying files."""
    repo = _repo(repository)
    try:
        git_status = status(repo)
    except RepositoryError as error:
        raise typer.BadParameter(str(error)) from error
    payload = {"repository": str(repo), "status": git_status}
    _audit(repo).write("repository.inspected", payload)
    console.print(Panel(git_status or "Working tree clean", title=str(repo)))


@app.command("check-path")
def check_path(paths: list[Path]) -> None:
    """Evaluate whether file paths are safe for an agent to access."""
    result = evaluate_paths(paths)
    console.print_json(json=result.model_dump(mode="json"))
    if result.decision == "block":
        raise typer.Exit(2)


@app.command("check-command")
def check_command(command: str) -> None:
    """Evaluate a shell command before execution."""
    result = evaluate_command(command)
    console.print_json(json=result.model_dump(mode="json"))
    if result.decision == "block":
        raise typer.Exit(2)


@app.command()
def show_diff(repository: RepositoryArgument = Path(".")) -> None:
    """Show uncommitted changes and write an audit event."""
    repo = _repo(repository)
    try:
        content = diff(repo)
    except RepositoryError as error:
        raise typer.BadParameter(str(error)) from error
    _audit(repo).write("repository.diff_viewed", {"repository": str(repo), "bytes": len(content)})
    console.print(content or "No uncommitted diff.")


@app.command()
def ask(
    prompt: str,
    model: ModelOption = "qwen2.5-coder:7b",
    repository: RepositoryOption = Path("."),
) -> None:
    """Ask a local model for analysis. This command never writes project files."""
    repo = _repo(repository)
    try:
        git_status = status(repo)
    except RepositoryError as error:
        raise typer.BadParameter(str(error)) from error

    guarded_prompt = f"""You are analyzing a software repository in read-only mode.
Do not claim to have modified files or executed commands.
Repository: {repo}
Git status:\n{git_status or '(clean)'}

User task:\n{prompt}

Return: findings, risks, and a minimal testable plan.
"""
    answer = OllamaClient().generate(model, guarded_prompt)
    _audit(repo).write(
        "model.asked",
        {"repository": str(repo), "model": model, "prompt": prompt, "mode": "read-only"},
    )
    console.print(Panel(answer, title=f"AgentGuard · {model}"))


if __name__ == "__main__":
    app()
