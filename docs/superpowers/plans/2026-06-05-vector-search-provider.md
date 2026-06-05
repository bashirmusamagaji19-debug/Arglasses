# Vector Search Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-first vector semantic search provider that can replace the current lightweight rule-based search without changing the Streamlit/FastAPI search surface.

**Architecture:** Keep `SearchProvider` as the boundary. Add an `EmbeddingProvider` boundary, a SQLite-backed vector index, and a `VectorSearchProvider` that embeds memory text and queries, stores vectors by `memory_event.id`, and falls back to the existing lightweight provider when vector search is disabled.

**Tech Stack:** Python 3.11, SQLite, standard-library math/hashlib/json, optional future `sentence-transformers`, pytest.

---

## File Map

- Create `src/ai_glasses_memory/services/embedding.py`: embedding provider protocol plus deterministic local provider and optional sentence-transformers provider factory.
- Create `src/ai_glasses_memory/services/vector_index.py`: SQLite vector table, cosine similarity, rebuild/delete/clear helpers.
- Modify `src/ai_glasses_memory/services/search.py`: add `VectorSearchProvider` while preserving `LightweightSemanticSearchProvider`.
- Modify `src/ai_glasses_memory/services/pipeline.py`: add vector index synchronization after ask/delete/clear/prune/dedupe when vector search is enabled.
- Modify `src/ai_glasses_memory/api/routes.py` and `src/ai_glasses_memory/ui/streamlit_app.py`: create the configured search provider.
- Modify `src/ai_glasses_memory/config.py`: add search and embedding settings.
- Modify `.env.example`, `README.md`, `docs/phase3-search.md`: document local-first vector search.
- Test `tests/test_embedding.py`, `tests/test_vector_index.py`, `tests/test_search_provider.py`, `tests/test_pipeline.py`, `tests/test_config.py`.

## Task 1: Embedding Provider Boundary

**Files:**
- Create: `src/ai_glasses_memory/services/embedding.py`
- Test: `tests/test_embedding.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing tests for deterministic local embeddings**

Create `tests/test_embedding.py`:

```python
from ai_glasses_memory.services.embedding import (
    HashEmbeddingProvider,
    create_embedding_provider,
)


def test_hash_embedding_is_deterministic_and_normalized():
    provider = HashEmbeddingProvider(dimensions=32)

    first = provider.embed_text("黑色无线鼠标")
    second = provider.embed_text("黑色无线鼠标")

    assert first == second
    assert len(first) == 32
    assert abs(sum(value * value for value in first) - 1.0) < 1e-6


def test_hash_embedding_distinguishes_different_text():
    provider = HashEmbeddingProvider(dimensions=32)

    mouse = provider.embed_text("黑色无线鼠标")
    bottle = provider.embed_text("透明水杯")

    assert mouse != bottle


def test_create_embedding_provider_defaults_to_hash():
    provider = create_embedding_provider("hash", dimensions=16)

    assert isinstance(provider, HashEmbeddingProvider)
    assert len(provider.embed_text("测试")) == 16
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_embedding.py -q
```

Expected: fail because `ai_glasses_memory.services.embedding` does not exist.

- [ ] **Step 3: Implement `embedding.py`**

Create `src/ai_glasses_memory/services/embedding.py`:

```python
from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]:
        ...


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = self._tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = re.sub(r"\s+", "", text.lower())
        chars = [char for char in normalized if "\u4e00" <= char <= "\u9fff"]
        bigrams = [
            normalized[index : index + 2]
            for index in range(max(0, len(normalized) - 1))
            if all("\u4e00" <= char <= "\u9fff" for char in normalized[index : index + 2])
        ]
        words = re.findall(r"[a-zA-Z0-9_+-]{2,}", text.lower())
        return chars + bigrams + words


class SentenceTransformersEmbeddingProvider:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install the embedding optional dependency first."
            ) from exc

        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return [float(value) for value in vector.tolist()]


