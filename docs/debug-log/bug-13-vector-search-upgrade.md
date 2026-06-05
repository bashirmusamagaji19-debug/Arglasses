# Bug 13：轻量语义检索到向量检索的升级

## 背景

当前流程已经跑通：

```text
手机/网页输入
-> OCR / VLM
-> 写入 SQLite
-> 时间线展示
-> 历史搜索
```

但轻量语义检索依赖规则、字符重叠和少量意图增强。它能改善关键词搜索，但遇到更抽象的问题、重复记忆、mock 旧记录和长时间线时，仍然会出现答非所问。

## 目标

升级成更好的语义架构，同时保持部署可控：

```text
SearchProvider
├── LightweightSemanticSearchProvider
└── VectorSearchProvider
```

UI 和 API 仍然调用 `MemoryPipeline.search_memories()`，不直接依赖向量库。

## 处理方案

新增三个边界：

- `EmbeddingProvider`：负责把文本转成向量。
- `SQLiteVectorIndex`：负责保存 memory id 和向量。
- `VectorSearchProvider`：负责 query embedding、向量 top-k、SQLite 回表。

第一版默认使用 `HashEmbeddingProvider`，原因是：

- 不需要 API key。
- 不产生费用。
- 不增加 Streamlit Cloud 部署体积。
- 先验证架构边界，再替换成真实 embedding 模型。

## 和记忆管理的关系

向量索引必须和 SQLite 同步。否则会出现：

```text
SQLite 记忆已删除
但向量索引仍然召回旧 memory id
```

因此 pipeline 在新增、删除、清空、裁剪、去重后会调用 `rebuild_index()`。

第一版采用重建索引，而不是逐条精细同步。当前记忆数据量小，重建更简单，也更不容易产生一致性 bug。

## 后续升级

后续可以逐步替换：

```text
HashEmbeddingProvider
-> SentenceTransformersEmbeddingProvider
-> BAAI/bge-small-zh-v1.5
-> 云端 embedding API
```

向量索引也可以替换：

```text
SQLiteVectorIndex
-> FAISS
-> Chroma
```

## 面试复盘说法

> 我没有一开始就上 Chroma 或 FAISS，而是先把检索能力抽象成 provider。第一阶段用轻量规则检索验证产品闭环，等 OCR/VLM/手机输入和记忆管理都跑通后，再加入向量检索。  
> 向量检索第一版用本地 hash embedding 和 SQLite 向量表，重点不是追求最强效果，而是验证 SQLite 结构化记忆、向量索引和 memory id 回表之间的架构关系。后续可以无缝替换成 bge-small-zh 或 FAISS / Chroma。
