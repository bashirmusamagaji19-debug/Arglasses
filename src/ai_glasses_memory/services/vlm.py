from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Protocol

import httpx


logger = logging.getLogger(__name__)


class VLMProvider(Protocol):
    def answer_question(self, question: str, ocr_text: str, image_path: str | None) -> str:
        ...


class MockVLMProvider:
    def answer_question(self, question: str, ocr_text: str, image_path: str | None) -> str:
        return (
            f"模拟 VLM 回答：针对问题“{question}”，系统根据当前画面和 OCR 文本判断，"
            f"相关线索是：{ocr_text}"
        )


class OpenAICompatibleVLMProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        fallback: VLMProvider | None = None,
        http_client=None,
        max_tokens: int = 512,
        timeout_seconds: float = 30,
        max_image_width: int = 1024,
        image_detail: str = "low",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.fallback = fallback or MockVLMProvider()
        self.http_client = http_client or httpx.Client()
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_image_width = max_image_width
        self.image_detail = image_detail

    def answer_question(self, question: str, ocr_text: str, image_path: str | None) -> str:
        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=self._build_payload(question, ocr_text, image_path),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning(
                "VLM provider fell back to mock: provider=openai_compatible model=%s base_url=%s error=%s",
                self.model,
                self.base_url,
                exc,
            )
            return self.fallback.answer_question(question, ocr_text, image_path)

        if not content:
            return self.fallback.answer_question(question, ocr_text, image_path)
        return str(content)

    def _build_payload(self, question: str, ocr_text: str, image_path: str | None) -> dict:
        user_content: list[dict] = [
            {
                "type": "text",
                "text": (
                    "你是一个面向 AI 眼镜的视觉记忆助手。"
                    "请结合图片内容、OCR 文本和用户问题，用中文给出简洁、具体的回答。\n\n"
                    f"用户问题：{question}\n"
                    f"OCR 文本：{ocr_text}"
                ),
            }
        ]

        image_data_url = self._image_to_data_url(image_path)
        if image_data_url:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url, "detail": self.image_detail},
                }
            )

        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个视觉记忆系统中的多模态问答模块，回答必须使用中文。",
                },
                {"role": "user", "content": user_content},
            ],
            "max_tokens": self.max_tokens,
        }

    def _image_to_data_url(self, image_path: str | None) -> str | None:
        if not image_path:
            return None

        path = Path(image_path)
        if not path.exists() or not path.is_file():
            return None

        try:
            image_bytes = self._compressed_image_bytes(path)
            mime_type = "image/jpeg"
        except Exception as exc:
            logger.warning("VLM image compression failed, using original image: path=%s error=%s", path, exc)
            image_bytes = path.read_bytes()
            mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"

        logger.info(
            "VLM image payload prepared: path=%s bytes=%s max_image_width=%s detail=%s",
            path,
            len(image_bytes),
            self.max_image_width,
            self.image_detail,
        )
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _compressed_image_bytes(self, path: Path) -> bytes:
        from io import BytesIO

        from PIL import Image

        with Image.open(path) as image:
            image = image.convert("RGB")
            if image.width > self.max_image_width:
                ratio = self.max_image_width / image.width
                image = image.resize((self.max_image_width, max(1, int(image.height * ratio))))
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85, optimize=True)
            return buffer.getvalue()


def create_vlm_provider(
    provider_name: str | None,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 512,
    timeout_seconds: float = 30,
    max_image_width: int = 1024,
) -> VLMProvider:
    normalized = (provider_name or "mock").strip().lower()
    if normalized in {"openai_compatible", "openai-compatible"}:
        if base_url and api_key and model:
            return OpenAICompatibleVLMProvider(
                base_url=base_url,
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
                max_image_width=max_image_width,
            )
    return MockVLMProvider()
