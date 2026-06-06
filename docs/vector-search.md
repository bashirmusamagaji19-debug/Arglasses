# 向量语义检索与 Chroma RAG

## 当前状态

项目当前默认使用 Chroma 作为历史记忆 RAG 的检索后端：

```text
AI_GLASSES_SEARCH_PROVIDER=chroma
AI_GLASSES_CHROMA_PATH=data/chroma
AI_GLASSES_CHROMA_COLLECTION=visual_memory
```

同时仍保留两个本地 fallback：

- `lightweight`：低依赖规则检索。
- `vector`：SQLite-backed 本地向量索引。

这三个 provider 共享同一个 `SearchProvider` 边界，`MemoryPipeline.search_memories()` 不需要关心具体后端。

## Chroma RAG 数据流

```text
MemoryEvent
-> question / answer / scene_summary / ocr_text
-> embedding text
-> EmbeddingProvider
-> Chroma collection
-> query top-k
-> memory_id 回查 SQLite
-> RAGAnswerProvider 生成回答
```

SQLite 和 Chroma 的分工：

- SQLite：保存完整 `MemoryEvent`，包括问题、回答、场景摘要、OCR、图片路径和延迟。
- Chroma：保存用于召回的 document、embedding 和 metadata。
- `memory_id`：连接 Chroma 检索结果和 SQLite 完整记录。

## Embedding provider

默认 embedding provider 是 `hash`：

```text
AI_GLASSES_EMBEDDING_PROVIDER=hash
AI_GLASSES_EMBEDDING_DIMENSIONS=384
```

hash embedding 不是真正的大模型 embedding，主要用于：

- 自动化测试。
- 免费云端 demo fallback。
- 验证 Chroma / SQLite 回表 / 记忆管理同步。

本地要获得更好的中文语义检索效果，推荐切换到 sentence-transformers：

```text
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
AI_GLASSES_EMBEDDING_DIMENSIONS=512
```

安装可选依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[embedding]"
```

首次运行会下载模型。下载完成后模型会缓存在本机 Hugging Face cache 中。

## SQLite vector provider 的定位

`VectorSearchProvider` 不是当前默认后端，但它仍然有工程价值：

```text
MemoryEvent
-> EmbeddingProvider
-> SQLiteVectorIndex
-> cosine similarity
-> memory_id 回查 SQLite
```

它适合解释项目如何从“规则检索”过渡到“向量检索”，也适合在不引入 Chroma 的环境中验证 provider 边界。

启用方式：

```powershell
$env:AI_GLASSES_SEARCH_PROVIDER="vector"
$env:AI_GLASSES_VECTOR_DB_PATH="data/vector_memory.sqlite3"
$env:AI_GLASSES_EMBEDDING_PROVIDER="sentence_transformers"
$env:AI_GLASSES_EMBEDDING_MODEL="BAAI/bge-small-zh-v1.5"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 和记忆管理的关系

向量索引和 Chroma 都通过 `memory_event.id` 和 SQLite 关联。当前 pipeline 在以下操作后会维护检索索引：

- 新增记忆
- 删除单条记忆
- 清空全部记忆
- 只保留最近 N 条
- 去重记忆

这样可以避免 SQLite 已经删除记录，但检索索引仍然召回旧记忆。

## 一键验证

运行：

```powershell
.\.venv\Scripts\python.exe scripts\rag_smoke.py
```

预期能看到：

```text
question: 鼠标是什么颜色的？
answer: 根据历史记忆，鼠标主要是黑色的；另外也出现过银灰色的鼠标。
contexts: 2
```

## 面试表述

> 我把历史检索从关键词搜索升级成 provider 化的语义检索。SQLite 保存完整 memory event，Chroma 保存用于召回的 document、embedding 和 metadata。检索时先在 Chroma 做 top-k，再用 memory id 回 SQLite 取完整记录，最后由 RAG answer provider 生成用户可读答案。  
> 我保留 lightweight 和 SQLite vector provider，是为了让 demo 在低依赖环境下仍能运行，同时展示清晰的渐进式架构演进。
