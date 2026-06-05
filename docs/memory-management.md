# 记忆管理功能

## 目标

当前系统会把每次视觉问答写入 SQLite。手机拍照和 VLM 调试时很容易反复提交相似问题，时间线会快速变长，轻量语义检索也会被重复记忆干扰。

这一阶段先加入记忆管理能力：

```text
单条删除
清空全部
只保留最近 N 条
精确去重
```

这一步不是为了做复杂功能，而是为了让 demo 数据可控，并为后续 Chroma / FAISS 向量检索做准备。

## 当前实现

核心能力放在 `MemoryStore`：

- `delete_event(event_id)`：删除指定记忆。
- `clear_events()`：清空全部记忆。
- `prune_events(keep_latest)`：只保留最新 N 条，删除更旧记录。
- `dedupe_events()`：按 `question + answer + scene_summary + ocr_text` 精确去重，保留最新一条。

`MemoryPipeline` 只负责转发这些操作，避免 UI / API 直接操作 SQLite。

FastAPI 入口：

```text
DELETE /memories/{memory_id}
DELETE /memories
POST /memories/prune?keep_latest=50
POST /memories/dedupe
```

Streamlit UI 入口：

- 时间线里可以删除单条记忆。
- 搜索栏下方有“裁剪记忆”“去重记忆”“清空全部记忆”。
- 清空全部需要先勾选确认，避免演示时误点。

## 为什么先做精确去重

现在没有 embedding，也没有稳定的向量索引。若直接做“语义去重”，可能把相似但并不相同的记忆删掉，例如：

```text
手上拿的是鼠标
桌上放着鼠标
屏幕上显示鼠标图片
```

这些句子语义接近，但在视觉记忆系统里可能代表不同场景。因此当前只做精确去重，主要处理重复点击提交、重复拍同一张图、重复 API 调试产生的数据。

## 和后续向量检索的关系

后续接入 Chroma / FAISS 时，记忆管理会影响两份数据：

```text
SQLite memory_events
向量索引中的 embedding
```

所以后续不能只删除 SQLite。需要让删除、清空、裁剪、去重同时更新向量索引，保证检索结果不会召回已经被删除的记忆。

当前先把管理接口放在 `MemoryPipeline`，后续可以在 pipeline 内部统一处理 SQLite 和 vector index 的一致性。

## 面试表述

> 我在做轻量语义检索时发现，重复提交和过长时间线会明显影响召回质量，所以先补了记忆管理能力，包括单条删除、清空、保留最近 N 条和精确去重。  
> 这一步的重点不是 UI 按钮，而是把记忆生命周期管理放到 pipeline 层，后续接入 Chroma / FAISS 时，可以在同一个入口同时维护 SQLite 和向量索引一致性。
