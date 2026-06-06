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


def test_live_page_exposes_browser_native_camera_and_audio_controls():
    client = TestClient(app)

    response = client.get("/live")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "navigator.mediaDevices.getUserMedia" in response.text
    assert "MediaRecorder" in response.text
    assert "captureFrame" in response.text
    assert 'fetch("/live/ask"' in response.text
    assert 'fetch("/live/transcribe"' in response.text
    assert "/live/asr/ws" in response.text
    assert "startRealtimeAsr" in response.text
    assert "实时识别" in response.text
    assert "<video" in response.text
    assert "<canvas" in response.text


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


def test_live_ask_accepts_current_frame_upload_and_returns_memory(tmp_path):
    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(MemoryStore(tmp_path / "live.sqlite3"))

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    response = client.post(
        "/live/ask",
        data={"question": "我现在看到什么？"},
        files={"image": ("frame.jpg", b"fake frame bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "我现在看到什么？"
    assert payload["image_path"]
    assert Path(payload["image_path"]).exists()

    app.dependency_overrides.clear()


def test_api_transcribes_audio_upload(tmp_path):
    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(MemoryStore(tmp_path / "asr.sqlite3"))

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    response = client.post(
        "/transcribe",
        files={"audio": ("question.wav", b"fake audio bytes", "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "我刚才看到了什么？"
    assert payload["audio_path"]
    assert Path(payload["audio_path"]).exists()
    assert payload["latency_ms"]["asr"] >= 0

    app.dependency_overrides.clear()


def test_live_transcribe_accepts_recorded_audio(tmp_path):
    def override_pipeline() -> MemoryPipeline:
        return MemoryPipeline(MemoryStore(tmp_path / "live-asr.sqlite3"))

    app.dependency_overrides[get_pipeline] = override_pipeline
    client = TestClient(app)

    response = client.post(
        "/live/transcribe",
        files={"audio": ("voice.webm", b"fake recorded audio", "audio/webm")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "我刚才看到了什么？"
    assert payload["audio_path"]
    assert Path(payload["audio_path"]).exists()

    app.dependency_overrides.clear()


def test_live_asr_websocket_reports_missing_dashscope_key(monkeypatch):
    for name in ["DASHSCOPE_API_KEY", "AI_GLASSES_DASHSCOPE_API_KEY"]:
        monkeypatch.delenv(name, raising=False)

    client = TestClient(app)

    with client.websocket_connect("/live/asr/ws") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "error"
    assert "DASHSCOPE_API_KEY" in payload["message"]


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
