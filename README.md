# AI 眼镜视觉记忆系统原型

这是一个面向 AI 眼镜场景的视觉记忆系统原型。当前阶段先实现可展示 Web MVP：用模拟 OCR / 模拟 VLM 跑通“图片和问题输入 -> 场景理解 -> 记忆写入 -> 时间线展示 -> 历史检索”的最小闭环。

## 当前 MVP

已实现：

- 输入问题和图片。
- 使用手机浏览器摄像头拍照，模拟 AI 眼镜第一视角输入。
- 使用模拟 OCR / 模拟 VLM 生成回答和场景摘要。
- 将 memory event 写入 SQLite。
- 在 Streamlit UI 展示记忆时间线。
- 支持基于关键词的历史搜索。
- 记录 OCR、VLM、摘要和总耗时。

当前阶段不追求真实 AI 能力，重点是先有一个能上线、能打开、能演示的作品集入口。

## 总路线

1. 部署 Web MVP。
2. 接入手机摄像头，模拟眼镜第一视角。
3. 接入真实 OCR / VLM / 向量检索 / ASR。
4. 接入 RK3588 + 摄像头硬件输入原型。
5. 整理 README、demo 视频、简历和面试稿。
6. 回头系统学习代码细节和原理。

## 技术栈

- Python 3.11+
- FastAPI
- Streamlit
- SQLite
- pytest

## 本地运行

安装依赖：

```powershell
python -m pip install -e ".[dev]"
```

运行测试：

```powershell
python -m pytest -q
```

启动后端 API：

```powershell
python -m uvicorn ai_glasses_memory.main:app --reload
```

启动 Web UI：

```powershell
python -m streamlit run app.py
```

打开：

```text
http://localhost:8501
```

## 部署

部署入口是根目录的 `app.py`。

最快方案是 Streamlit Community Cloud：

```text
Main file path: app.py
```

Render 也可直接使用 `render.yaml`。详细步骤见 [docs/deployment.md](docs/deployment.md)。

## 手机摄像头演示

线上部署后，用手机浏览器打开 demo 链接：

1. 允许浏览器访问摄像头。
2. 在“当前输入”区域拍一张第一视角照片。
3. 输入问题，例如 `我刚才看到了什么？`。
4. 点击“提交问题”。
5. 查看模拟回答、OCR 文本、场景摘要和时间线记录。

如果手机摄像头权限不可用，可以使用备用的图片上传入口。

## 在线 Demo

👉 **[点此打开在线 Demo]()** ← *部署后填入 Streamlit Cloud 或 Render 的实际 URL*

Demo 使用模拟 OCR / 模拟 VLM，无需任何 API Key，上传图片即可体验视觉记忆闭环。

| 功能 | 说明 |
|------|------|
| 图片上传 + 提问 | 上传一张图片，输入问题（如"我刚才看到了什么？"） |
| 模拟回答与场景摘要 | 系统生成模拟 OCR 文本、VLM 回答和场景摘要 |
| 记忆时间线 | 自动保存每次交互记录，按时间倒序展示 |
| 历史检索 | 通过关键词搜索历史记忆事件 |

## API

启动 FastAPI 后可使用：

- `GET /health`
- `POST /ask`
- `GET /memories`
- `GET /memories/search?q=关键词`

## 项目结构

```text
app.py                                # Streamlit 云部署入口
render.yaml                           # Render 部署配置
requirements.txt                      # 云部署依赖入口
src/ai_glasses_memory/main.py         # FastAPI 应用
src/ai_glasses_memory/api/routes.py   # API 路由
src/ai_glasses_memory/ui/             # Streamlit UI
src/ai_glasses_memory/services/       # pipeline、mock AI、SQLite store
src/ai_glasses_memory/models/         # 数据模型
tests/                                # 自动化测试
docs/                                 # 架构、部署和学习文档
```

## 后续演进

- 手机摄像头：当前已支持拍照上传；后续再做抽帧和自动提交。
- 真实 OCR：PaddleOCR 或 EasyOCR。
- 真实 VLM：多模态模型。
- 向量检索：Chroma 或 FAISS。
- 语音输入：faster-whisper ASR。
- 硬件端：RK3588 + 摄像头采集、帧采样、图像压缩和 HTTP 上传。

最终定位不是“摄像头 + ChatGPT”，而是一个包含 Web 演示端、后端记忆服务、真实 AI 能力模块和硬件输入原型的视觉记忆系统。