def create_embedding_provider(
    provider: str,
    *,
    model_name: str = "BAAI/bge-small-zh-v1.5",
    dimensions: int = 384,
) -> EmbeddingProvider:
    normalized = provider.strip().lower()
    if normalized in {"", "hash", "local"}:
        return HashEmbeddingProvider(dimensions=dimensions)
    if normalized in {"sentence_transformers", "sentence-transformers"}:
        return SentenceTransformersEmbeddingProvider(model_name)
    raise ValueError(f"Unsupported embedding provider: {provider}")
```

- [ ] **Step 4: Add optional dependency**

Modify `pyproject.toml`:

```toml
[project.optional-dependencies]
embedding = [
    "sentence-transformers>=3.0.0",
]
```

Keep existing `dev` and `ocr` optional dependencies.

- [ ] **Step 5: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_embedding.py -q
```

Expected: 3 tests pass.

## Task 2: SQLite Vector Index

**Files:**
- Create: `src/ai_glasses_memory/services/vector_index.py`
- Test: `tests/test_vector_index.py`

- [ ] **Step 1: Write failing vector index tests**

Create `tests/test_vector_index.py`:

```python
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


def test_vector_index_upserts_searches_and_deletes(tmp_path):
    index = SQLiteVectorIndex(tmp_path / "vectors.sqlite3")

    index.upsert(memory_id=1, vector=[1.0, 0.0], text="mouse")
    index.upsert(memory_id=2, vector=[0.0, 1.0], text="cup")

    results = index.search([1.0, 0.0], limit=2)

    assert [result.memory_id for result in results] == [1, 2]
    assert results[0].score > results[1].score

    assert index.delete(1) == 1
    assert [result.memory_id for result in index.search([1.0, 0.0], limit=2)] == [2]


def test_vector_index_clear_removes_all_vectors(tmp_path):
    index = SQLiteVectorIndex(tmp_path / "vectors.sqlite3")
    index.upsert(memory_id=1, vector=[1.0, 0.0], text="mouse")
    index.upsert(memory_id=2, vector=[0.0, 1.0], text="cup")

    assert index.clear() == 2
    assert index.search([1.0, 0.0], limit=2) == []
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_vector_index.py -q
```

Expected: fail because `vector_index.py` does not exist.

- [ ] **Step 3: Implement vector index**

Create `src/ai_glasses_memory/services/vector_index.py`:

```python
from __future__ import annotations

import json
import math
import sqlite3
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
        with self._connect() as conn:
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

        with self._connect() as conn:
            rows = conn.execute("SELECT memory_id, vector_json FROM memory_vectors").fetchall()

        scored = []
        for row in rows:
            vector = [float(value) for value in json.loads(row["vector_json"])]
            score = self._cosine_similarity(query_vector, vector)
            if score > 0:
                scored.append(VectorSearchResult(memory_id=int(row["memory_id"]), score=score))

        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:limit]

    def delete(self, memory_id: int) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memory_vectors WHERE memory_id = ?", (memory_id,))
            return int(cursor.rowcount)

    def clear(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memory_vectors")
            return int(cursor.rowcount)

    def _init_db(self) -> None:
        with self._connect() as conn:
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
```

- [ ] **Step 4: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_vector_index.py -q
```

Expected: 2 tests pass.

## Task 3: Vector Search Provider

**Files:**
- Modify: `src/ai_glasses_memory/services/search.py`
- Test: `tests/test_search_provider.py`

- [ ] **Step 1: Write failing vector search provider tests**

Append to `tests/test_search_provider.py`:

```python
from ai_glasses_memory.services.embedding import HashEmbeddingProvider
from ai_glasses_memory.services.search import VectorSearchProvider
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


