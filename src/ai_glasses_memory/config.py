from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("data/memory.sqlite3")
    ocr_provider: str = "mock"
    vlm_provider: str = "mock"
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_model: str = ""
    vlm_max_tokens: int = 512
    vlm_timeout_seconds: float = 30


def get_settings() -> Settings:
    return Settings(
        db_path=Path(os.getenv("AI_GLASSES_DB_PATH", "data/memory.sqlite3")),
        ocr_provider=os.getenv("AI_GLASSES_OCR_PROVIDER", "mock"),
        vlm_provider=os.getenv("AI_GLASSES_VLM_PROVIDER", "mock"),
        vlm_base_url=os.getenv("AI_GLASSES_VLM_BASE_URL", ""),
        vlm_api_key=os.getenv("AI_GLASSES_VLM_API_KEY", ""),
        vlm_model=os.getenv("AI_GLASSES_VLM_MODEL", ""),
        vlm_max_tokens=int(os.getenv("AI_GLASSES_VLM_MAX_TOKENS", "512")),
        vlm_timeout_seconds=float(os.getenv("AI_GLASSES_VLM_TIMEOUT_SECONDS", "30")),
    )
