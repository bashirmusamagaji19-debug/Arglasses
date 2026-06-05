from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]:
        ...


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = self._tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = re.sub(r"\s+", "", text.lower())
        chars = [char for char in normalized if "\u4e00" <= char <= "\u9fff"]
        bigrams = [
            normalized[index : index + 2]
            for index in range(max(0, len(normalized) - 1))
            if all("\u4e00" <= char <= "\u9fff" for char in normalized[index : index + 2])
        ]
        words = re.findall(r"[a-zA-Z0-9_+-]{2,}", text.lower())
        return chars + bigrams + words


class SentenceTransformersEmbeddingProvider:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install the embedding optional dependency first."
            ) from exc

        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return [float(value) for value in vector.tolist()]


def create_embedding_provider(
    provider: str,
    *,
    model_name: str = "BAAI/bge-small-zh-v1.5",
    dimensions: int = 384,
) -> EmbeddingProvider:
    normalized = provider.strip().lower()
    if normalized in {"", "hash", "local"}:
        return HashEmbeddingProvider(dimensions=dimensions)
    if normalized in {"sentence_transformers", "sentence-transformers"}:
        return SentenceTransformersEmbeddingProvider(model_name)
    raise ValueError(f"Unsupported embedding provider: {provider}")
