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
    vlm_max_image_width: int = 1024
    search_provider: str = "lightweight"
    vector_db_path: Path = Path("data/vector_memory.sqlite3")
    chroma_path: Path = Path("data/chroma")
    chroma_collection: str = "visual_memory"
    embedding_provider: str = "hash"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimensions: int = 384


def load_dotenv(env_file: Path | str | None = Path(".env")) -> None:
    if env_file is None:
        return

    path = Path(env_file)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_settings(env_file: Path | str | None = Path(".env")) -> Settings:
    load_dotenv(env_file)
    return Settings(
        db_path=Path(os.getenv("AI_GLASSES_DB_PATH", "data/memory.sqlite3")),
        ocr_provider=os.getenv("AI_GLASSES_OCR_PROVIDER", "mock"),
        vlm_provider=os.getenv("AI_GLASSES_VLM_PROVIDER", "mock"),
        vlm_base_url=os.getenv("AI_GLASSES_VLM_BASE_URL", ""),
        vlm_api_key=os.getenv("AI_GLASSES_VLM_API_KEY", ""),
        vlm_model=os.getenv("AI_GLASSES_VLM_MODEL", ""),
        vlm_max_tokens=int(os.getenv("AI_GLASSES_VLM_MAX_TOKENS", "512")),
        vlm_timeout_seconds=float(os.getenv("AI_GLASSES_VLM_TIMEOUT_SECONDS", "30")),
        vlm_max_image_width=int(os.getenv("AI_GLASSES_VLM_MAX_IMAGE_WIDTH", "1024")),
        search_provider=os.getenv("AI_GLASSES_SEARCH_PROVIDER", "lightweight"),
        vector_db_path=Path(os.getenv("AI_GLASSES_VECTOR_DB_PATH", "data/vector_memory.sqlite3")),
        chroma_path=Path(os.getenv("AI_GLASSES_CHROMA_PATH", "data/chroma")),
        chroma_collection=os.getenv("AI_GLASSES_CHROMA_COLLECTION", "visual_memory"),
        embedding_provider=os.getenv("AI_GLASSES_EMBEDDING_PROVIDER", "hash"),
        embedding_model=os.getenv("AI_GLASSES_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
        embedding_dimensions=int(os.getenv("AI_GLASSES_EMBEDDING_DIMENSIONS", "384")),
    )
