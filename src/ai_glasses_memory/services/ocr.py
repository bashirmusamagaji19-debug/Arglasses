from __future__ import annotations

from typing import Callable, Protocol


class OCRProvider(Protocol):
    def extract_text(self, image_path: str | None) -> str:
        ...


class MockOCRProvider:
    def extract_text(self, image_path: str | None) -> str:
        return "模拟 OCR：画面中可能包含电脑屏幕、课程笔记、水杯和一张写着 AI 眼镜项目计划的纸。"


class PaddleOCRProvider:
    def __init__(
        self,
        fallback: OCRProvider | None = None,
        paddleocr_class_loader: Callable[[], type] | None = None,
    ) -> None:
        self.fallback = fallback or MockOCRProvider()
        self._paddleocr_class_loader = paddleocr_class_loader or self._load_paddleocr_class
        self._engine = None

    def extract_text(self, image_path: str | None) -> str:
        if not image_path:
            return self.fallback.extract_text(image_path)

        try:
            engine = self._get_engine()
            result = engine.predict(image_path)
            lines = self._extract_lines(result)
        except Exception:
            return self.fallback.extract_text(image_path)

        if not lines:
            return self.fallback.extract_text(image_path)
        return "PaddleOCR：" + "\n".join(lines)

    def _get_engine(self):
        if self._engine is None:
            paddleocr_class = self._paddleocr_class_loader()
            self._engine = paddleocr_class(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                lang="ch",
            )
        return self._engine

    @staticmethod
    def _load_paddleocr_class() -> type:
        from paddleocr import PaddleOCR

        return PaddleOCR

    @staticmethod
    def _extract_lines(result) -> list[str]:
        lines: list[str] = []
        for page in result or []:
            if isinstance(page, dict) and page.get("rec_texts"):
                lines.extend(str(text) for text in page["rec_texts"] if text)
                continue
            for item in page or []:
                if len(item) < 2:
                    continue
                text_score = item[1]
                if not text_score:
                    continue
                text = text_score[0]
                if text:
                    lines.append(str(text))
        return lines


def create_ocr_provider(provider_name: str | None) -> OCRProvider:
    normalized = (provider_name or "mock").strip().lower()
    if normalized == "paddleocr":
        return PaddleOCRProvider()
    return MockOCRProvider()
