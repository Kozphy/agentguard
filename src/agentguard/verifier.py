from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentguard import repository
from agentguard.policy import evaluate_command


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class VerificationReport:
    checks: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def failure_summary(self, max_chars: int = 6000) -> str:
        chunks: list[str] = []
        for check in self.checks:
            if check.passed:
                continue
            body = (check.stdout + "\n" + check.stderr).strip()
            chunks.append(f"## {check.name}\n{body}")
        return "\n\n".join(chunks)[:max_chars]


DEFAULT_CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pytest", ("pytest", "-q")),
    ("ruff", ("ruff", "check", ".")),
    ("mypy", ("mypy", "src")),
)


def run_verification(
    repo: Path,
    checks: tuple[tuple[str, tuple[str, ...]], ...] = DEFAULT_CHECKS,
) -> VerificationReport:
    repository.ensure_git_repository(repo)
    results: list[CheckResult] = []

    for name, command in checks:
        policy = evaluate_command(" ".join(command))
        if policy.decision == "block":
            results.append(
                CheckResult(
                    name=name,
                    command=command,
                    returncode=2,
                    stdout="",
                    stderr="Verification command blocked by policy: " + "; ".join(policy.reasons),
                )
            )
            continue

        completed = repository.run(list(command), repo)
        results.append(
            CheckResult(
                name=name,
                command=command,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )

    return VerificationReport(tuple(results))
