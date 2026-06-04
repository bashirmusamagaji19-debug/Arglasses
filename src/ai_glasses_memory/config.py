from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("data/memory.sqlite3")
    ocr_provider: str = "mock"


def get_settings() -> Settings:
    return Settings(
        db_path=Path(os.getenv("AI_GLASSES_DB_PATH", "data/memory.sqlite3")),
        ocr_provider=os.getenv("AI_GLASSES_OCR_PROVIDER", "mock"),
    )
