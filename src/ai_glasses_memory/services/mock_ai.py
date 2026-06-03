from __future__ import annotations


class MockAIService:
    """第一周使用的模拟 OCR / VLM 服务。"""

    def run_ocr(self, image_path: str | None) -> str:
        # 修改这里的模拟文案只会影响之后新生成的记忆，SQLite 里已有的旧记录不会自动变化。
        if image_path:
            return "模拟 OCR：画面中可能包含电脑屏幕、课程笔记、水杯和一张写着 AI 眼镜项目计划的纸。"
        return "模拟 OCR：画面中可能包含电脑屏幕、课程笔记、水杯和一张写着 AI 眼镜项目计划的纸。"

    def answer_question(self, question: str, ocr_text: str) -> str:
        return (
            f"模拟 VLM 回答：针对问题“{question}”，系统根据当前画面和 OCR 文本判断，"
            f"相关线索是：{ocr_text}"
        )

    def summarize_scene(self, question: str, answer: str, ocr_text: str) -> str:
        return (
            "模拟场景摘要：本次交互模拟了 AI 眼镜看到当前场景、"
            f"读取文字并回答用户问题的过程。问题：{question}。OCR：{ocr_text}。"
        )
