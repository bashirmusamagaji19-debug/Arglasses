# Phase 3.4：轻量语义检索原型

## 目标

当前系统已经可以把每次视觉问答写入 SQLite。原来的搜索只做关键词 `LIKE` 匹配，适合查精确词，但不适合问：

```text
我刚才拿过什么？
之前看到的那个鼠标是什么？
屏幕上显示过什么项目？
```

本阶段先实现轻量语义检索原型，不引入 Chroma / FAISS / embedding 模型，避免在项目主链路还没完全稳定时增加重依赖。

## 当前实现

新增 `LightweightSemanticSearchProvider`：

```text
query
-> 读取最近 memory events
-> 拼接 question / answer / scene_summary / ocr_text
-> 关键词命中加权
-> 中文字符、bigram、英文 token 相似度
-> 简单意图增强：拿过 / 屏幕 / 文字
-> 排序返回相关记忆
```

它不改变 SQLite 表结构，也不新增依赖。

## 为什么不直接上 Chroma / FAISS

当前阶段的目标是先验证“视觉记忆召回”的产品形态：

- 搜索入口是否有用。
- 用户是否会问历史记忆问题。
- 记忆字段如何组织更利于检索。
- UI 如何展示召回结果。

Chroma / FAISS 后续会带来 embedding 模型、索引持久化、向量库依赖和部署体积问题。先用轻量 provider 跑通边界更稳。

## 后续替换路径

后续可以把检索模块升级为 provider：

```text
SearchProvider
├── LightweightSemanticSearchProvider
└── VectorSearchProvider
    ├── Chroma
    └── FAISS
```

届时 `MemoryPipeline.search_memories()` 不需要大改，只替换 provider 实现。

## 面试表述

> 我先实现了一个轻量语义检索原型，用最近 memory event 的问题、回答、场景摘要和 OCR 文本做相似度排序，先验证“视觉记忆召回”的产品形态。  
> 后续再把这个 provider 替换成 Chroma 或 FAISS，接入 embedding 模型做真正的向量检索。  
> 这样可以避免项目早期被向量库依赖和部署问题卡住，同时保留清晰的升级路径。
