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
