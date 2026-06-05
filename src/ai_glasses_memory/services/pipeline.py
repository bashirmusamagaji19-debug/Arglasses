from __future__ import annotations

from ai_glasses_memory.models.memory import MemoryEvent, MemoryEventCreate
from ai_glasses_memory.services.latency import LatencyTracker
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.mock_ai import MockAIService
from ai_glasses_memory.services.ocr import OCRProvider
from ai_glasses_memory.services.search import LightweightSemanticSearchProvider, SearchProvider
from ai_glasses_memory.services.summary import RuleBasedSummaryProvider, SummaryProvider
from ai_glasses_memory.services.vlm import MockVLMProvider, VLMProvider


class MemoryPipeline:
    """第一周端到端视觉记忆处理流程。"""

    def __init__(
        self,
        store: MemoryStore,
        ai_service: MockAIService | None = None,
        ocr_provider: OCRProvider | None = None,
        vlm_provider: VLMProvider | None = None,
        summary_provider: SummaryProvider | None = None,
        search_provider: SearchProvider | None = None,
    ) -> None:
        self.store = store
        self.ai_service = ai_service or MockAIService()
        self.ocr_provider = ocr_provider
        self.vlm_provider = vlm_provider or MockVLMProvider()
        self.summary_provider = summary_provider or RuleBasedSummaryProvider()
        self.search_provider = search_provider or LightweightSemanticSearchProvider(store)

    def ask(self, question: str, image_path: str | None = None) -> MemoryEvent:
        tracker = LatencyTracker()

        if self.ocr_provider is None:
            ocr_text = self.ai_service.run_ocr(image_path)
        else:
            ocr_text = self.ocr_provider.extract_text(image_path)
        tracker.mark("ocr")

        answer = self.vlm_provider.answer_question(question, ocr_text, image_path)
        tracker.mark("vlm")

        scene_summary = self.summary_provider.summarize_scene(question, answer, ocr_text)
        tracker.mark("summary")

        latency_ms = tracker.finish()
        event = self.store.add_event(
            MemoryEventCreate(
                question=question,
                answer=answer,
                scene_summary=scene_summary,
                ocr_text=ocr_text,
                image_path=image_path,
                latency_ms=latency_ms,
            )
        )
        self._index_search_event(event)
        return event

    def list_memories(self, limit: int = 50) -> list[MemoryEvent]:
        return self.store.list_events(limit=limit)

    def search_memories(self, keyword: str, limit: int = 20) -> list[MemoryEvent]:
        return self.search_provider.search(query=keyword, limit=limit)

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

    def _index_search_event(self, event: MemoryEvent) -> None:
        index_event = getattr(self.search_provider, "index_event", None)
        if callable(index_event):
            index_event(event)
            return
        self._sync_search_index()
