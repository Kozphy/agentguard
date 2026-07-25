import json
from pathlib import Path

from agentguard.audit import AuditLog


def test_writes_jsonl_record(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    AuditLog(path).write("test.event", {"ok": True})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "test.event"
    assert record["payload"] == {"ok": True}
    assert record["timestamp"]
