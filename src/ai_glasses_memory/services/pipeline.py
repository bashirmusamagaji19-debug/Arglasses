from __future__ import annotations

from ai_glasses_memory.models.memory import MemoryEvent, MemoryEventCreate
from ai_glasses_memory.services.latency import LatencyTracker
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.mock_ai import MockAIService


class MemoryPipeline:
    """第一周端到端视觉记忆处理流程。"""

    def __init__(
        self,
        store: MemoryStore,
        ai_service: MockAIService | None = None,
    ) -> None:
        self.store = store
        self.ai_service = ai_service or MockAIService()

    def ask(self, question: str, image_path: str | None = None) -> MemoryEvent:
        tracker = LatencyTracker()

        ocr_text = self.ai_service.run_ocr(image_path)
        tracker.mark("ocr")

        answer = self.ai_service.answer_question(question, ocr_text)
        tracker.mark("vlm")

        scene_summary = self.ai_service.summarize_scene(question, answer, ocr_text)
        tracker.mark("summary")

        latency_ms = tracker.finish()
        return self.store.add_event(
            MemoryEventCreate(
                question=question,
                answer=answer,
                scene_summary=scene_summary,
                ocr_text=ocr_text,
                image_path=image_path,
                latency_ms=latency_ms,
            )
        )

    def list_memories(self, limit: int = 50) -> list[MemoryEvent]:
        return self.store.list_events(limit=limit)

    def search_memories(self, keyword: str, limit: int = 20) -> list[MemoryEvent]:
        return self.store.search_events(keyword=keyword, limit=limit)
