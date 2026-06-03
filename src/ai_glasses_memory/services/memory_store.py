from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ai_glasses_memory.models.memory import MemoryEvent, MemoryEventCreate


class MemoryStore:
    """SQLite 记忆时间线存储。"""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def add_event(self, event: MemoryEventCreate) -> MemoryEvent:
        created_at = datetime.now(timezone.utc)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory_events (
                    created_at, question, answer, scene_summary,
                    ocr_text, image_path, latency_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at.isoformat(),
                    event.question,
                    event.answer,
                    event.scene_summary,
                    event.ocr_text,
                    event.image_path,
                    json.dumps(event.latency_ms, ensure_ascii=False),
                ),
            )
            event_id = int(cursor.lastrowid)
        return MemoryEvent(id=event_id, created_at=created_at, **event.model_dump())

    def list_events(self, limit: int = 50) -> list[MemoryEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, question, answer, scene_summary,
                       ocr_text, image_path, latency_ms
                FROM memory_events
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def search_events(self, keyword: str, limit: int = 20) -> list[MemoryEvent]:
        normalized = keyword.strip()
        if not normalized:
            return []

        pattern = f"%{normalized}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, question, answer, scene_summary,
                       ocr_text, image_path, latency_ms
                FROM memory_events
                WHERE question LIKE ?
                   OR answer LIKE ?
                   OR scene_summary LIKE ?
                   OR ocr_text LIKE ?
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ?
                """,
                (pattern, pattern, pattern, pattern, limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    scene_summary TEXT NOT NULL,
                    ocr_text TEXT NOT NULL DEFAULT '',
                    image_path TEXT,
                    latency_ms TEXT NOT NULL DEFAULT '{}'
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> MemoryEvent:
        return MemoryEvent(
            id=int(row["id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            question=row["question"],
            answer=row["answer"],
            scene_summary=row["scene_summary"],
            ocr_text=row["ocr_text"],
            image_path=row["image_path"],
            latency_ms=json.loads(row["latency_ms"]),
        )
