from pathlib import Path

from fastapi.testclient import TestClient

from ai_glasses_memory.api.routes import get_pipeline
from ai_glasses_memory.main import app
from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline


def test_api_ask_lists_and_searches_memories(tmp_path):
    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(MemoryStore(tmp_path / "api.sqlite3"))

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    response = client.post(
        "/ask",
        json={"question": "我刚才看到了什么？", "image_path": "assets/samples/default.txt"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "我刚才看到了什么？"
    assert "模拟 VLM" in payload["answer"]

    memories_response = client.get("/memories")
    assert memories_response.status_code == 200
    assert len(memories_response.json()) == 1

    search_response = client.get("/memories/search", params={"q": "模拟"})
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1

    app.dependency_overrides.clear()


def test_api_answers_from_retrieved_memories(tmp_path):
    store = MemoryStore(tmp_path / "rag.sqlite3")
    store.add_event(
        MemoryEventCreate(
            question="照片里面有什么？",
            answer="照片里有一只黑色无线鼠标。",
            scene_summary="白色桌面上有黑色无线鼠标。",
        )
    )

    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(store)

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    response = client.post(
        "/memories/rag-answer",
        json={"question": "我刚才看到的鼠标是什么颜色？", "limit": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "鼠标主要是黑色" in payload["answer"]
    assert len(payload["context_memories"]) == 1

    app.dependency_overrides.clear()


def test_health_endpoint_reports_service_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-glasses-memory"}


def test_mobile_page_exposes_camera_capture_form():
    client = TestClient(app)

    response = client.get("/mobile")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'accept="image/*"' in response.text
    assert 'capture="environment"' in response.text
    assert 'action="/mobile/ask"' in response.text


def test_mobile_ask_accepts_image_upload_and_returns_memory(tmp_path):
    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(MemoryStore(tmp_path / "mobile.sqlite3"))

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    response = client.post(
        "/mobile/ask",
        data={"question": "手上是什么？"},
        files={"image": ("phone.jpg", b"fake image bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "手上是什么？"
    assert payload["image_path"]
    assert Path(payload["image_path"]).exists()

    app.dependency_overrides.clear()


def test_api_can_delete_clear_prune_and_dedupe_memories(tmp_path):
    store = MemoryStore(tmp_path / "manage.sqlite3")

    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(store)

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    first = store.add_event(MemoryEventCreate(question="one", answer="same", scene_summary="same"))
    store.add_event(MemoryEventCreate(question="one", answer="same", scene_summary="same"))
    store.add_event(MemoryEventCreate(question="three", answer="answer", scene_summary="summary"))

    delete_response = client.delete(f"/memories/{first.id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] == 1

    dedupe_response = client.post("/memories/dedupe")
    assert dedupe_response.status_code == 200
    assert dedupe_response.json()["deleted"] == 0

    prune_response = client.post("/memories/prune", params={"keep_latest": 1})
    assert prune_response.status_code == 200
    assert prune_response.json()["deleted"] == 1

    clear_response = client.delete("/memories")
    assert clear_response.status_code == 200
    assert clear_response.json()["deleted"] == 1

    app.dependency_overrides.clear()
