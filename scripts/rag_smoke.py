from __future__ import annotations

import tempfile
from pathlib import Path

from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.embedding import SentenceTransformersEmbeddingProvider
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.search import ChromaSearchProvider


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        store = MemoryStore(tmp_path / "memory.sqlite3")
        search = ChromaSearchProvider(
            store=store,
            chroma_path=tmp_path / "chroma",
            collection_name="visual_memory_smoke",
            embedding_provider=SentenceTransformersEmbeddingProvider("BAAI/bge-small-zh-v1.5"),
            min_score=0.0,
        )
        pipeline = MemoryPipeline(store, search_provider=search)

        memories = [
            MemoryEventCreate(
                question="我刚才看到了什么？",
                answer="你刚才看到的是一只黑色的无线鼠标，放在白色桌面上。",
                scene_summary="白色桌面上有黑色无线鼠标。",
            ),
            MemoryEventCreate(
                question="照片里面有什么？",
                answer="前景是一只黑色人体工学鼠标，后方稍远处是一只银灰色扁平鼠标。",
                scene_summary="桌面上有黑色鼠标和银灰色鼠标。",
            ),
            MemoryEventCreate(
                question="桌上有什么饮品？",
                answer="桌上有一个透明水杯。",
                scene_summary="白色桌面上有水杯。",
            ),
        ]

        for memory in memories:
            event = store.add_event(memory)
            search.index_event(event)

        question = "鼠标是什么颜色的？"
        result = pipeline.answer_from_memory(question, limit=3)

        print(f"question: {question}")
        print(f"answer: {result.answer}")
        print(f"contexts: {len(result.context_memories)}")
        for memory in result.context_memories:
            print(f"- {memory.id}: {memory.question} -> {memory.answer}")


if __name__ == "__main__":
    main()
