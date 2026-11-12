"""Offline tests for P0-P2 control-plane safety."""
import pytest

from agentguard.control_plane import ControlPlane, Task, authorize_action, digest_payload


def task(operation="read", stage="P0", task_id="issue-1"):
    return Task(task_id, "Kozphy/agentguard", stage, operation, digest_payload({"issue": 1}))


def test_deny_mutation_and_invalid_stage():
    for operation in ["write", "push", "draft_pr", "merge", "deploy", "secrets", "unknown"]:
        with pytest.raises(PermissionError):
            authorize_action(operation)
    with pytest.raises(ValueError):
        ControlPlane(":memory:").enqueue(task(operation="prepare", stage="P0"))


def test_idempotency_and_conflicting_ids(tmp_path):
    q = ControlPlane(tmp_path / "queue.sqlite")
    assert q.enqueue(task())
    assert not q.enqueue(task())
    with pytest.raises(ValueError):
        q.enqueue(task(operation="verify", stage="P1"))


def test_lease_requires_owner_and_evidence(tmp_path):
    q = ControlPlane(tmp_path / "queue.sqlite")
    q.enqueue(task(operation="verify", stage="P1"))
    claimed = q.lease("worker-1")
    assert claimed == task(operation="verify", stage="P1")
    assert q.lease("worker-2") is None
    with pytest.raises(PermissionError):
        q.complete(claimed.task_id, "worker-2", {"passed": True})
    with pytest.raises(ValueError):
        q.complete(claimed.task_id, "worker-1", {})
    assert q.complete(claimed.task_id, "worker-1", {"passed": True})
    assert q.status(claimed.task_id) == "done"


def test_persistence(tmp_path):
    db = tmp_path / "queue.sqlite"
    first = ControlPlane(db)
    first.enqueue(task())
    first.close()
    second = ControlPlane(db)
    assert second.status("issue-1") == "queued"
    second.close()
