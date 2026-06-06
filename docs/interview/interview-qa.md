# 面试问答准备

## 1. 这个项目为什么不是普通“摄像头 + ChatGPT”demo？

普通视觉问答 demo 只处理当前图片，回答完就结束。这个项目的重点是“视觉记忆”：每次交互都会被结构化成 `MemoryEvent`，写入 SQLite，并同步到检索索引。用户后续可以问“刚才看到了什么”“鼠标是什么颜色的”“屏幕上出现过什么项目”，系统会从历史记忆中召回相关上下文再回答。

## 2. 一次完整 pipeline 是怎么跑的？

```text
手机拍照 / 图片上传
-> 保存图片
-> OCR provider 提取文字
-> VLM provider 结合图片、OCR 和用户问题生成回答
-> Summary provider 生成场景摘要
-> SQLite 写入 MemoryEvent
-> Search provider 更新检索索引
-> UI 展示当前回答、OCR、摘要、时间线和历史问答
```

语音提问会先经过 ASR provider 转写成文本，再进入同一条视觉问答 pipeline。

这条 pipeline 的核心价值是模块边界清楚：ASR、OCR、VLM、Embedding、Search、RAG Answer 都可以替换，不需要重写 UI 或 API。

## 3. 为什么用 SQLite 保存 memory event？

SQLite 适合第一版视觉记忆系统：

- 依赖低，本地和云端 demo 都容易运行。
- 适合保存完整结构化记录。
- 时间线展示、删除、裁剪和去重都很直接。
- 后续接 Chroma / FAISS 时，可以用 `memory_event.id` 和向量索引关联。

向量库不适合替代 SQLite，因为向量库主要负责召回，不负责完整业务状态管理。

## 4. Chroma 在项目里负责什么？

Chroma 负责语义召回，不保存完整业务记录。系统会把 `question / answer / scene_summary / ocr_text` 拼成 document，写入 Chroma collection，并把 `memory_id` 放进 metadata。用户追问时，Chroma 返回 top-k 相关 document，系统再用 `memory_id` 回 SQLite 取完整 `MemoryEvent`。

## 5. 你怎么解释这个项目里的 RAG？

RAG 不是只做向量搜索。当前项目的 RAG 是：

```text
Retrieval: Chroma 从历史视觉记忆中召回 top-k
Context: 回表取完整 MemoryEvent 作为上下文
Generation: RAG answer provider 把上下文组织成回答
Evidence: UI 展示“使用的历史记忆”
```

所以用户看到的不是一堆搜索结果，而是基于历史记忆生成的答案。

## 6. 为什么要保留 lightweight 和 SQLite vector provider？

因为不同环境约束不同：

- lightweight provider 没有重依赖，适合测试和云端 fallback。
- SQLite vector provider 可以验证 embedding、向量索引、cosine similarity 和回表逻辑。
- Chroma provider 是当前默认 RAG 检索方案。

保留 provider 边界可以展示系统是渐进式演进的，不是把某个向量库写死在业务逻辑里。

## 7. 为什么默认 demo 不强制真实 VLM？

真实 VLM 会带来 API key、费用、服务可用性和图片大小限制。如果默认强制真实 VLM，demo 很容易因为网络、余额或依赖问题不可用。当前设计是默认 mock，配置完整时切换到 OpenAI-compatible provider，请求失败时 fallback，保证作品集 demo 可以稳定打开。

## 8. PaddleOCR 遇到过什么问题？

PaddleOCR 是重依赖，Windows CPU 环境下 PaddleOCR、PaddlePaddle、numpy、protobuf 等版本组合会影响运行。项目把 PaddleOCR 做成可选 provider：默认 mock OCR，本地需要时再安装 OCR 可选依赖。这样可以证明真实 OCR 能接入 pipeline，又不会让云端部署被重依赖卡住。

## 9. 记忆管理为什么重要？

视觉记忆系统会因为重复拍照和重复提问快速积累相似记录。如果不做管理，时间线会膨胀，检索也会被重复记忆干扰。所以项目加入了删除、清空、裁剪和保守近重复去重。更重要的是，这些操作放在 pipeline 层，后续可以同时维护 SQLite 和向量索引一致性。

## 10. 当前项目的主要限制是什么？

- 当前 ASR 是非流式音频上传版，还没有做实时麦克风和流式转写。
- 当前 RAG answer provider 仍偏规则型，不是生产级 LLM 生成器。
- 真实 VLM 依赖外部 OpenAI-compatible API 或自部署服务。
- Chroma 默认可以跑通 RAG 架构，但中文语义效果取决于 embedding provider。
- 当前是软件原型，还没有真正接入 RK3588 或智能眼镜硬件。

## 11. 后续最有价值的升级是什么？

按原计划，后续优先级是：

1. 把非流式 ASR 升级为实时麦克风或流式转写。
2. 做隐私模式和延迟面板，体现 AI 眼镜工程意识。
3. 接硬件端 HTTP 上传原型，让 RK3588 或手机端复用同一 pipeline。
4. 把 RAG answer provider 升级为可选 LLM provider，提高历史问答自然度。

## 12. 如果面试官问“你在项目中主要做了什么”怎么答？

我主要做了三件事：

1. 把视觉问答从一次性 demo 设计成可积累的 memory event pipeline。
2. 把 ASR、OCR、VLM、Embedding、Search 和 RAG Answer 都做成 provider 边界，降低真实模型和部署依赖风险。
3. 把历史检索升级成 Chroma RAG，让系统能基于过去看到的内容回答用户追问，并保留证据记忆方便解释。
