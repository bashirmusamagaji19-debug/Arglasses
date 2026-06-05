from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ai_glasses_memory.config import get_settings
from ai_glasses_memory.models.memory import MemoryEvent
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.ocr import create_ocr_provider
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.search import create_search_provider
from ai_glasses_memory.services.uploads import save_input_image
from ai_glasses_memory.services.vlm import create_vlm_provider

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    image_path: str | None = None


class MutationResult(BaseModel):
    deleted: int


def get_pipeline() -> MemoryPipeline:
    settings = get_settings()
    store = MemoryStore(settings.db_path)
    return MemoryPipeline(
        store,
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
        search_provider=create_search_provider(
            settings.search_provider,
            store=store,
            vector_db_path=settings.vector_db_path,
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
        ),
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-glasses-memory"}


@router.get("/mobile", response_class=HTMLResponse)
def mobile_page() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 眼镜手机输入</title>
  <style>
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f7f7f8;
      color: #171717;
    }
    main {
      max-width: 520px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 {
      font-size: 22px;
      margin: 8px 0 18px;
    }
    label {
      display: block;
      font-size: 14px;
      font-weight: 600;
      margin: 16px 0 8px;
    }
    input, button {
      width: 100%;
      box-sizing: border-box;
      font-size: 16px;
    }
    input[type="text"], input[type="file"] {
      border: 1px solid #d0d5dd;
      border-radius: 8px;
      background: #fff;
      padding: 12px;
    }
    button {
      margin-top: 18px;
      border: 0;
      border-radius: 8px;
      padding: 13px 16px;
      background: #2563eb;
      color: #fff;
      font-weight: 700;
    }
    .note {
      margin-top: 14px;
      font-size: 13px;
      color: #525252;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <main>
    <h1>AI 眼镜第一视角输入</h1>
    <form action="/mobile/ask" method="post" enctype="multipart/form-data">
      <label for="question">问题</label>
      <input id="question" name="question" type="text" value="我刚才看到了什么？" required>

      <label for="image">拍照 / 选择图片</label>
      <input id="image" name="image" type="file" accept="image/*" capture="environment" required>

      <button type="submit">提交到视觉记忆系统</button>
    </form>
    <p class="note">手机只负责拍照上传，OCR、VLM、记忆写入和检索都在后端运行。</p>
  </main>
</body>
</html>
"""


@router.post("/ask", response_model=MemoryEvent)
def ask(
    request: AskRequest,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MemoryEvent:
    return pipeline.ask(question=request.question, image_path=request.image_path)


@router.post("/mobile/ask", response_model=MemoryEvent)
def mobile_ask(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    question: str = Form(...),
    image: UploadFile = File(...),
) -> MemoryEvent:
    image_path = save_input_image(image)
    return pipeline.ask(question=question, image_path=image_path)


@router.get("/memories", response_model=list[MemoryEvent])
def list_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    limit: int = 50,
) -> list[MemoryEvent]:
    return pipeline.list_memories(limit=limit)


@router.delete("/memories", response_model=MutationResult)
def clear_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MutationResult:
    return MutationResult(deleted=pipeline.clear_memories())


@router.delete("/memories/{memory_id}", response_model=MutationResult)
def delete_memory(
    memory_id: int,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MutationResult:
    return MutationResult(deleted=pipeline.delete_memory(memory_id))


@router.post("/memories/prune", response_model=MutationResult)
def prune_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    keep_latest: int = 50,
) -> MutationResult:
    return MutationResult(deleted=pipeline.prune_memories(keep_latest=keep_latest))


@router.post("/memories/dedupe", response_model=MutationResult)
def dedupe_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MutationResult:
    return MutationResult(deleted=pipeline.dedupe_memories())


@router.get("/memories/search", response_model=list[MemoryEvent])
def search_memories(
    q: str,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    limit: int = 20,
) -> list[MemoryEvent]:
    return pipeline.search_memories(keyword=q, limit=limit)
