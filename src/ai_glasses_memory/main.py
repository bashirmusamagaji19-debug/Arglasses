from __future__ import annotations

from fastapi import FastAPI

from ai_glasses_memory.api.routes import router

app = FastAPI(
    title="AI 眼镜实时视觉记忆助手",
    description="第一周系统骨架：模拟视觉问答、SQLite 记忆时间线和基础检索。",
    version="0.1.0",
)
app.include_router(router)
