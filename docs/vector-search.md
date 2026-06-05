# 向量语义检索

当前系统支持两种历史检索 provider：

- `lightweight`：低依赖规则检索，适合 Streamlit Cloud demo 和 fallback。
- `vector`：本地向量检索，适合更好的语义召回。

## 启用方式

本地启动向量检索：

```powershell
$env:AI_GLASSES_SEARCH_PROVIDER="vector"
$env:AI_GLASSES_EMBEDDING_PROVIDER="sentence_transformers"
$env:AI_GLASSES_EMBEDDING_MODEL="BAAI/bge-small-zh-v1.5"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

也可以写入 `.env`：

```text
AI_GLASSES_SEARCH_PROVIDER=vector
AI_GLASSES_VECTOR_DB_PATH=data/vector_memory.sqlite3
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
AI_GLASSES_EMBEDDING_DIMENSIONS=512
```

## 当前实现

推荐本地使用 `sentence_transformers` + `BAAI/bge-small-zh-v1.5`：

```text
MemoryEvent
-> question / answer / scene_summary / ocr_text
-> embedding text
-> SentenceTransformersEmbeddingProvider
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

## hash embedding 的定位

hash embedding 不是真正的大模型 embedding，检索效果会明显弱于 `bge-small-zh`。它只适合：

- 自动化测试。
- 云端 demo fallback。
- 验证向量索引、SQLite 回表、记忆删除同步这些架构边界。

如果要真实提升中文语义检索效果，应使用：

```text
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

届时需要安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[embedding]"
```

首次运行会下载模型。下载完成后模型会缓存在本机 Hugging Face cache 中。

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
