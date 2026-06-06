from __future__ import annotations

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

        primary = contexts[0]
        context_lines = [
            f"- {memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}：{memory.scene_summary or memory.answer}"
            for memory in contexts[:3]
        ]
        return (
            f"根据历史记忆，最相关的一次记录是：{primary.answer}\n\n"
            "相关记忆：\n"
            + "\n".join(context_lines)
        )
