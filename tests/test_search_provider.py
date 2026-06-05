from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.search import LightweightSemanticSearchProvider


def test_lightweight_semantic_search_recalls_related_memory_without_exact_keyword(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    mouse_event = store.add_event(
        MemoryEventCreate(
            question="手上是什么？",
            answer="手上拿的是一个黑色无线鼠标。",
            scene_summary="用户手里拿着黑色无线鼠标，并询问手上是什么。",
            ocr_text="",
            image_path=None,
            latency_ms={"total": 1.0},
        )
    )
    store.add_event(
        MemoryEventCreate(
            question="屏幕上是什么？",
            answer="屏幕上显示项目计划和代码。",
            scene_summary="电脑屏幕显示项目计划。",
            ocr_text="AI glasses memory",
            image_path=None,
            latency_ms={"total": 1.0},
        )
    )

    provider = LightweightSemanticSearchProvider(store)
    results = provider.search("我刚才拿过什么？")

    assert results
    assert results[0].id == mouse_event.id


def test_lightweight_semantic_search_still_prioritizes_exact_keyword(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.add_event(
        MemoryEventCreate(
            question="手上是什么？",
            answer="手上拿的是一个黑色无线鼠标。",
            scene_summary="用户手里拿着黑色无线鼠标。",
        )
    )
    screen_event = store.add_event(
        MemoryEventCreate(
            question="屏幕上是什么？",
            answer="屏幕上显示项目计划和代码。",
            scene_summary="电脑屏幕显示项目计划。",
            ocr_text="AI glasses memory",
        )
    )

    provider = LightweightSemanticSearchProvider(store)
    results = provider.search("项目计划")

    assert results[0].id == screen_event.id


def test_lightweight_semantic_search_returns_empty_for_blank_query(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    provider = LightweightSemanticSearchProvider(store)

    assert provider.search("   ") == []


def test_lightweight_semantic_search_filters_mock_memory_when_real_hits_exist(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    real_event = store.add_event(
        MemoryEventCreate(
            question="我刚才看到了什么？",
            answer="你刚才看到的是一只黑色的无线鼠标，放在白色桌面上。",
            scene_summary="用户提问：我刚才看到了什么？。视觉回答：黑色无线鼠标。",
            ocr_text="PaddleOCR：0",
        )
    )
    store.add_event(
        MemoryEventCreate(
            question="手上是什么",
            answer="模拟 VLM 回答：手上可能拿着鼠标。",
            scene_summary="模拟场景摘要：本次交互模拟了 AI 眼镜看到当前场景。",
            ocr_text="模拟 OCR：画面中可能包含电脑屏幕、课程笔记、水杯。",
        )
    )

    provider = LightweightSemanticSearchProvider(store)
    results = provider.search("鼠标")

    assert [event.id for event in results] == [real_event.id]
