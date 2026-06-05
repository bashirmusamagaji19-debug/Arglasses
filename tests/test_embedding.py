from ai_glasses_memory.services.embedding import HashEmbeddingProvider, create_embedding_provider


def test_hash_embedding_is_deterministic_and_normalized():
    provider = HashEmbeddingProvider(dimensions=32)

    first = provider.embed_text("黑色无线鼠标")
    second = provider.embed_text("黑色无线鼠标")

    assert first == second
    assert len(first) == 32
    assert abs(sum(value * value for value in first) - 1.0) < 1e-6


def test_hash_embedding_distinguishes_different_text():
    provider = HashEmbeddingProvider(dimensions=32)

    mouse = provider.embed_text("黑色无线鼠标")
    bottle = provider.embed_text("透明水杯")

    assert mouse != bottle


def test_create_embedding_provider_defaults_to_hash():
    provider = create_embedding_provider("hash", dimensions=16)

    assert isinstance(provider, HashEmbeddingProvider)
    assert len(provider.embed_text("测试")) == 16
