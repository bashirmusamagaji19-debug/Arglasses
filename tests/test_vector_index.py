from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


def test_vector_index_upserts_searches_and_deletes(tmp_path):
    index = SQLiteVectorIndex(tmp_path / "vectors.sqlite3")

    index.upsert(memory_id=1, vector=[1.0, 0.0], text="mouse")
    index.upsert(memory_id=2, vector=[0.0, 1.0], text="cup")

    results = index.search([1.0, 0.0], limit=2)

    assert [result.memory_id for result in results] == [1, 2]
    assert results[0].score > results[1].score

    assert index.delete(1) == 1
    assert [result.memory_id for result in index.search([1.0, 0.0], limit=2)] == [2]


def test_vector_index_clear_removes_all_vectors(tmp_path):
    index = SQLiteVectorIndex(tmp_path / "vectors.sqlite3")
    index.upsert(memory_id=1, vector=[1.0, 0.0], text="mouse")
    index.upsert(memory_id=2, vector=[0.0, 1.0], text="cup")

    assert index.clear() == 2
    assert index.search([1.0, 0.0], limit=2) == []


def test_vector_index_releases_sqlite_file_after_operations(tmp_path):
    db_path = tmp_path / "vectors.sqlite3"
    index = SQLiteVectorIndex(db_path)
    index.upsert(memory_id=1, vector=[1.0, 0.0], text="mouse")
    assert index.search([1.0, 0.0], limit=1)

    db_path.unlink()

    assert not db_path.exists()
