from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentguard.audit import AuditLog
from agentguard.ollama import OllamaClient
from agentguard.policy import evaluate_paths
from agentguard.repository import RepositoryError, status
from agentguard.verifier import VerificationReport, run_verification


class RepairLoopError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepairOutcome:
    passed: bool
    rounds: int
    verification: VerificationReport
    rolled_back: bool = False


def _extract_diff(text: str) -> str:
    fenced = re.search(r"```diff\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip() + "\n"

    start = text.find("diff --git ")
    if start >= 0:
        return text[start:].strip() + "\n"

    raise RepairLoopError("Model did not return a unified diff.")


def _patch_paths(patch: str) -> set[Path]:
    paths: set[Path] = set()
    for line in patch.splitlines():
        if not line.startswith("+++ "):
            continue
        raw = line[4:].strip()
        if raw == "/dev/null":
            raise RepairLoopError("Creating new files is not allowed in v0.2 repair mode.")
        if raw.startswith("b/"):
            raw = raw[2:]
        paths.add(Path(raw))
    if not paths:
        raise RepairLoopError("Patch does not modify any files.")
    return paths


def _validate_patch(patch: str, allowed_files: set[Path]) -> None:
    changed = _patch_paths(patch)
    if not changed <= allowed_files:
        unexpected = sorted(str(path) for path in changed - allowed_files)
        raise RepairLoopError("Patch touched files outside the allowlist: " + ", ".join(unexpected))


def _apply_patch(repo: Path, patch: str) -> None:
    check = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=repo,
        input=patch,
        text=True,
        capture_output=True,
        check=False,
    )
    if check.returncode != 0:
        raise RepairLoopError(check.stderr.strip() or "git apply --check failed")

    applied = subprocess.run(
        ["git", "apply", "-"],
        cwd=repo,
        input=patch,
        text=True,
        capture_output=True,
        check=False,
    )
    if applied.returncode != 0:
        raise RepairLoopError(applied.stderr.strip() or "git apply failed")


def _restore(repo: Path, files: list[Path]) -> None:
    command = ["git", "restore", "--", *(str(path) for path in files)]
    restored = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    if restored.returncode != 0:
        raise RepairLoopError(restored.stderr.strip() or "Unable to roll back failed repair")


def _file_context(repo: Path, files: list[Path], max_chars: int = 30000) -> str:
    chunks: list[str] = []
    remaining = max_chars
    for path in files:
        full_path = repo / path
        if not full_path.is_file():
            raise RepairLoopError(f"Allowed file does not exist: {path}")
        content = full_path.read_text(encoding="utf-8")
        chunk = f"\n### FILE: {path}\n```\n{content}\n```\n"
        if len(chunk) > remaining:
            raise RepairLoopError("Selected file context exceeds the repair context budget.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return "".join(chunks)


def _build_prompt(
    task: str,
    repo: Path,
    files: list[Path],
    verification: VerificationReport,
) -> str:
    context = _file_context(repo, files)
    failures = verification.failure_summary()
    allowlist = ", ".join(str(path) for path in files)
    return f"""You are a coding repair agent operating under strict change control.

Task:
{task}

Repository:
{repo}

Allowed existing files only:
{allowlist}

Current deterministic verification failures:
{failures or '(none)'}

Rules:
- Return exactly one unified git diff and no prose.
- Modify only the allowed existing files.
- Do not create, delete, or rename files.
- Make the smallest change that addresses the failures and task.
- Do not weaken or delete tests merely to make verification pass.
- Do not add secrets, network calls, or destructive commands.

Repository file context:
{context}
"""


def run_repair_loop(
    repo: Path,
    task: str,
    files: list[Path],
    *,
    model: str = "qwen2.5-coder:7b",
    max_rounds: int = 2,
    client: OllamaClient | None = None,
) -> RepairOutcome:
    repo = repo.expanduser().resolve()
    normalized_files = [Path(path) for path in files]
    if not normalized_files:
        raise RepairLoopError("At least one --file is required.")
    if max_rounds < 1 or max_rounds > 5:
        raise RepairLoopError("max_rounds must be between 1 and 5.")

    if status(repo).strip():
        raise RepositoryError("Repair mode requires a clean working tree.")

    policy = evaluate_paths(normalized_files)
    if policy.decision == "block":
        raise RepairLoopError("Selected paths were blocked by policy: " + "; ".join(policy.reasons))

    for path in normalized_files:
        if path.is_absolute() or ".." in path.parts:
            raise RepairLoopError(f"Unsafe repair path: {path}")

    audit = AuditLog(repo / ".agentguard" / "audit.jsonl")
    verification = run_verification(repo)
    audit.write(
        "repair.baseline_verified",
        {
            "repository": str(repo),
            "task": task,
            "files": [str(path) for path in normalized_files],
            "passed": verification.passed,
        },
    )
    if verification.passed:
        return RepairOutcome(True, 0, verification)

    model_client = client or OllamaClient()
    allowed = set(normalized_files)
    applied_any_patch = False

    try:
        for round_number in range(1, max_rounds + 1):
            prompt = _build_prompt(task, repo, normalized_files, verification)
            response = model_client.generate(model, prompt)
            patch = _extract_diff(response)
            _validate_patch(patch, allowed)
            _apply_patch(repo, patch)
            applied_any_patch = True

            audit.write(
                "repair.patch_applied",
                {
                    "repository": str(repo),
                    "task": task,
                    "model": model,
                    "round": round_number,
                    "files": [str(path) for path in sorted(_patch_paths(patch), key=str)],
                },
            )

            verification = run_verification(repo)
            audit.write(
                "repair.round_verified",
                {
                    "repository": str(repo),
                    "round": round_number,
                    "passed": verification.passed,
                    "failures": verification.failure_summary(2000),
                },
            )
            if verification.passed:
                audit.write(
                    "repair.completed",
                    {
                        "repository": str(repo),
                        "task": task,
                        "rounds": round_number,
                        "decision": "preview",
                        "reason": "Verification passed; human review is still required before commit/push.",
                    },
                )
                return RepairOutcome(True, round_number, verification)

        _restore(repo, normalized_files)
        audit.write(
            "repair.rolled_back",
            {
                "repository": str(repo),
                "task": task,
                "rounds": max_rounds,
                "reason": "Deterministic verification still failed after the repair budget.",
            },
        )
        return RepairOutcome(False, max_rounds, verification, rolled_back=True)
    except Exception:
        if applied_any_patch:
            _restore(repo, normalized_files)
            audit.write(
                "repair.rolled_back",
                {
                    "repository": str(repo),
                    "task": task,
                    "reason": "Repair loop raised an error after applying a patch.",
                },
            )
        raise
