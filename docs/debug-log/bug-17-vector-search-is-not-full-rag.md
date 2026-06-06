# Bug 17：只有向量搜索展示还不能完整体现 RAG

## 现象

当前系统已经可以把视觉问答记忆写入 SQLite，并用 embedding 做历史检索。但用户追问：

```text
如果我想体现自己在项目中使用了 RAG，应该使用哪种方案？
```

这暴露出一个产品和架构边界问题：历史检索只是把相关记忆列出来，还没有把召回结果作为上下文生成新的回答。

## 排查过程

1. 检查当前链路，已有：

```text
MemoryEvent -> embedding text -> vector index -> search results
```

2. 对照 RAG 的标准三段式：

```text
Indexing：把资料写入向量库
Retrieval：根据问题召回相关资料
Generation：把召回资料作为上下文生成回答
```

3. 当前项目已经具备 indexing 和 retrieval，但 generation 只发生在“新图片问答”场景；历史检索结果只是 UI 展示，没有进入一个“基于历史记忆回答”的生成流程。

## 根因

这是概念边界没有完全闭合：

- 向量搜索是 RAG 的 retrieval 部分。
- 只展示搜索结果，不能完整说明系统做了 retrieval-augmented generation。
- 要在面试里可信地讲 RAG，需要展示“召回记忆 -> 构造上下文 -> 生成回答”的完整闭环。

## 修复

1. 新增 `RAGAnswerProvider` 和 `MemoryPipeline.answer_from_memory()`：

```text
question
-> search_provider.search(question, top_k)
-> context_memories
-> rag_answer_provider.answer(question, context_memories)
-> answer + context_memories
```

2. 新增 API：

```text
POST /memories/rag-answer
```

3. Streamlit UI 新增“历史记忆问答”入口，用户可以直接问：

```text
我刚才看到的鼠标是什么颜色？
```

系统会先检索历史记忆，再返回基于记忆的回答，并显示使用的上下文记忆。

4. 新增 `ChromaSearchProvider` 作为可选 provider：

```text
SQLite：保存完整 MemoryEvent
Chroma：保存 memory document embedding + metadata(memory_id, created_at)
RAG：检索 top-k memory -> 回表 -> 生成回答
```

Chroma 依赖放入 `rag` optional extra，默认 demo 不强制安装。

## 面试复盘说法

> 我一开始实现的是向量语义搜索：把视觉问答记录转成 embedding，搜索时按相似度召回历史记忆。但后来我意识到这只能说明做了 retrieval，还不能完整称为 RAG。  
>  
> 所以后续我把系统升级成“视觉记忆 RAG”：SQLite 保存完整 memory event，向量检索层负责召回 top-k 相关记忆，然后 RAG answer service 把这些记忆作为上下文生成回答。这样用户不只是看到搜索列表，还可以追问“我刚才看到的鼠标是什么颜色”，系统会基于历史记忆回答。  
>  
> 同时我把 Chroma 设计成可选 provider，避免默认 demo 被重依赖卡住；真实项目里可以用 Chroma 管理 embedding 和 metadata，用 SQLite 继续保存业务完整记录。
