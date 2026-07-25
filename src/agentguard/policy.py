from __future__ import annotations

import re
from pathlib import Path

from agentguard.models import Decision, PolicyResult, RiskLevel

SENSITIVE_PARTS = {
    ".env",
    ".ssh",
    ".aws",
    ".gnupg",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "cookies",
}

BLOCKED_COMMAND_PATTERNS = (
    re.compile(r"(^|\s)rm\s+-rf\s+[/~]"),
    re.compile(r"(^|\s)format(\.com)?\s", re.IGNORECASE),
    re.compile(r"(^|\s)shutdown(\.exe)?\s", re.IGNORECASE),
    re.compile(r"(^|\s)diskpart(\.exe)?(?:\s|$)", re.IGNORECASE),
    re.compile(r"curl\s+.+\|\s*(sh|bash|powershell)", re.IGNORECASE),
)

PREVIEW_COMMAND_PREFIXES = (
    "git push",
    "git reset --hard",
    "git clean",
    "pip install",
    "npm install",
    "pnpm install",
    "docker run",
)


def evaluate_paths(paths: list[Path]) -> PolicyResult:
    reasons: list[str] = []
    for path in paths:
        lowered = {part.lower() for part in path.parts}
        if lowered & SENSITIVE_PARTS:
            reasons.append(f"Sensitive path requested: {path}")

    if reasons:
        return PolicyResult(decision=Decision.BLOCK, risk=RiskLevel.CRITICAL, reasons=reasons)
    return PolicyResult(decision=Decision.ALLOW, risk=RiskLevel.LOW, reasons=[])


def evaluate_command(command: str) -> PolicyResult:
    normalized = " ".join(command.strip().split())
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if pattern.search(normalized):
            return PolicyResult(
                decision=Decision.BLOCK,
                risk=RiskLevel.CRITICAL,
                reasons=[f"Destructive or unsafe command pattern: {normalized}"],
            )

    if normalized.lower().startswith(PREVIEW_COMMAND_PREFIXES):
        return PolicyResult(
            decision=Decision.PREVIEW,
            risk=RiskLevel.HIGH,
            reasons=["Command requires explicit human approval."],
        )

    return PolicyResult(decision=Decision.ALLOW, risk=RiskLevel.LOW, reasons=[])
