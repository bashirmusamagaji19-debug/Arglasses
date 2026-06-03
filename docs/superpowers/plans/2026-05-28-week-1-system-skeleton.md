# 第一周：系统骨架实施计划

> **给自动化执行者的说明：** 实施本计划时，需要使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步执行。步骤使用 checkbox（`- [ ]`）语法跟踪状态。

**目标：** 第一周完成 AI 眼镜实时视觉记忆助手的最小可运行骨架，跑通“输入图片/问题 -> 模拟处理 -> 写入记忆 -> UI 展示时间线”的闭环。

**架构：** 第一周不接真实 VLM、ASR、OCR 和向量数据库，先用清晰的接口和模拟实现建立系统边界。后端使用 FastAPI 暴露处理与查询接口，UI 使用 Streamlit 做演示界面，SQLite 负责保存 memory event。

**技术栈：** Python, FastAPI, Pydantic, SQLite, Streamlit, pytest, Markdown

---

## 1. 第一周定位

第一周是“系统骨架周”，核心任务不是做复杂 AI 能力，而是把项目的工程底座搭稳。

本周结束时，项目应该能回答三个问题：

1. 这个 AI 眼镜项目的代码结构是什么？
2. 一次视觉问答交互在系统中怎么流动？
3. 场景记忆如何被建模、保存、展示和检索？

第一周暂时不追求：

- 真实多模态模型回答。
- 真实语音输入。
- 真实 OCR。
- 向量数据库。
- 实时视频流。

这些能力后续逐阶段补齐。第一周的价值在于搭好“以后往哪里插模块”的骨架。

## 2. 本周应实现的用户效果

用户打开 Streamlit UI 后，可以完成下面流程：

1. 上传一张图片，或者先使用项目内置示例图片。
2. 输入一个问题，例如“我刚才看到了什么？”
3. 点击提交。
4. 系统返回一段模拟回答和模拟场景摘要。
5. 系统把本次交互记录为 memory event。
6. UI 展示历史 memory timeline。
7. 用户可以输入关键词搜索历史记录。
8. UI 展示本次处理的耗时统计。

这就是第一周的最小闭环。

## 3. 建议项目结构

第一周建议创建下面结构：

```text
D:\ARglasses
  README.md
  pyproject.toml
  .env.example
  src/
    ai_glasses_memory/
      __init__.py
      main.py
      config.py
      api/
        __init__.py
        routes.py
      models/
        __init__.py
        memory.py
      services/
        __init__.py
        mock_ai.py
        memory_store.py
        pipeline.py
        latency.py
      ui/
        streamlit_app.py
  tests/
    test_memory_store.py
    test_pipeline.py
  docs/
    notes/
      01-system-skeleton.md
    architecture/
      system-architecture.md
      data-model.md
      pipeline.md
```

文件职责：

- `README.md`：项目入口说明，先写第一版中文 README。
- `pyproject.toml`：Python 项目配置和依赖。
- `.env.example`：环境变量示例。
- `src/ai_glasses_memory/main.py`：FastAPI 应用入口。
- `src/ai_glasses_memory/config.py`：配置读取。
- `src/ai_glasses_memory/api/routes.py`：API 路由。
- `src/ai_glasses_memory/models/memory.py`：memory event 数据模型。
- `src/ai_glasses_memory/services/mock_ai.py`：模拟 OCR、模拟 VLM、模拟场景摘要。
- `src/ai_glasses_memory/services/memory_store.py`：SQLite 写入、读取、搜索。
- `src/ai_glasses_memory/services/pipeline.py`：第一周端到端处理流程。
- `src/ai_glasses_memory/services/latency.py`：耗时记录工具。
- `src/ai_glasses_memory/ui/streamlit_app.py`：Streamlit 演示界面。
- `tests/test_memory_store.py`：验证 memory event 存储和搜索。
- `tests/test_pipeline.py`：验证最小 pipeline。
- `docs/notes/01-system-skeleton.md`：第一周详细学习笔记。
- `docs/architecture/system-architecture.md`：系统架构说明。
- `docs/architecture/data-model.md`：memory event 数据模型说明。
- `docs/architecture/pipeline.md`：第一周处理链路说明。

