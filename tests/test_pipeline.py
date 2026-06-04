from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline


class StaticOCRProvider:
    def extract_text(self, image_path: str | None) -> str:
        return f"真实 OCR 文本：{image_path}"


class StaticVLMProvider:
    def answer_question(self, question: str, ocr_text: str, image_path: str | None) -> str:
        return f"真实 VLM 回答：{question} / {ocr_text} / {image_path}"


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
