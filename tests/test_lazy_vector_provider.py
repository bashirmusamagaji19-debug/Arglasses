import builtins

from ai_glasses_memory.models.memory import MemoryEventCreate
from ai_glasses_memory.services.embedding import SentenceTransformersEmbeddingProvider
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.search import VectorSearchProvider, create_search_provider


def test_sentence_transformers_provider_does_not_import_model_until_embed(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise AssertionError("model package should not be imported during provider construction")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    provider = SentenceTransformersEmbeddingProvider("BAAI/bge-small-zh-v1.5")

    assert provider.model_name == "BAAI/bge-small-zh-v1.5"


def test_create_vector_search_provider_does_not_rebuild_index_immediately(tmp_path, monkeypatch):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.add_event(
        MemoryEventCreate(
            question="鼠标在哪里",
            answer="黑色无线鼠标在桌上",
            scene_summary="桌面上有鼠标",
        )
    )

    def fail_rebuild(self):
        raise AssertionError("vector index should not rebuild during provider construction")

    monkeypatch.setattr(VectorSearchProvider, "rebuild_index", fail_rebuild)

    provider = create_search_provider(
        "vector",
        store=store,
        vector_db_path=tmp_path / "vectors.sqlite3",
        embedding_provider="hash",
        embedding_model="BAAI/bge-small-zh-v1.5",
        embedding_dimensions=64,
    )

    assert isinstance(provider, VectorSearchProvider)
