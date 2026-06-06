# Phase 3.4：历史记忆检索与 RAG

## 目标

当前系统已经不是单纯关键词搜索，而是完成了从“历史检索”到“视觉记忆 RAG”的升级：

```text
用户历史追问
-> 检索 provider 召回相关 memory events
-> RAG answer provider 基于召回上下文生成回答
-> UI 展示回答和使用的历史记忆
```

这个阶段的目标是让 AI 眼镜系统不只回答当前图片，还能围绕过去看到的内容继续追问：

```text
鼠标是什么颜色的？
刚才看到的屏幕上是什么项目？
我手上拿过什么东西？
```

## 当前检索 provider

系统保留多个检索 provider，方便在本地、云端 demo 和测试环境之间切换：

```text
SearchProvider
├── LightweightSemanticSearchProvider
├── VectorSearchProvider
└── ChromaSearchProvider
```

### `lightweight`

低依赖规则检索，不需要 embedding 模型和向量数据库。它会读取最近的 memory events，把 `question / answer / scene_summary / ocr_text` 拼成文本，再用中文字符、bigram、英文 token 和简单意图增强计算相似度。

定位：

- 自动化测试。
- 云端 demo fallback。
- 向量依赖不可用时保持历史检索入口可用。

### `vector`

本地 SQLite 向量检索 provider。它使用 `EmbeddingProvider` 生成向量，并把向量写入 SQLite vector table。检索时先做 cosine similarity 排序，再用 `memory_event.id` 回表取完整事件。

定位：

- 验证 embedding provider、向量索引、SQLite 回表和记忆删除同步这些架构边界。
- 在不引入 Chroma 时提供本地向量检索方案。

### `chroma`

当前默认 RAG 检索 provider。它使用 Chroma collection 保存 memory document、embedding 和 metadata，检索时返回 memory id，再回 SQLite 读取完整 memory event。

默认配置：

```text
AI_GLASSES_SEARCH_PROVIDER=chroma
AI_GLASSES_CHROMA_PATH=data/chroma
AI_GLASSES_CHROMA_COLLECTION=visual_memory
AI_GLASSES_EMBEDDING_PROVIDER=hash
```

本地要提升中文语义召回质量，可以切换到：

```text
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
AI_GLASSES_EMBEDDING_DIMENSIONS=512
```

## SQLite 和 Chroma 的分工

```text
SQLite memory_events
├── question
├── answer
├── scene_summary
├── ocr_text
├── image_path
└── latency_ms

Chroma visual_memory
├── document: question / answer / scene_summary / ocr_text
├── embedding
└── metadata: memory_id / created_at
```

SQLite 保存完整业务记录，Chroma 负责语义召回。这样可以避免把完整业务状态塞进向量库，也方便删除、裁剪、去重后通过 memory id 保持一致性。

## RAG 闭环

检索本身只能返回相关记忆，不能直接回答用户问题。当前系统在检索后增加了 `RuleBasedRAGAnswerProvider`：

```text
历史追问
-> Chroma top-k 召回
-> 回表取完整 MemoryEvent
-> RuleBasedRAGAnswerProvider 生成回答
-> UI 展示回答 + 使用的历史记忆
```

例如：

```text
问题：鼠标是什么颜色的？
回答：根据历史记忆，鼠标主要是黑色的；另外也出现过银灰色的鼠标。
```

这就是项目中可以讲清楚的 RAG：retrieval 负责找相关历史记忆，generation 负责把上下文组织成用户可读答案。

## 为什么保留多个 provider

Chroma 是当前默认选择，但项目仍保留 lightweight 和 SQLite vector provider，原因是：

- 免费云端部署可能不适合安装所有重依赖。
- 自动化测试需要低成本、确定性的 fallback。
- 面试时可以展示清晰的 provider 边界和渐进式升级路线。
- 后续接 FAISS、本地向量库或云端向量数据库时，pipeline 不需要大改。

## 一键验证

本地运行：

```powershell
.\.venv\Scripts\python.exe scripts\rag_smoke.py
```

预期能看到类似输出：

```text
question: 鼠标是什么颜色的？
answer: 根据历史记忆，鼠标主要是黑色的；另外也出现过银灰色的鼠标。
contexts: 2
```

## 面试表述

> 我把历史记忆检索设计成 provider 边界：早期先用 lightweight 规则检索验证产品形态，随后加入 SQLite vector provider 验证向量索引和回表逻辑，最后把默认检索升级到 Chroma。  
> 当前系统的 SQLite 负责保存完整 memory event，Chroma 负责语义召回，RAG answer provider 负责把召回结果组织成答案。这样系统不是简单的向量搜索，而是一个完整的 retrieval -> context -> generation 闭环。
