from ai_glasses_memory.config import Settings
from ai_glasses_memory.services.asr import FasterWhisperASRProvider, QwenRealtimeASRProvider
from ai_glasses_memory.services.factory import create_pipeline
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline


def test_create_pipeline_builds_memory_pipeline_from_settings(tmp_path, monkeypatch):
    for name in [
        "AI_GLASSES_ASR_MODEL",
        "AI_GLASSES_ASR_DEVICE",
        "AI_GLASSES_ASR_COMPUTE_TYPE",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AI_GLASSES_ASR_PROVIDER", "faster_whisper")

    pipeline = create_pipeline(db_path=tmp_path / "memory.sqlite3")

    assert isinstance(pipeline, MemoryPipeline)
    assert isinstance(pipeline.store, MemoryStore)
    assert pipeline.store.db_path == tmp_path / "memory.sqlite3"
    assert isinstance(pipeline.asr_provider, FasterWhisperASRProvider)


def test_create_pipeline_accepts_qwen_realtime_asr_provider(tmp_path):
    pipeline = create_pipeline(
        settings=Settings(asr_provider="qwen_realtime"),
        db_path=tmp_path / "memory.sqlite3",
    )

    assert isinstance(pipeline.asr_provider, QwenRealtimeASRProvider)
