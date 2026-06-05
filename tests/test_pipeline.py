from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.embedding import HashEmbeddingProvider
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.search import VectorSearchProvider
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


class StaticOCRProvider:
    def extract_text(self, image_path: str | None) -> str:
        return f"真实 OCR 文本：{image_path}"


class StaticVLMProvider:
    def answer_question(self, question: str, ocr_text: str, image_path: str | None) -> str:
        return f"真实 VLM 回答：{question} / {ocr_text} / {image_path}"


class StaticSummaryProvider:
    def summarize_scene(self, question: str, answer: str, ocr_text: str) -> str:
        return f"真实摘要：{question} / {answer} / {ocr_text}"


class StaticSearchProvider:
    def search(self, query: str, limit: int = 20):
        return [f"search:{query}:{limit}"]


class IncrementalSearchProvider:
    def __init__(self) -> None:
        self.indexed_ids: list[int] = []

    def search(self, query: str, limit: int = 20):
        return []

    def index_event(self, event):
        self.indexed_ids.append(event.id)

    def rebuild_index(self):
        raise AssertionError("new memories should be indexed incrementally")


def test_pipeline_generates_answer_and_persists_memory_event(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store)

    result = pipeline.ask(
        question="我刚才看到了什么？",
        image_path="assets/samples/default.txt",
    )

    timeline = store.list_events()

    assert result.question == "我刚才看到了什么？"
    assert "模拟" in result.answer
    assert result.scene_summary
    assert result.ocr_text
    assert result.latency_ms["total"] >= 0
    assert len(timeline) == 1
    assert timeline[0].answer == result.answer


def test_pipeline_can_search_existing_memory(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store)
    pipeline.ask(question="桌上有没有水杯？", image_path=None)

    results = pipeline.search_memories("水杯")

    assert len(results) == 1
    assert results[0].question == "桌上有没有水杯？"


def test_pipeline_uses_injected_ocr_provider(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store, ocr_provider=StaticOCRProvider())

    result = pipeline.ask(question="屏幕上有什么？", image_path="screen.jpg")

    assert result.ocr_text == "真实 OCR 文本：screen.jpg"
    assert "真实 OCR 文本：screen.jpg" in result.answer


def test_pipeline_uses_injected_vlm_provider(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(
        store,
        ocr_provider=StaticOCRProvider(),
        vlm_provider=StaticVLMProvider(),
    )

    result = pipeline.ask(question="屏幕上有什么？", image_path="screen.jpg")

    assert result.answer == "真实 VLM 回答：屏幕上有什么？ / 真实 OCR 文本：screen.jpg / screen.jpg"


def test_pipeline_uses_injected_summary_provider(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(
        store,
        ocr_provider=StaticOCRProvider(),
        vlm_provider=StaticVLMProvider(),
        summary_provider=StaticSummaryProvider(),
    )

    result = pipeline.ask(question="屏幕上有什么？", image_path="screen.jpg")

    assert result.scene_summary.startswith("真实摘要：屏幕上有什么？")
    assert "模拟场景摘要" not in result.scene_summary


def test_pipeline_uses_injected_search_provider(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store, search_provider=StaticSearchProvider())

    results = pipeline.search_memories("刚才拿过什么", limit=3)

    assert results == ["search:刚才拿过什么:3"]


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


def test_pipeline_indexes_new_memory_incrementally_when_supported(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    search_provider = IncrementalSearchProvider()
    pipeline = MemoryPipeline(store, search_provider=search_provider)

    event = pipeline.ask(question="鼠标在哪里？", image_path=None)

    assert search_provider.indexed_ids == [event.id]


def test_pipeline_rebuilds_vector_index_after_memory_cleanup(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    vector_search = VectorSearchProvider(
        store=store,
        vector_index=SQLiteVectorIndex(tmp_path / "vectors.sqlite3"),
        embedding_provider=HashEmbeddingProvider(dimensions=64),
    )
    pipeline = MemoryPipeline(store, search_provider=vector_search)

    first = store.add_event(
        MemoryEventCreate(question="鼠标在哪里", answer="桌上有鼠标", scene_summary="鼠标在桌面")
    )
    second = store.add_event(
        MemoryEventCreate(question="水杯在哪里", answer="桌上有水杯", scene_summary="水杯在桌面")
    )
    vector_search.rebuild_index()

    assert pipeline.delete_memory(first.id) == 1

    assert [result.memory_id for result in vector_search.vector_index.search(
        vector_search.embedding_provider.embed_text("鼠标"),
        limit=2,
    )] == [second.id]
    assert [item.id for item in pipeline.search_memories("水杯", limit=1)] == [second.id]
    assert first.id not in [item.id for item in pipeline.search_memories("鼠标", limit=5)]
