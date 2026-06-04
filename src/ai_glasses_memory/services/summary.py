from __future__ import annotations

from typing import Protocol


class SummaryProvider(Protocol):
    def summarize_scene(self, question: str, answer: str, ocr_text: str) -> str:
        ...


class RuleBasedSummaryProvider:
    def summarize_scene(self, question: str, answer: str, ocr_text: str) -> str:
        parts = [
            f"用户提问：{question}",
            f"视觉回答：{answer}",
        ]
        if ocr_text.strip():
            parts.append(f"OCR 文字：{ocr_text}")
        return "。".join(parts) + "。"


def create_summary_provider(provider_name: str | None = None) -> SummaryProvider:
    normalized = (provider_name or "rule_based").strip().lower()
    if normalized == "rule_based":
        return RuleBasedSummaryProvider()
    return RuleBasedSummaryProvider()
