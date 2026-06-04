from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ai_glasses_memory.config import get_settings
from ai_glasses_memory.models.memory import MemoryEvent
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.ocr import create_ocr_provider
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.vlm import create_vlm_provider

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    image_path: str | None = None


def get_pipeline() -> MemoryPipeline:
    settings = get_settings()
    return MemoryPipeline(
        MemoryStore(settings.db_path),
        ocr_provider=create_ocr_provider(settings.ocr_provider),
        vlm_provider=create_vlm_provider(
            settings.vlm_provider,
            base_url=settings.vlm_base_url,
            api_key=settings.vlm_api_key,
            model=settings.vlm_model,
            max_tokens=settings.vlm_max_tokens,
            timeout_seconds=settings.vlm_timeout_seconds,
            max_image_width=settings.vlm_max_image_width,
        ),
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-glasses-memory"}


@router.post("/ask", response_model=MemoryEvent)
def ask(
    request: AskRequest,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MemoryEvent:
    return pipeline.ask(question=request.question, image_path=request.image_path)


@router.get("/memories", response_model=list[MemoryEvent])
def list_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    limit: int = 50,
) -> list[MemoryEvent]:
    return pipeline.list_memories(limit=limit)


@router.get("/memories/search", response_model=list[MemoryEvent])
def search_memories(
    q: str,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    limit: int = 20,
) -> list[MemoryEvent]:
    return pipeline.search_memories(keyword=q, limit=limit)
