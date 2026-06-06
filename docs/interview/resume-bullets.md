# 简历 Bullet 素材

## 项目名称

AI Glasses Memory Assistant | AI 眼镜视觉记忆 RAG 助手

## 一句话项目描述

构建面向 AI 眼镜场景的视觉记忆系统，支持手机/图片第一视角输入、OCR/VLM 场景理解、SQLite 记忆沉淀、Chroma 语义召回和基于历史记忆的 RAG 问答。

## 中文简历 Bullet

- 设计并实现 AI 眼镜视觉记忆 RAG 原型，将图片/手机拍照输入、OCR、VLM 问答、场景摘要、SQLite 记忆存储、Chroma 语义检索和历史追问串成完整 pipeline。
- 将历史检索抽象为 `SearchProvider`，支持 lightweight 规则检索、SQLite vector provider 和 Chroma provider，保证本地 demo、云端 fallback 和后续向量库升级可以共用同一业务入口。
- 设计 `MemoryEvent` 数据模型，结构化保存用户问题、视觉回答、场景摘要、OCR 文本、图片路径和延迟数据，并通过 `memory_id` 关联 SQLite 与 Chroma 检索结果。
- 接入可选 PaddleOCR 和 OpenAI-compatible VLM provider，默认保留 mock/fallback 策略，避免真实模型依赖、API 失败或云端部署缺包导致 demo 崩溃。
- 构建历史记忆 RAG 问答能力：使用 Chroma 召回 top-k 相关视觉记忆，再由 RAG answer provider 将上下文压缩成用户可读答案，并在 UI 中展示被使用的历史记忆作为证据。
- 增加记忆管理能力，支持单条删除、清空、裁剪和保守近重复去重，并在 pipeline 层维护 SQLite 与检索索引的一致性。
- 记录 20+ 条调试日志，覆盖 Streamlit Cloud 部署、PaddleOCR Windows 依赖、真实 VLM fallback、图片压缩、向量检索质量和 Chroma 依赖冲突等问题，形成可复盘的工程排障材料。

## English Resume Bullets

- Built an AI-glasses visual memory RAG prototype that connects first-person image input, OCR, VLM-based visual QA, structured memory storage, Chroma retrieval, and history-aware question answering.
- Designed provider boundaries for OCR, VLM, embedding, search, and RAG answer generation, enabling mock defaults, local fallback, and OpenAI-compatible model integration without changing the core pipeline.
- Modeled each interaction as a `MemoryEvent` stored in SQLite and linked Chroma retrieval documents back to full records through `memory_id`.
- Implemented Chroma-based top-k retrieval plus a RAG answer layer that turns recalled visual memories into user-readable answers while exposing the supporting memories in the UI.
- Added memory lifecycle operations including delete, clear, prune, and conservative deduplication, keeping the structured database and retrieval index synchronized.

## 技术栈写法

Python, FastAPI, Streamlit, SQLite, Chroma, sentence-transformers, PaddleOCR, OpenAI-compatible VLM API, pytest

## 面试时不要夸大的点

- 当前不是完整智能眼镜硬件产品，而是 AI 眼镜场景的软件原型。
- 当前 RAG answer provider 主要是规则型生成层，不是生产级 LLM 生成器。
- 默认 embedding 可以使用 hash fallback；本地高质量中文召回需要 sentence-transformers + `BAAI/bge-small-zh-v1.5`。
- 真实 VLM 是可选 provider，默认 demo 仍可在无 API key 环境下运行。
