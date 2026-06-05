from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VectorSearchResult:
    memory_id: int
    score: float


class SQLiteVectorIndex:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def upsert(self, memory_id: int, vector: list[float], text: str) -> None:
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO memory_vectors (memory_id, vector_json, text)
                    VALUES (?, ?, ?)
                    ON CONFLICT(memory_id) DO UPDATE SET
                        vector_json = excluded.vector_json,
                        text = excluded.text
                    """,
                    (memory_id, json.dumps(vector), text),
                )

    def search(self, query_vector: list[float], limit: int = 20) -> list[VectorSearchResult]:
        if limit <= 0:
            return []

        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT memory_id, vector_json FROM memory_vectors").fetchall()

        scored = []
        for row in rows:
            vector = [float(value) for value in json.loads(row["vector_json"])]
            score = self._cosine_similarity(query_vector, vector)
            if score >= 0:
                scored.append(VectorSearchResult(memory_id=int(row["memory_id"]), score=score))

        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:limit]

    def delete(self, memory_id: int) -> int:
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute("DELETE FROM memory_vectors WHERE memory_id = ?", (memory_id,))
                return int(cursor.rowcount)

    def clear(self) -> int:
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute("DELETE FROM memory_vectors")
                return int(cursor.rowcount)

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_vectors (
                        memory_id INTEGER PRIMARY KEY,
                        vector_json TEXT NOT NULL,
                        text TEXT NOT NULL DEFAULT ''
                    )
                    """
                )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)
