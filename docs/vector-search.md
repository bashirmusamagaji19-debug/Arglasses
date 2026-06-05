# 向量语义检索

当前系统支持两种历史检索 provider：

- `lightweight`：低依赖规则检索，适合 Streamlit Cloud demo 和 fallback。
- `vector`：本地向量检索，适合更好的语义召回。

## 启用方式

本地启动向量检索：

```powershell
$env:AI_GLASSES_SEARCH_PROVIDER="vector"
$env:AI_GLASSES_EMBEDDING_PROVIDER="hash"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

也可以写入 `.env`：

```text
AI_GLASSES_SEARCH_PROVIDER=vector
AI_GLASSES_VECTOR_DB_PATH=data/vector_memory.sqlite3
AI_GLASSES_EMBEDDING_PROVIDER=hash
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
AI_GLASSES_EMBEDDING_DIMENSIONS=384
```

## 当前实现

第一版使用本地 hash embedding：

```text
MemoryEvent
-> question / answer / scene_summary / ocr_text
-> embedding text
-> HashEmbeddingProvider
-> SQLiteVectorIndex
```

搜索时：

```text
query
-> query embedding
-> SQLiteVectorIndex top-k
-> 用 memory_event.id 回查 SQLite
-> 返回完整 MemoryEvent
```

## 为什么先用 hash embedding

hash embedding 不是真正的大模型 embedding，但它有几个工程优势：

- 无 API key。
- 无调用费用。
- 无新增运行时重依赖。
- Streamlit Cloud 不会因为模型包变大而部署失败。
- 可以先验证向量索引、SQLite 回表、记忆删除同步这些架构边界。

后续可以切换到：

```text
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

届时需要安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[embedding]"
```

## 和记忆管理的关系

向量索引通过 `memory_event.id` 和 SQLite 关联。当前 pipeline 在以下操作后会自动重建索引：

- 新增记忆
- 删除单条记忆
- 清空全部记忆
- 只保留最近 N 条
- 去重记忆

这样可以避免 SQLite 已经删除记录，但向量索引仍然召回旧记忆。

## 面试表述

> 我把历史检索从规则相似度升级成 provider 化的向量检索。SQLite 继续保存完整 memory event，向量索引只保存 embedding 和 memory id，检索时先做向量 top-k，再回表返回完整记录。  
> 第一版没有直接引入 Chroma 或大型 embedding 模型，而是先用本地 hash embedding 和 SQLite 向量表验证架构边界，避免部署和成本问题。后续可以把 embedding provider 换成 bge-small-zh，或者把向量索引换成 FAISS / Chroma。
