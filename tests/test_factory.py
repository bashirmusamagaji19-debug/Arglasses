from ai_glasses_memory.services.asr import FasterWhisperASRProvider
from ai_glasses_memory.services.factory import create_pipeline
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline


def test_create_pipeline_builds_memory_pipeline_from_settings(tmp_path, monkeypatch):
    for name in [
        "AI_GLASSES_ASR_PROVIDER",
        "AI_GLASSES_ASR_MODEL",
        "AI_GLASSES_ASR_DEVICE",
        "AI_GLASSES_ASR_COMPUTE_TYPE",
    ]:
        monkeypatch.delenv(name, raising=False)

    pipeline = create_pipeline(db_path=tmp_path / "memory.sqlite3")

    assert isinstance(pipeline, MemoryPipeline)
    assert isinstance(pipeline.store, MemoryStore)
    assert pipeline.store.db_path == tmp_path / "memory.sqlite3"
    assert isinstance(pipeline.asr_provider, FasterWhisperASRProvider)
