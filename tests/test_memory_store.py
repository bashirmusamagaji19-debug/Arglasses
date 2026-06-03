from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.memory_store import MemoryStore


def test_add_event_and_list_timeline_in_reverse_time_order(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    first = store.add_event(
        MemoryEventCreate(
            question="我刚才看到了什么？",
            answer="你看到了一张桌子。",
            scene_summary="桌面上有笔记本电脑和水杯。",
            ocr_text="会议议程",
            image_path="assets/samples/desk.jpg",
            latency_ms={"total": 12.5},
        )
    )
    second = store.add_event(
        MemoryEventCreate(
            question="桌上有没有水杯？",
            answer="有，一个水杯在电脑旁边。",
            scene_summary="桌面场景，水杯靠近电脑。",
            ocr_text="",
            image_path="assets/samples/desk.jpg",
            latency_ms={"total": 9.1},
        )
    )

    timeline = store.list_events()

    assert [event.id for event in timeline] == [second.id, first.id]
    assert timeline[0].question == "桌上有没有水杯？"
    assert timeline[0].latency_ms["total"] == 9.1


def test_search_events_matches_question_answer_summary_and_ocr(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.add_event(
        MemoryEventCreate(
            question="我把钥匙放在哪里了？",
            answer="钥匙在玄关桌面上。",
            scene_summary="玄关桌面上有钥匙和快递盒。",
            ocr_text="快递单",
            image_path=None,
            latency_ms={"total": 10.0},
        )
    )
    store.add_event(
        MemoryEventCreate(
            question="屏幕上写了什么？",
            answer="屏幕显示项目计划。",
            scene_summary="电脑屏幕展示计划表。",
            ocr_text="AI 眼镜项目第一周计划",
            image_path=None,
            latency_ms={"total": 11.0},
        )
    )

    key_results = store.search_events("钥匙")
    ocr_results = store.search_events("第一周")

    assert len(key_results) == 1
    assert key_results[0].answer == "钥匙在玄关桌面上。"
    assert len(ocr_results) == 1
    assert ocr_results[0].ocr_text == "AI 眼镜项目第一周计划"
