from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from ai_glasses_memory.models.memory import MemoryEvent, MemoryEventCreate


class MemoryStore:
    """SQLite 记忆时间线存储。"""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def add_event(self, event: MemoryEventCreate) -> MemoryEvent:
        created_at = datetime.now(timezone.utc)
        with closing(self._connect()) as conn:
            with conn:
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
        with closing(self._connect()) as conn:
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
        with closing(self._connect()) as conn:
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

    def delete_event(self, event_id: int) -> int:
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute("DELETE FROM memory_events WHERE id = ?", (event_id,))
                return int(cursor.rowcount)

    def clear_events(self) -> int:
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute("DELETE FROM memory_events")
                return int(cursor.rowcount)

    def prune_events(self, keep_latest: int) -> int:
        if keep_latest <= 0:
            return self.clear_events()

        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    DELETE FROM memory_events
                    WHERE id NOT IN (
                        SELECT id
                        FROM memory_events
                        ORDER BY datetime(created_at) DESC, id DESC
                        LIMIT ?
                    )
                    """,
                    (keep_latest,),
                )
                return int(cursor.rowcount)

    def dedupe_events(self) -> int:
        events = self.list_events(limit=10000)
        seen_keys: set[tuple[str, ...]] = set()
        duplicate_ids: list[int] = []

        for event in events:
            key = self._dedupe_key(event)
            if key in seen_keys:
                duplicate_ids.append(event.id)
            else:
                seen_keys.add(key)

        if not duplicate_ids:
            return 0

        placeholders = ",".join("?" for _ in duplicate_ids)
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute(
                    f"DELETE FROM memory_events WHERE id IN ({placeholders})",
                    duplicate_ids,
                )
                return int(cursor.rowcount)

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            with conn:
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

    @staticmethod
    def _dedupe_key(event: MemoryEvent) -> tuple[str, ...]:
        normalized_question = MemoryStore._normalize_text(event.question)
        normalized_ocr = MemoryStore._normalize_ocr_text(event.ocr_text)
        if normalized_ocr:
            return ("question_ocr", normalized_question, normalized_ocr)

        return (
            "exact",
            normalized_question,
            MemoryStore._normalize_text(event.answer),
            MemoryStore._normalize_text(event.scene_summary),
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = re.sub(r"\s+", "", value.strip().lower())
        return normalized.strip("。！？!?.,，、；;：:")

    @staticmethod
    def _normalize_ocr_text(value: str) -> str:
        normalized = MemoryStore._normalize_text(value)
        return re.sub(r"^(paddleocr|mockocr|模拟ocr)[:：]", "", normalized)
