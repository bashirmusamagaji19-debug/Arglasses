from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MemoryEventCreate(BaseModel):
    """创建一条视觉记忆事件所需的数据。"""

    question: str
    answer: str
    scene_summary: str
    ocr_text: str = ""
    image_path: Optional[str] = None
    latency_ms: dict[str, float] = Field(default_factory=dict)


class MemoryEvent(MemoryEventCreate):
    """已经持久化的视觉记忆事件。"""

    id: int
    created_at: datetime
