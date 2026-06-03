# Pipeline 说明

## 第一周处理链路

第一周的 pipeline 负责串联最小闭环：

```text
用户问题 + 图片路径
-> 模拟 OCR
-> 模拟 VLM 回答
-> 模拟场景摘要
-> 延迟统计
-> 写入 SQLite
-> 返回 memory event
```

## 为什么要拆出 pipeline

如果把逻辑直接写在 FastAPI 或 Streamlit 里，后续接真实 OCR、VLM、ASR 和向量库时会很难维护。拆出 `MemoryPipeline` 后，API 和 UI 只负责输入输出，核心业务流程集中在一个地方。

这样有三个好处：

- 后续替换真实模型更容易。
- 测试可以直接验证业务流程，不依赖 UI。
- 面试时可以清楚解释系统链路。

## 当前 pipeline 输出

pipeline 返回一条已经写入数据库的 `MemoryEvent`，包含：

- 用户问题
- 模拟回答
- 模拟 OCR 文本
- 模拟场景摘要
- 图片路径
- 延迟统计
- 创建时间
