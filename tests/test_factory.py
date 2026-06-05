from ai_glasses_memory.services.factory import create_pipeline
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.pipeline import MemoryPipeline


def test_create_pipeline_builds_memory_pipeline_from_settings(tmp_path):
    pipeline = create_pipeline(db_path=tmp_path / "memory.sqlite3")

    assert isinstance(pipeline, MemoryPipeline)
    assert isinstance(pipeline.store, MemoryStore)
    assert pipeline.store.db_path == tmp_path / "memory.sqlite3"
