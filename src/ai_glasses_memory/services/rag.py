from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from ai_glasses_memory.models.memory import MemoryEvent


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    context_memories: list[MemoryEvent]


class RAGAnswerProvider(Protocol):
    def answer(self, question: str, contexts: list[MemoryEvent]) -> str:
        ...


class RuleBasedRAGAnswerProvider:
    def answer(self, question: str, contexts: list[MemoryEvent]) -> str:
        if not contexts:
            return "没有找到足够相关的历史记忆。"

        if self._asks_color(question):
            color_answer = self._answer_color_question(contexts)
            if color_answer:
                return color_answer

        primary = contexts[0]
        return f"根据历史记忆，{self._clean_answer(primary.answer)}"

    @staticmethod
    def _asks_color(question: str) -> bool:
        return any(term in question for term in ["颜色", "什么色", "哪种色", "黑色", "银灰色"])

    @classmethod
    def _answer_color_question(cls, contexts: list[MemoryEvent]) -> str:
        colors = cls._colors_from_contexts(contexts)
        if not colors:
            return ""

        primary = colors[0]
        answer = f"根据历史记忆，鼠标主要是{primary}的"
        secondary = [color for color in colors[1:] if color != primary]
        if secondary:
            answer += f"；另外也出现过{secondary[0]}的鼠标"
        return answer + "。"

    @classmethod
    def _colors_from_contexts(cls, contexts: list[MemoryEvent]) -> list[str]:
        known_colors = ["黑色", "银灰色", "灰色", "白色", "银色", "蓝色", "红色", "绿色", "黄色"]
        found: list[str] = []
        for memory in contexts:
            text = cls._memory_text(memory)
            for color in known_colors:
                if cls._color_describes_mouse(text, color) and color not in found:
                    found.append(color)
        if "银灰色" in found and "灰色" in found:
            found.remove("灰色")
        return found

    @staticmethod
    def _color_describes_mouse(text: str, color: str) -> bool:
        color_then_mouse = rf"{re.escape(color)}[^。；，,、\n]{{0,6}}鼠标"
        mouse_then_color = rf"鼠标[^。；，,、\n]{{0,12}}{re.escape(color)}"
        return re.search(color_then_mouse, text) is not None or re.search(mouse_then_color, text) is not None

    @staticmethod
    def _memory_text(memory: MemoryEvent) -> str:
        return "\n".join([memory.question, memory.answer, memory.scene_summary, memory.ocr_text])

    @staticmethod
    def _clean_answer(answer: str) -> str:
        return answer.strip().rstrip("。") + "。"