def test_vector_search_provider_finds_semantic_memory(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    mouse_event = store.add_event(
        MemoryEventCreate(
            question="我刚才看到了什么？",
            answer="你刚才看到了一只黑色无线鼠标。",
            scene_summary="黑色无线鼠标放在桌面上。",
            ocr_text="",
        )
    )
    store.add_event(
        MemoryEventCreate(
            question="桌上有什么饮品？",
            answer="桌上有一个透明水杯。",
            scene_summary="透明水杯在桌面右侧。",
            ocr_text="",
        )
    )
    provider = VectorSearchProvider(
        store=store,
        vector_index=SQLiteVectorIndex(tmp_path / "vectors.sqlite3"),
        embedding_provider=HashEmbeddingProvider(dimensions=64),
    )

    provider.rebuild_index()
    results = provider.search("无线鼠标", limit=1)

    assert [event.id for event in results] == [mouse_event.id]


def test_vector_search_provider_rebuilds_from_sqlite_after_clear_index(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    event = store.add_event(
        MemoryEventCreate(
            question="屏幕上是什么？",
            answer="屏幕上显示 AI 眼镜项目计划。",
            scene_summary="电脑屏幕显示项目计划。",
            ocr_text="AI 眼镜项目计划",
        )
    )
    vector_index = SQLiteVectorIndex(tmp_path / "vectors.sqlite3")
    provider = VectorSearchProvider(
        store=store,
        vector_index=vector_index,
        embedding_provider=HashEmbeddingProvider(dimensions=64),
    )

    vector_index.clear()
    provider.rebuild_index()

    assert [item.id for item in provider.search("项目计划", limit=1)] == [event.id]
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_search_provider.py -q
```

Expected: fail because `VectorSearchProvider` does not exist.

- [ ] **Step 3: Implement `VectorSearchProvider`**

Add to `src/ai_glasses_memory/services/search.py`:

```python
from ai_glasses_memory.services.embedding import EmbeddingProvider
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex
```

Then add:

```python
class VectorSearchProvider:
    def __init__(
        self,
        store: MemoryStore,
        vector_index: SQLiteVectorIndex,
        embedding_provider: EmbeddingProvider,
        fallback_provider: SearchProvider | None = None,
    ) -> None:
        self.store = store
        self.vector_index = vector_index
        self.embedding_provider = embedding_provider
        self.fallback_provider = fallback_provider or LightweightSemanticSearchProvider(store)

    def search(self, query: str, limit: int = 20) -> list[MemoryEvent]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        results = self.vector_index.search(
            self.embedding_provider.embed_text(normalized_query),
            limit=limit,
        )
        if not results:
            return self.fallback_provider.search(query=query, limit=limit)

        events_by_id = {event.id: event for event in self.store.list_events(limit=10000)}
        events = [
            events_by_id[result.memory_id]
            for result in results
            if result.memory_id in events_by_id
        ]
        if events:
            return events
        return self.fallback_provider.search(query=query, limit=limit)

    def index_event(self, event: MemoryEvent) -> None:
        text = self._embedding_text(event)
        self.vector_index.upsert(
            memory_id=event.id,
            vector=self.embedding_provider.embed_text(text),
            text=text,
        )

    def rebuild_index(self) -> None:
        self.vector_index.clear()
        for event in reversed(self.store.list_events(limit=10000)):
            self.index_event(event)

    @staticmethod
    def _embedding_text(event: MemoryEvent) -> str:
        return "\n".join(
            [
                f"question: {event.question}",
                f"answer: {event.answer}",
                f"summary: {event.scene_summary}",
                f"ocr: {event.ocr_text}",
            ]
        )
```

- [ ] **Step 4: Run provider tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_search_provider.py tests\test_vector_index.py tests\test_embedding.py -q
```

Expected: all pass.

## Task 4: Configuration and Pipeline Integration

**Files:**
- Modify: `src/ai_glasses_memory/config.py`
- Modify: `src/ai_glasses_memory/services/pipeline.py`
- Modify: `src/ai_glasses_memory/api/routes.py`
- Modify: `src/ai_glasses_memory/ui/streamlit_app.py`
- Test: `tests/test_config.py`, `tests/test_pipeline.py`

- [ ] **Step 1: Write failing config tests**

Append to `tests/test_config.py`:

```python
def test_settings_include_search_and_embedding_options(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_GLASSES_SEARCH_PROVIDER=vector",
                "AI_GLASSES_VECTOR_DB_PATH=data/test_vectors.sqlite3",
                "AI_GLASSES_EMBEDDING_PROVIDER=hash",
                "AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5",
                "AI_GLASSES_EMBEDDING_DIMENSIONS=64",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings(env_file)

    assert settings.search_provider == "vector"
    assert str(settings.vector_db_path) == "data/test_vectors.sqlite3"
    assert settings.embedding_provider == "hash"
    assert settings.embedding_model == "BAAI/bge-small-zh-v1.5"
    assert settings.embedding_dimensions == 64
```

- [ ] **Step 2: Write failing pipeline sync test**

Append to `tests/test_pipeline.py`:

```python
from ai_glasses_memory.services.embedding import HashEmbeddingProvider
from ai_glasses_memory.services.search import VectorSearchProvider
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


def test_pipeline_indexes_new_memory_for_vector_search(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    vector_search = VectorSearchProvider(
        store=store,
        vector_index=SQLiteVectorIndex(tmp_path / "vectors.sqlite3"),
        embedding_provider=HashEmbeddingProvider(dimensions=64),
    )
    pipeline = MemoryPipeline(store, search_provider=vector_search)

    event = pipeline.ask(question="我刚才看到鼠标了吗？", image_path=None)

    assert [item.id for item in pipeline.search_memories("鼠标", limit=1)] == [event.id]


def test_pipeline_rebuilds_vector_index_after_memory_cleanup(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    vector_search = VectorSearchProvider(
        store=store,
        vector_index=SQLiteVectorIndex(tmp_path / "vectors.sqlite3"),
        embedding_provider=HashEmbeddingProvider(dimensions=64),
    )
    pipeline = MemoryPipeline(store, search_provider=vector_search)

    first = store.add_event(MemoryEventCreate(question="鼠标在哪里", answer="桌上有鼠标", scene_summary="鼠标在桌面"))
    second = store.add_event(MemoryEventCreate(question="水杯在哪里", answer="桌上有水杯", scene_summary="水杯在桌面"))
    vector_search.rebuild_index()

    assert pipeline.delete_memory(first.id) == 1

    assert [item.id for item in pipeline.search_memories("水杯", limit=1)] == [second.id]
    assert pipeline.search_memories("鼠标", limit=1) == []
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py tests\test_pipeline.py -q
```

Expected: fail because config fields and pipeline vector synchronization are missing.

- [ ] **Step 4: Add settings**

Modify `src/ai_glasses_memory/config.py`:

```python
@dataclass(frozen=True)
class Settings:
    ...
    search_provider: str = "lightweight"
    vector_db_path: Path = Path("data/vector_memory.sqlite3")
    embedding_provider: str = "hash"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimensions: int = 384
```

Add in `get_settings()`:

```python
search_provider=os.getenv("AI_GLASSES_SEARCH_PROVIDER", "lightweight"),
vector_db_path=Path(os.getenv("AI_GLASSES_VECTOR_DB_PATH", "data/vector_memory.sqlite3")),
embedding_provider=os.getenv("AI_GLASSES_EMBEDDING_PROVIDER", "hash"),
embedding_model=os.getenv("AI_GLASSES_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
embedding_dimensions=int(os.getenv("AI_GLASSES_EMBEDDING_DIMENSIONS", "384")),
```

- [ ] **Step 5: Add search provider factory**

Modify `src/ai_glasses_memory/services/search.py`:

```python
from pathlib import Path
from ai_glasses_memory.services.embedding import create_embedding_provider
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


def create_search_provider(
    provider: str,
    *,
    store: MemoryStore,
    vector_db_path: str | Path,
    embedding_provider: str,
    embedding_model: str,
    embedding_dimensions: int,
) -> SearchProvider:
    normalized = provider.strip().lower()
    if normalized in {"", "lightweight", "mock"}:
        return LightweightSemanticSearchProvider(store)
    if normalized == "vector":
        vector_provider = VectorSearchProvider(
            store=store,
            vector_index=SQLiteVectorIndex(vector_db_path),
            embedding_provider=create_embedding_provider(
                embedding_provider,
                model_name=embedding_model,
                dimensions=embedding_dimensions,
            ),
        )
        vector_provider.rebuild_index()
        return vector_provider
    raise ValueError(f"Unsupported search provider: {provider}")
```

- [ ] **Step 6: Wire API and UI factories**

Modify `src/ai_glasses_memory/api/routes.py` and `src/ai_glasses_memory/ui/streamlit_app.py`:

```python
from ai_glasses_memory.services.search import create_search_provider
```

In each `get_pipeline()`:

```python
store = MemoryStore(settings.db_path)
return MemoryPipeline(
    store,
    ocr_provider=...,
    vlm_provider=...,
    search_provider=create_search_provider(
        settings.search_provider,
        store=store,
        vector_db_path=settings.vector_db_path,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dimensions=settings.embedding_dimensions,
    ),
)
```

- [ ] **Step 7: Sync vector index from pipeline**

Modify `src/ai_glasses_memory/services/pipeline.py`:

```python
    def ask(self, question: str, image_path: str | None = None) -> MemoryEvent:
        ...
        event = self.store.add_event(...)
        self._sync_search_index()
        return event

    def delete_memory(self, memory_id: int) -> int:
        deleted = self.store.delete_event(memory_id)
        if deleted:
            self._sync_search_index()
        return deleted

    def clear_memories(self) -> int:
        deleted = self.store.clear_events()
        self._sync_search_index()
        return deleted

    def prune_memories(self, keep_latest: int) -> int:
        deleted = self.store.prune_events(keep_latest=keep_latest)
        if deleted:
            self._sync_search_index()
        return deleted

    def dedupe_memories(self) -> int:
        deleted = self.store.dedupe_events()
        if deleted:
            self._sync_search_index()
        return deleted

    def _sync_search_index(self) -> None:
        rebuild = getattr(self.search_provider, "rebuild_index", None)
        if callable(rebuild):
            rebuild()
```

- [ ] **Step 8: Run config and pipeline tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py tests\test_pipeline.py -q
```

Expected: pass.

## Task 5: Docs, Env, Verification, Commit

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/phase3-search.md`
- Create: `docs/vector-search.md`
- Create: `docs/debug-log/bug-13-vector-search-upgrade.md`

- [ ] **Step 1: Update `.env.example`**

Add:

```text
AI_GLASSES_SEARCH_PROVIDER=lightweight
AI_GLASSES_VECTOR_DB_PATH=data/vector_memory.sqlite3
AI_GLASSES_EMBEDDING_PROVIDER=hash
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
AI_GLASSES_EMBEDDING_DIMENSIONS=384
```

- [ ] **Step 2: Add vector search docs**

Create `docs/vector-search.md` with:

```markdown
# 向量语义检索

当前系统支持两种检索 provider：

- `lightweight`：低依赖规则检索，适合云端 demo 和 fallback。
- `vector`：本地向量检索，适合更好的语义召回。

本地启动向量检索：

```powershell
$env:AI_GLASSES_SEARCH_PROVIDER="vector"
$env:AI_GLASSES_EMBEDDING_PROVIDER="hash"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

第一版默认使用 hash embedding，优点是无依赖、无成本、可测试。后续可切换到 `sentence_transformers` 和 `BAAI/bge-small-zh-v1.5`。
```

- [ ] **Step 3: Add debug log**

Create `docs/debug-log/bug-13-vector-search-upgrade.md` explaining why lightweight search was not enough and why the first vector implementation is local-first with a fallback provider.

- [ ] **Step 4: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Expected:

```text
All tests pass
No broken requirements found.
```

- [ ] **Step 5: Commit and push**

Run:

```powershell
git status --short
git add .
git commit -m "新增: 本地向量语义检索 provider"
git push origin main
```

Expected: push succeeds to `https://github.com/bashirmusamagaji19-debug/Arglasses`.

## Self-Review

- Spec coverage: The plan adds local-first vector search, preserves lightweight fallback, adds provider boundaries, handles SQLite/vector rebuild via pipeline, and documents costs/deployment tradeoffs.
- Placeholder scan: No TBD/TODO placeholders are used.
- Type consistency: `EmbeddingProvider`, `SQLiteVectorIndex`, `VectorSearchProvider`, and `create_search_provider` signatures are consistent across tasks.
