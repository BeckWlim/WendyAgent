from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RuntimeStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists conversations (
                    id text primary key,
                    username text,
                    meta_json text not null,
                    created_at text not null
                );

                create table if not exists messages (
                    id integer primary key autoincrement,
                    conversation_id text not null,
                    role text not null,
                    content text not null,
                    created_at text not null
                );

                create table if not exists tool_invocations (
                    id integer primary key autoincrement,
                    conversation_id text,
                    tool_name text not null,
                    args_json text not null,
                    result_json text,
                    created_at text not null
                );

                create table if not exists tasks (
                    id text primary key,
                    kind text not null,
                    status text not null,
                    payload_json text not null,
                    result_json text,
                    error text,
                    created_at text not null,
                    updated_at text not null
                );
                """
            )

    def ensure_conversation(self, conversation_id: str, username: str | None, meta: dict[str, Any]) -> None:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                """
                insert or ignore into conversations (id, username, meta_json, created_at)
                values (?, ?, ?, ?)
                """,
                (conversation_id, username, json.dumps(meta, ensure_ascii=False), now),
            )

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into messages (conversation_id, role, content, created_at)
                values (?, ?, ?, ?)
                """,
                (conversation_id, role, content, self._now()),
            )

    def recent_messages(self, conversation_id: str, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select role, content from messages
                where conversation_id = ?
                order by id desc
                limit ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def record_tool_invocation(
        self,
        conversation_id: str | None,
        tool_name: str,
        args: dict[str, Any],
        result: Any,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into tool_invocations
                (conversation_id, tool_name, args_json, result_json, created_at)
                values (?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    tool_name,
                    json.dumps(args, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False, default=str),
                    self._now(),
                ),
            )

    def upsert_task(
        self,
        task_id: str,
        kind: str,
        status: str,
        payload: dict[str, Any],
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                """
                insert into tasks
                (id, kind, status, payload_json, result_json, error, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                    status = excluded.status,
                    result_json = excluded.result_json,
                    error = excluded.error,
                    updated_at = excluded.updated_at
                """,
                (
                    task_id,
                    kind,
                    status,
                    json.dumps(payload, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False) if result is not None else None,
                    error,
                    now,
                    now,
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()