## 4. 第一周任务拆分

### Task 1：初始化 Python 项目和基础文档

**目标：** 建立可运行、可测试、可持续写文档的项目底座。

**文件：**

- 创建：`README.md`
- 创建：`pyproject.toml`
- 创建：`.env.example`
- 创建：`src/ai_glasses_memory/__init__.py`
- 创建：`tests/`

**验收标准：**

- 可以安装项目依赖。
- 可以运行 `pytest`。
- README 明确说明项目定位是 AI 眼镜实时视觉记忆助手。
- README 使用中文为主。

### Task 2：定义 memory event 数据模型

**目标：** 明确系统“记住”的最小数据单元。

**建议字段：**

- `id`
- `created_at`
- `question`
- `answer`
- `scene_summary`
- `ocr_text`
- `image_path`
- `latency_ms`

**文件：**

- 创建：`src/ai_glasses_memory/models/memory.py`
- 创建：`docs/architecture/data-model.md`

**验收标准：**

- 数据模型能表达一次视觉问答交互。
- 文档能解释为什么需要 `question`、`answer`、`scene_summary`、`ocr_text` 和 `created_at`。
- 能说明这个模型后续如何扩展到向量检索。

### Task 3：实现 SQLite memory store

**目标：** 把 memory event 存入本地数据库，并支持按时间线读取和关键词搜索。

**文件：**

- 创建：`src/ai_glasses_memory/services/memory_store.py`
- 创建：`tests/test_memory_store.py`

**能力：**

- 初始化数据库表。
- 新增 memory event。
- 按时间倒序读取 timeline。
- 根据关键词搜索 `question`、`answer`、`scene_summary`、`ocr_text`。

**验收标准：**

- 测试能覆盖新增、读取和搜索。
- 搜索不需要语义检索，第一周只做关键词检索。

### Task 4：实现模拟 AI 服务

**目标：** 先不依赖真实模型，用模拟服务跑通系统链路。

**文件：**

- 创建：`src/ai_glasses_memory/services/mock_ai.py`

**能力：**

- 模拟 OCR：返回固定 OCR 文本。
- 模拟 VLM：根据用户问题返回固定回答。
- 模拟场景摘要：根据 OCR 和问题生成摘要。

**验收标准：**

- 不需要 API key。
- 不需要安装大模型。
- 输出格式稳定，方便后续替换真实 OCR 和 VLM。

### Task 5：实现延迟统计工具

**目标：** 从第一周开始培养低延迟系统意识。

**文件：**

- 创建：`src/ai_glasses_memory/services/latency.py`

**能力：**

- 记录单个阶段耗时。
- 记录端到端耗时。
- 返回毫秒级 latency 字典。

**验收标准：**

- pipeline 输出里包含耗时字段。
- UI 可以展示耗时。

### Task 6：实现第一版 pipeline

**目标：** 串起“输入问题 -> 模拟 OCR -> 模拟 VLM -> 生成摘要 -> 写入记忆 -> 返回结果”的闭环。

**文件：**

- 创建：`src/ai_glasses_memory/services/pipeline.py`
- 创建：`tests/test_pipeline.py`
- 创建：`docs/architecture/pipeline.md`

**验收标准：**

- 测试能证明 pipeline 会生成回答。
- 测试能证明 pipeline 会写入 memory store。
- pipeline 返回 answer、scene_summary、ocr_text、latency_ms。

### Task 7：实现 FastAPI 接口

**目标：** 暴露后端服务接口，为 UI 和后续扩展做准备。

**文件：**

- 创建：`src/ai_glasses_memory/main.py`
- 创建：`src/ai_glasses_memory/api/__init__.py`
- 创建：`src/ai_glasses_memory/api/routes.py`

**接口：**

