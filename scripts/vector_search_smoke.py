from __future__ import annotations

import tempfile
from pathlib import Path

from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.search import create_search_provider


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        store = MemoryStore(tmp_path / "memory.sqlite3")
        search = create_search_provider(
            "vector",
            store=store,
            vector_db_path=tmp_path / "vectors.sqlite3",
            embedding_provider="sentence_transformers",
            embedding_model="BAAI/bge-small-zh-v1.5",
            embedding_dimensions=512,
        )
        pipeline = MemoryPipeline(store, search_provider=search)
        store.add_event(
            MemoryEventCreate(
                question="鼠标在哪里",
                answer="黑色无线鼠标在桌上",
                scene_summary="桌面上有鼠标",
            )
        )
        store.add_event(
            MemoryEventCreate(
                question="水杯在哪里",
                answer="透明水杯在桌上",
                scene_summary="桌面上有水杯",
            )
        )
        search.rebuild_index()

        print([event.question for event in pipeline.search_memories("无线鼠标", limit=1)])
        print([event.question for event in pipeline.search_memories("喝水的杯子", limit=1)])


if __name__ == "__main__":
    main()
