from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.rag import RuleBasedRAGAnswerProvider


class StaticRAGSearchProvider:
    def __init__(self, memories):
        self.memories = memories
        self.calls = []

    def search(self, query: str, limit: int = 20):
        self.calls.append((query, limit))
        return self.memories[:limit]


class CapturingRAGAnswerProvider:
    def __init__(self) -> None:
        self.calls = []

    def answer(self, question, contexts):
        self.calls.append((question, contexts))
        return "基于历史记忆：黑色无线鼠标。"


def test_pipeline_answers_question_with_retrieved_memory_context(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    mouse_memory = store.add_event(
        MemoryEventCreate(
            question="照片里面有什么？",
            answer="照片里有一只黑色无线鼠标。",
            scene_summary="白色桌面上有黑色无线鼠标。",
            ocr_text="PaddleOCR：0",
        )
    )
    rag_provider = CapturingRAGAnswerProvider()
    search_provider = StaticRAGSearchProvider([mouse_memory])
    pipeline = MemoryPipeline(
        store,
        search_provider=search_provider,
        rag_answer_provider=rag_provider,
    )

    result = pipeline.answer_from_memory("我刚才看到的鼠标是什么颜色？", limit=3)

    assert result.answer == "基于历史记忆：黑色无线鼠标。"
    assert result.context_memories == [mouse_memory]
    assert search_provider.calls == [("我刚才看到的鼠标是什么颜色？", 3)]
    assert rag_provider.calls[0][0] == "我刚才看到的鼠标是什么颜色？"
    assert rag_provider.calls[0][1] == [mouse_memory]


def test_rule_based_rag_answer_provider_handles_empty_context():
    provider = RuleBasedRAGAnswerProvider()

    result = provider.answer("我刚才看到了什么？", [])

    assert result == "没有找到足够相关的历史记忆。"


def test_rule_based_rag_answer_provider_summarizes_top_context(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    memory = store.add_event(
        MemoryEventCreate(
            question="照片里面有什么？",
            answer="照片里有一只黑色无线鼠标。",
            scene_summary="白色桌面上有黑色无线鼠标。",
        )
    )
    provider = RuleBasedRAGAnswerProvider()

    result = provider.answer("我刚才看到的鼠标是什么颜色？", [memory])

    assert "根据历史记忆" in result
    assert "黑色无线鼠标" in result
