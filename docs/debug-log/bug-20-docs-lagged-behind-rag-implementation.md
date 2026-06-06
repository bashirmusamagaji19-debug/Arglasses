# Bug 20：文档和 demo 脚本落后于 RAG 实现

## 现象

项目代码已经支持：

```text
SQLite memory event
-> Chroma 向量检索
-> RAG 历史追问
-> 使用的历史记忆可解释展示
```

但架构文档和 30 秒 demo 脚本仍然停留在第一版 Web MVP：

```text
模拟 OCR / 模拟 VLM
关键词搜索
下一步接真实模型
```

这会导致面试和演示时讲法落后于代码能力。

## 排查过程

1. 检查 `docs/architecture/system-architecture.md`，发现仍然描述 `MockAIService` 和关键词检索。

2. 检查 `docs/interview/demo-script-30s.md`，发现演示重点还是“上传图片 -> 模拟回答 -> 搜索模拟记录”，没有展示 Chroma 和 RAG 问答。

3. 对照当前代码能力，确认最应该展示的是：

```text
图片输入
-> 视觉问答写入 memory
-> Chroma 召回相关历史记忆
-> 历史记忆问答生成自然回答
```

## 根因

项目功能迭代速度快，但文档没有作为验收物同步更新。对于作品集项目，这会削弱面试表达：代码里有 RAG，但讲稿仍像普通图片问答 demo。

## 修复

1. 更新 `docs/architecture/system-architecture.md`：

- 说明当前是视觉记忆 RAG 原型。
- 增加 Mermaid 架构图。
- 明确 SQLite 保存业务记录，Chroma 保存 memory document embedding 和 metadata。
- 写清楚 RAG 闭环：检索 top-k -> 回表 -> 生成回答。

2. 更新 `docs/interview/demo-script-30s.md`：

- 演示“我刚才看到了什么？”
- 演示“鼠标是什么颜色的？”
- 指出 RAG 回答和“使用的历史记忆”列表。

3. 新增 `scripts/rag_smoke.py`：

```powershell
.\.venv\Scripts\python.exe scripts\rag_smoke.py
```

预期输出：

```text
question: 鼠标是什么颜色的？
answer: 根据历史记忆，鼠标主要是黑色的；另外也出现过银灰色的鼠标。
contexts: 2
```

## 面试复盘说法

> 做作品集项目时，我不只关注代码能跑，也把文档和演示脚本作为交付的一部分。RAG 功能完成后，我发现旧文档仍然在讲 mock OCR 和关键词搜索，这会让面试表达低估项目真实能力。  
>  
> 所以我同步更新了架构图、demo 脚本和 smoke 验证脚本，让项目可以清楚展示“视觉记忆写入、Chroma 检索、RAG 历史追问、上下文可解释展示”这一整条链路。
