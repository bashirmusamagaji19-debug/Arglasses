# 记忆管理功能

## 目标

当前系统会把每次视觉问答写入 SQLite。手机拍照和 VLM 调试时很容易反复提交相似问题，时间线会快速变长，轻量语义检索也会被重复记忆干扰。

这一阶段加入记忆管理能力：

```text
单条删除
清空全部
只保留最近 N 条
保守近重复去重
```

这一步不是为了做复杂功能，而是为了让 demo 数据可控，并为后续 Chroma / FAISS 向量检索做准备。

## 当前实现

核心能力放在 `MemoryStore`：

- `delete_event(event_id)`：删除指定记忆。
- `clear_events()`：清空全部记忆。
- `prune_events(keep_latest)`：只保留最新 N 条，删除更旧记录。
- `dedupe_events()`：保留最新一条。有 OCR 文本时按 `question + ocr_text` 判断近重复；没有 OCR 文本时按 `question + answer + scene_summary` 精确去重。

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

## 为什么不是纯精确去重

你遇到的真实例子是：

```text
问题相同：手上拿着什么
OCR 相同：PaddleOCR：所得皆所顺 如意
回答差异：所得皆所愿 / 所得皆所顺
```

这两条从用户视角看是重复记忆，但第一版规则把 `answer` 也纳入完全匹配，所以只要 VLM 输出一个字不同，就不会被删掉。

因此现在改成保守近重复：

- 有 OCR 文本时，同一问题和同一 OCR 文本通常来自同一张图或同一场景，可以去重。
- 没有 OCR 文本时，继续使用完整字段精确去重，避免误删不同场景。
- 去重永远保留时间线里最新的一条。

## 和后续向量检索的关系

后续接入 Chroma / FAISS 时，记忆管理会影响两份数据：

```text
SQLite memory_events
向量索引中的 embedding
```

所以后续不能只删除 SQLite。需要让删除、清空、裁剪、去重同时更新向量索引，保证检索结果不会召回已经被删除的记忆。

当前先把管理接口放在 `MemoryPipeline`，后续可以在 pipeline 内部统一处理 SQLite 和 vector index 的一致性。

## 面试表述

> 我在做轻量语义检索时发现，重复提交和过长时间线会明显影响召回质量。第一版我做的是精确去重，但真实测试里 VLM 回答只差一个字就无法去重。  
> 所以后来我把规则改成保守近重复去重：有 OCR 时按同一问题和同一 OCR 文本判断重复，没有 OCR 时仍然使用完整字段精确去重。这样既能清掉重复拍摄/重复提交产生的数据，又尽量避免误删不同场景。  
> 这一步的重点不是 UI 按钮，而是把记忆生命周期管理放到 pipeline 层，后续接入 Chroma / FAISS 时，可以在同一个入口同时维护 SQLite 和向量索引一致性。
