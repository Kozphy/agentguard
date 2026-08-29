from pathlib import Path

from agentguard import repository
from agentguard.verifier import CheckResult, VerificationReport, run_verification


def test_verification_report_passes_only_when_all_checks_pass() -> None:
    report = VerificationReport(
        (
            CheckResult("pytest", ("pytest", "-q"), 0, "ok", ""),
            CheckResult("ruff", ("ruff", "check", "."), 1, "", "lint failed"),
        )
    )

    assert report.passed is False
    assert "ruff" in report.failure_summary()
    assert "lint failed" in report.failure_summary()


def test_run_verification_executes_deterministic_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[tuple[list[str], Path]] = []

    monkeypatch.setattr(repository, "ensure_git_repository", lambda path: None)

    def fake_run(command: list[str], cwd: Path) -> repository.CommandResult:
        calls.append((command, cwd))
        return repository.CommandResult(command, 0, "ok", "")

    monkeypatch.setattr(repository, "run", fake_run)
    checks = (("pytest", ("pytest", "-q")),)
    repo = Path("/tmp/example")

    report = run_verification(repo, checks)

    assert report.passed is True
    assert calls == [(["pytest", "-q"], repo)]
