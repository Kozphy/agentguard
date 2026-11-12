"""Offline, deny-by-default orchestration primitives; no remote agent execution."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

Stage = Literal["P0", "P1", "P2"]
_ALLOWED = {"P0": {"read"}, "P1": {"read", "verify"}, "P2": {"read", "verify", "prepare"}}


@dataclass(frozen=True)
class Task:
    task_id: str
    repository: str
    stage: Stage
    operation: str
    payload_digest: str


def digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_task(task: Task) -> None:
    if task.stage not in _ALLOWED or task.operation not in _ALLOWED[task.stage]:
        raise ValueError("operation not allowed for stage")
    if not task.task_id or "/" not in task.repository or len(task.payload_digest) != 64:
        raise ValueError("invalid task identity")


class ControlPlane:
    """Persistent local task queue; never invokes shell, GitHub writes, or model APIs."""

    def __init__(self, db_path: str | Path) -> None:
        self.connection = sqlite3.connect(str(db_path), timeout=10)
        self.connection.execute("PRAGMA busy_timeout=10000")
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, repository TEXT NOT NULL,
                stage TEXT NOT NULL, operation TEXT NOT NULL,
                digest TEXT NOT NULL, status TEXT NOT NULL,
                lease_owner TEXT, lease_until REAL, evidence_digest TEXT,
                UNIQUE(repository, stage, operation, digest)
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS audit (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL, event TEXT NOT NULL,
                timestamp REAL NOT NULL, metadata TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    def _audit(self, task_id: str, event: str, **metadata: object) -> None:
        self.connection.execute(
            "INSERT INTO audit (task_id,event,timestamp,metadata) VALUES (?,?,?,?)",
            (task_id, event, time.time(), json.dumps(metadata, sort_keys=True)),
        )

    def enqueue(self, task: Task) -> bool:
        validate_task(task)
        with self.connection:
            row = self.connection.execute(
                "SELECT repository,stage,operation,digest FROM tasks WHERE task_id=?",
                (task.task_id,),
            ).fetchone()
            values = (task.repository, task.stage, task.operation, task.payload_digest)
            if row:
                if tuple(row) != values:
                    raise ValueError("conflicting task_id")
                return False
            self.connection.execute(
                """INSERT INTO tasks
                (task_id,repository,stage,operation,digest,status)
                VALUES (?,?,?,?,?,'queued')""",
                (task.task_id, *values),
            )
            self._audit(task.task_id, "queued")
        return True

    def lease(self, owner: str, seconds: int = 60) -> Task | None:
        if not owner or not 1 <= seconds <= 3600:
            raise ValueError("invalid lease")
        now = time.time()
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE") if not self.connection.in_transaction else None
            row = self.connection.execute(
                """SELECT task_id,repository,stage,operation,digest FROM tasks
                WHERE status='queued' OR (status='leased' AND lease_until < ?)
                ORDER BY rowid LIMIT 1""", (now,)
            ).fetchone()
            if row is None:
                return None
            self.connection.execute(
                """UPDATE tasks SET status='leased',lease_owner=?,lease_until=?
                WHERE task_id=?""", (owner, now + seconds, row[0])
            )
            self._audit(row[0], "leased", owner=owner)
        return Task(*row)

    def complete(self, task_id: str, owner: str, evidence: dict[str, object]) -> str:
        if not evidence:
            raise ValueError("evidence required")
        proof = digest_payload(evidence)
        with self.connection:
            result = self.connection.execute(
                """UPDATE tasks SET status='done',evidence_digest=?,lease_until=NULL
                WHERE task_id=? AND status='leased' AND lease_owner=? AND lease_until>=?""",
                (proof, task_id, owner, time.time()),
            )
            if result.rowcount != 1:
                raise PermissionError("not current lease owner")
            self._audit(task_id, "completed", digest=proof)
        return proof

    def status(self, task_id: str) -> str | None:
        row = self.connection.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return row[0] if row else None

    def close(self) -> None:
        self.connection.close()


def authorize_action(operation: str) -> None:
    """A deny-all mutation gate; separate explicit authorization is required."""
    if operation in {"write", "push", "draft_pr", "merge", "deploy", "secrets"}:
        raise PermissionError("mutation requires separate human-authorized implementation")
    if operation not in {"read", "verify", "prepare"}:
        raise PermissionError("unknown operation blocked")
