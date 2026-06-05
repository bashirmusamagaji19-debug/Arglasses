from __future__ import annotations

from pathlib import Path

from ai_glasses_memory.config import Settings, get_settings
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.ocr import create_ocr_provider
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.search import create_search_provider
from ai_glasses_memory.services.vlm import create_vlm_provider


def create_pipeline(
    settings: Settings | None = None,
    *,
    db_path: str | Path | None = None,
) -> MemoryPipeline:
    resolved_settings = settings or get_settings()
    store = MemoryStore(db_path or resolved_settings.db_path)
    return MemoryPipeline(
        store,
        ocr_provider=create_ocr_provider(resolved_settings.ocr_provider),
        vlm_provider=create_vlm_provider(
            resolved_settings.vlm_provider,
            base_url=resolved_settings.vlm_base_url,
            api_key=resolved_settings.vlm_api_key,
            model=resolved_settings.vlm_model,
            max_tokens=resolved_settings.vlm_max_tokens,
            timeout_seconds=resolved_settings.vlm_timeout_seconds,
            max_image_width=resolved_settings.vlm_max_image_width,
        ),
        search_provider=create_search_provider(
            resolved_settings.search_provider,
            store=store,
            vector_db_path=resolved_settings.vector_db_path,
            embedding_provider=resolved_settings.embedding_provider,
            embedding_model=resolved_settings.embedding_model,
            embedding_dimensions=resolved_settings.embedding_dimensions,
        ),
    )