- `GET /health`
- `POST /ask`
- `GET /memories`
- `GET /memories/search`

**验收标准：**

- `/health` 返回服务状态。
- `/ask` 能触发 pipeline。
- `/memories` 能返回 timeline。
- `/memories/search` 能按关键词搜索历史记录。

### Task 8：实现 Streamlit UI

**目标：** 提供第一版可演示界面。

**文件：**

- 创建：`src/ai_glasses_memory/ui/streamlit_app.py`

**界面内容：**

- 项目标题。
- 图片上传入口。
- 问题输入框。
- 提交按钮。
- 当前回答展示。
- OCR 文本展示。
- 场景摘要展示。
- 延迟统计展示。
- memory timeline 展示。
- 关键词搜索框。

**验收标准：**

- 用户可以通过 UI 完成第一周最小闭环。
- UI 文案使用中文。

### Task 9：写第一周详细学习笔记

**目标：** 把第一周学到的工程和项目决策沉淀成可复习材料。

**文件：**

- 创建：`docs/notes/01-system-skeleton.md`

**笔记必须包含：**

- 本阶段目标。
- 和 AI 眼镜项目定位的关系。
- 我们在对话中确定的设计决策。
- FastAPI、Streamlit、SQLite、Pydantic 的作用。
- memory event 为什么这样设计。
- pipeline 为什么要拆出来。
- 模拟服务为什么有价值。
- 第一周遇到的问题和解决方法。
- 面试可能怎么问。
- 简历 bullet 素材。

**验收标准：**

- 笔记使用中文。
- 笔记是 Markdown。
- 笔记足够详细，可以用于第一周复盘。

### Task 10：第一周收尾验证

**目标：** 确认第一周产出能运行、能测试、能讲清楚。

**必须运行：**

```powershell
pytest
```

```powershell
python -m uvicorn ai_glasses_memory.main:app --reload
```

```powershell
streamlit run src/ai_glasses_memory/ui/streamlit_app.py
```

**验收标准：**

- 测试通过。
- FastAPI 服务能启动。
- Streamlit UI 能启动。
- 可以完成一次模拟视觉问答。
- 可以看到 memory timeline。
- 可以搜索历史记录。
- 学习笔记已完成。

## 5. 第一周学习目标

本周你应该重点理解：

- 为什么项目要先做骨架，而不是直接接大模型。
- FastAPI 在 AI 应用中承担什么角色。
- Streamlit 为什么适合早期 demo。
- SQLite 为什么适合第一版记忆时间线。
- memory event 是什么，为什么它是记忆系统的核心。
- pipeline 层为什么重要。
- 模拟服务如何降低外部依赖风险。
- 延迟统计为什么从第一周就要做。

## 6. 第一周面试准备目标

本周结束后，你应该能回答：

1. 你的项目为什么叫 AI 眼镜记忆助手，而不是普通视觉问答 demo？
2. 你这个系统的核心链路是什么？
3. 什么是 memory event？
4. 你为什么第一版使用 SQLite？
5. 你为什么先用模拟服务，而不是直接接真实 VLM？
6. FastAPI 和 Streamlit 在项目里分别负责什么？
7. 后续如何把 OCR、VLM、ASR、向量数据库插入当前架构？

## 7. 第一周不做什么

为了控制学习节奏，本周明确不做：

- 不接真实摄像头实时流。
- 不接真实 ASR。
- 不接真实 VLM。
- 不接 Chroma 或 FAISS。
- 不做复杂 UI 美化。
- 不做 Docker。
- 不做部署。

这些不是放弃，而是为了让第一周先形成稳定闭环。

## 8. 第一周完成定义

第一周完成的定义是：

- 项目结构清晰。
- 后端服务能启动。
- UI 能启动。
- 模拟问答链路能跑通。
- memory event 能写入 SQLite。
- timeline 能展示。
- 关键词搜索能工作。
- 延迟统计能展示。
- 第一篇学习笔记完成。

达到这些标准后，再进入第二周“视觉输入与 OCR”。
