from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from ai_glasses_memory.models.memory import MemoryEvent
from ai_glasses_memory.services.embedding import EmbeddingProvider, create_embedding_provider
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.vector_index import SQLiteVectorIndex


class SearchProvider(Protocol):
    def search(self, query: str, limit: int = 20) -> list[MemoryEvent]:
        ...


class LightweightSemanticSearchProvider:
    def __init__(self, store: MemoryStore, candidate_limit: int = 100) -> None:
        self.store = store
        self.candidate_limit = candidate_limit

    def search(self, query: str, limit: int = 20) -> list[MemoryEvent]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        candidates = self.store.list_events(limit=max(self.candidate_limit, limit))
        scored = [(self._score(normalized_query, event), event) for event in candidates]
        scored = [(score, event) for score, event in scored if score > 0]
        real_scored = [
            (score, event)
            for score, event in scored
            if not self._looks_like_mock_event(event)
        ]
        if real_scored:
            scored = real_scored
        scored.sort(key=lambda item: (item[0], item[1].created_at, item[1].id), reverse=True)
        return [event for _, event in scored[:limit]]

    def _score(self, query: str, event: MemoryEvent) -> float:
        document = self._event_text(event)
        score = 0.0

        if query in document:
            score += 3.0

        keyword_hits = self._keyword_hits(query, document)
        score += keyword_hits * 0.8

        query_tokens = self._tokens(query)
        document_tokens = self._tokens(document)
        if query_tokens and document_tokens:
            overlap = query_tokens & document_tokens
            score += len(overlap) / len(query_tokens | document_tokens)
            score += len(overlap) / len(query_tokens) * 0.6

        score += self._intent_boost(query, document)
        return score

    @staticmethod
    def _event_text(event: MemoryEvent) -> str:
        return "\n".join(
            [
                event.question,
                event.answer,
                event.scene_summary,
                event.ocr_text,
            ]
        )

    @classmethod
    def _looks_like_mock_event(cls, event: MemoryEvent) -> bool:
        text = cls._event_text(event)
        mock_markers = [
            "模拟 OCR",
            "模拟 VLM",
            "模拟场景摘要",
            "mock OCR",
            "mock VLM",
            "mock scene",
        ]
        return any(marker.lower() in text.lower() for marker in mock_markers)

    @staticmethod
    def _keyword_hits(query: str, document: str) -> int:
        terms = [
            term
            for term in re.split(r"[\s,，。！？?、：；;（）()]+", query)
            if len(term) >= 2
        ]
        return sum(1 for term in terms if term in document)

    @staticmethod
    def _tokens(text: str) -> set[str]:
        normalized = re.sub(r"\s+", "", text.lower())
        stop_chars = set("我你他她它的是了在有和吗呢啊刚才之前看到什么哪里一个这个那个")
        chars = {
            char
            for char in normalized
            if "\u4e00" <= char <= "\u9fff" and char not in stop_chars
        }
        bigrams = {
            normalized[index : index + 2]
            for index in range(max(0, len(normalized) - 1))
            if all("\u4e00" <= char <= "\u9fff" for char in normalized[index : index + 2])
        }
        words = {
            word
            for word in re.findall(r"[a-zA-Z0-9_+-]+", text.lower())
            if len(word) >= 2
        }
        return chars | bigrams | words

    @staticmethod
    def _intent_boost(query: str, document: str) -> float:
        score = 0.0
        if any(term in query for term in ["拿", "拿过", "手上", "手里"]):
            if any(term in document for term in ["拿", "拿着", "手上", "手里", "手中"]):
                score += 1.2
        if any(term in query for term in ["屏幕", "电脑", "显示"]):
            if any(term in document for term in ["屏幕", "电脑", "显示"]):
                score += 1.2
        if any(term in query for term in ["文字", "写着", "写了"]):
            if any(term in document for term in ["文字", "写着", "OCR", "文本"]):
                score += 1.0
        return score


class VectorSearchProvider:
    def __init__(
        self,
        store: MemoryStore,
        vector_index: SQLiteVectorIndex,
        embedding_provider: EmbeddingProvider,
        fallback_provider: SearchProvider | None = None,
        min_score: float = 0.2,
    ) -> None:
        self.store = store
        self.vector_index = vector_index
        self.embedding_provider = embedding_provider
        self.fallback_provider = fallback_provider or LightweightSemanticSearchProvider(store)
        self.min_score = min_score
        self._index_ready = False

    def search(self, query: str, limit: int = 20) -> list[MemoryEvent]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        self._ensure_index_ready()
        results = self.vector_index.search(
            self.embedding_provider.embed_text(normalized_query),
            limit=limit,
        )
        if not results:
            return self.fallback_provider.search(query=query, limit=limit)
        results = [result for result in results if result.score >= self.min_score]
        if not results:
            return []

        events_by_id = {event.id: event for event in self.store.list_events(limit=10000)}
        events = [
            events_by_id[result.memory_id]
            for result in results
            if result.memory_id in events_by_id
        ]
        real_events = [
            event
            for event in events
            if not LightweightSemanticSearchProvider._looks_like_mock_event(event)
        ]
        if real_events:
            events = real_events
        if events:
            return events
        return self.fallback_provider.search(query=query, limit=limit)

    def index_event(self, event: MemoryEvent) -> None:
        text = self._embedding_text(event)
        self.vector_index.upsert(
            memory_id=event.id,
            vector=self.embedding_provider.embed_text(text),
            text=text,
        )

    def rebuild_index(self) -> None:
        self.vector_index.clear()
        for event in reversed(self.store.list_events(limit=10000)):
            self.index_event(event)
        self._index_ready = True

    def mark_index_stale(self) -> None:
        self._index_ready = False

    def _ensure_index_ready(self) -> None:
        if not self._index_ready:
            self.rebuild_index()

    @staticmethod
    def _embedding_text(event: MemoryEvent) -> str:
        return "\n".join(
            [
                f"question: {event.question}",
                f"answer: {event.answer}",
                f"summary: {event.scene_summary}",
                f"ocr: {event.ocr_text}",
            ]
        )


def create_search_provider(
    provider: str,
    *,
    store: MemoryStore,
    vector_db_path: str | Path,
    embedding_provider: str,
    embedding_model: str,
    embedding_dimensions: int,
) -> SearchProvider:
    normalized = provider.strip().lower()
    if normalized in {"", "lightweight", "mock"}:
        return LightweightSemanticSearchProvider(store)
    if normalized == "vector":
        vector_provider = VectorSearchProvider(
            store=store,
            vector_index=SQLiteVectorIndex(vector_db_path),
            embedding_provider=create_embedding_provider(
                embedding_provider,
                model_name=embedding_model,
                dimensions=embedding_dimensions,
            ),
        )
        return vector_provider
    raise ValueError(f"Unsupported search provider: {provider}")
