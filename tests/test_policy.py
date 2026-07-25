from pathlib import Path

from agentguard.models import Decision, RiskLevel
from agentguard.policy import evaluate_command, evaluate_paths


def test_blocks_env_file() -> None:
    result = evaluate_paths([Path("project/.env")])
    assert result.decision is Decision.BLOCK
    assert result.risk is RiskLevel.CRITICAL


def test_allows_normal_source_file() -> None:
    result = evaluate_paths([Path("src/app.py")])
    assert result.decision is Decision.ALLOW


def test_blocks_destructive_rm() -> None:
    result = evaluate_command("rm -rf /")
    assert result.decision is Decision.BLOCK


def test_requires_preview_for_git_push() -> None:
    result = evaluate_command("git push origin feature")
    assert result.decision is Decision.PREVIEW
    assert result.risk is RiskLevel.HIGH


def test_allows_pytest() -> None:
    result = evaluate_command("pytest tests/test_policy.py -q")
    assert result.decision is Decision.ALLOW
