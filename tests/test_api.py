from pathlib import Path

from fastapi.testclient import TestClient

from ai_glasses_memory.api.routes import get_pipeline
from ai_glasses_memory.main import app
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
