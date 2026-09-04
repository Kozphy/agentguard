from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from agentguard.audit import AuditLog
from agentguard.ollama import OllamaClient
from agentguard.policy import evaluate_command, evaluate_paths
from agentguard.repair_loop import RepairLoopError, run_repair_loop
from agentguard.repository import RepositoryError, diff, status
from agentguard.verifier import run_verification

app = typer.Typer(help="Governed, local-first AI coding agent.", no_args_is_help=True)
console = Console()


def _repo(value: Path) -> Path:
    return value.expanduser().resolve()


def _audit(repo: Path) -> AuditLog:
    return AuditLog(repo / ".agentguard" / "audit.jsonl")


@app.command()
def inspect(repository: Path = typer.Argument(Path("."))) -> None:
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
def show_diff(repository: Path = typer.Argument(Path("."))) -> None:
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
    model: str = typer.Option("qwen2.5-coder:7b", help="Ollama model name."),
    repository: Path = typer.Option(Path("."), "--repo"),
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


@app.command()
def verify(repository: Path = typer.Argument(Path("."))) -> None:
    """Run deterministic pytest, Ruff, and mypy verification gates."""
    repo = _repo(repository)
    try:
        report = run_verification(repo)
    except RepositoryError as error:
        raise typer.BadParameter(str(error)) from error

    payload = {
        "repository": str(repo),
        "passed": report.passed,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "returncode": check.returncode,
            }
            for check in report.checks
        ],
    }
    _audit(repo).write("verification.completed", payload)
    console.print_json(json=payload)
    if not report.passed:
        console.print(Panel(report.failure_summary(), title="Verification failures"))
        raise typer.Exit(1)


@app.command()
def repair(
    task: str,
    files: list[Path] = typer.Option([], "--file", "-f", help="Existing file the model may edit."),
    model: str = typer.Option("qwen2.5-coder:7b", help="Ollama coding model name."),
    max_rounds: int = typer.Option(2, min=1, max=5),
    repository: Path = typer.Option(Path("."), "--repo"),
) -> None:
    """Run AI repair -> deterministic verify -> retry, with rollback on final failure."""
    repo = _repo(repository)
    try:
        outcome = run_repair_loop(
            repo,
            task,
            files,
            model=model,
            max_rounds=max_rounds,
        )
    except (RepositoryError, RepairLoopError) as error:
        raise typer.BadParameter(str(error)) from error

    payload = {
        "repository": str(repo),
        "passed": outcome.passed,
        "rounds": outcome.rounds,
        "rolled_back": outcome.rolled_back,
        "decision": "preview" if outcome.passed and outcome.rounds > 0 else "no-change",
    }
    console.print_json(json=payload)
    if outcome.passed and outcome.rounds > 0:
        console.print(
            Panel(
                "Deterministic verification passed. Review `git diff` before committing or pushing.",
                title="Human review required",
            )
        )
    elif not outcome.passed:
        console.print(Panel("Repair budget exhausted; AI changes were rolled back.", title="Blocked"))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
