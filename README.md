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
- 支持麦克风录音语音提问：录音后由 ASR provider 转写成问题文本，默认使用 faster-whisper，文件上传作为 fallback。
- 支持 Chroma RAG 历史记忆问答。

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
- Chroma
- pytest

## 本地运行

复制本地环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`。本地启动时项目会自动读取 `.env`，但 `.env` 已被 `.gitignore` 忽略，不要提交 API key。

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

也可以使用独立手机输入页。启动 FastAPI 后，手机打开 `http://电脑局域网IP:8000/mobile`，用原生浏览器拍照上传。详细说明见 [docs/mobile-input.md](docs/mobile-input.md)。

## PaddleOCR

阶段 3.1 已加入 PaddleOCR provider 开关。默认仍使用 mock OCR；本地安装 OCR 可选依赖后，可以切换到真实 OCR：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ocr]"
.\.venv\Scripts\python.exe -m pip install "numpy==1.26.4" "pillow==10.4.0" "protobuf==4.25.3" "httpx==0.27.0"
$env:AI_GLASSES_OCR_PROVIDER="paddleocr"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

详细说明见 [docs/phase3-paddleocr.md](docs/phase3-paddleocr.md)。

## ASR 语音提问

阶段 4 已加入非流式 ASR provider。默认使用 faster-whisper：

```text
AI_GLASSES_ASR_PROVIDER=faster_whisper
AI_GLASSES_ASR_MODEL=base
AI_GLASSES_ASR_DEVICE=cpu
AI_GLASSES_ASR_COMPUTE_TYPE=int8
```

安装 / 更新本地依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[asr]"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit 的“语音提问”区域支持麦克风录音，也保留 `.wav`、`.mp3`、`.m4a`、`.ogg` 文件上传作为 fallback。系统会先转写成问题文本，再由用户提交到视觉记忆 pipeline。faster-whisper 模型采用首次转写时懒加载，因此打开页面不会立即加载模型；第一次转写可能需要下载和加载模型。当前版本是“录音后分段转写”，暂不做 WebSocket token 级实时流式，详细说明见 [docs/phase4-asr.md](docs/phase4-asr.md)。

## 在线 Demo

👉 **[点此打开在线 Demo]()** ← *部署后填入 Streamlit Cloud 或 Render 的实际 URL*

Demo 使用模拟 OCR / 模拟 VLM，无需任何 API Key，上传图片即可体验视觉记忆闭环。

| 功能 | 说明 |
|------|------|
| 图片上传 + 提问 | 上传一张图片，输入问题（如"我刚才看到了什么？"） |
| 模拟回答与场景摘要 | 系统生成模拟 OCR 文本、VLM 回答和场景摘要 |
| 记忆时间线 | 自动保存每次交互记录，按时间倒序展示 |
| 历史检索 / RAG | 默认使用 Chroma 召回历史记忆，并支持基于历史记忆的问答 |
| 语音提问 | 麦克风录音后转写，默认 faster-whisper，也可切换到 mock ASR 做低依赖 fallback |

## API

启动 FastAPI 后可使用：

- `GET /health`
- `POST /ask`
- `POST /transcribe`
- `GET /memories`
- `GET /memories/search?q=关键词`
- `DELETE /memories/{memory_id}`
- `DELETE /memories`
- `POST /memories/prune?keep_latest=50`
- `POST /memories/dedupe`

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
- 检索：默认使用轻量语义检索；本地可切换到向量检索，后续可升级到 Chroma 或 FAISS。
- 语音输入：当前已支持麦克风录音后转写；后续再做 WebSocket / WebRTC 级实时流式 ASR。
- 硬件端：RK3588 + 摄像头采集、帧采样、图像压缩和 HTTP 上传。

当前场景摘要已从 mock 文案改为基于用户问题、VLM 回答和 OCR 文本整理的 rule-based 摘要，不会额外产生一次云端模型调用。
当前历史搜索已从纯关键词匹配升级为 provider 化检索：默认轻量语义检索，本地可切换到向量检索，说明见 [docs/phase3-search.md](docs/phase3-search.md) 和 [docs/vector-search.md](docs/vector-search.md)。
当前已加入记忆管理能力，包括单条删除、清空、保留最近 N 条和精确去重，说明见 [docs/memory-management.md](docs/memory-management.md)。

暂不打断主路线的优化项记录在 [docs/optimization-backlog.md](docs/optimization-backlog.md)，包括 OCR 识别速度优化，以及外文 OCR 结果翻译成中文。

真实 VLM 接入路线记录在 [docs/phase3-vlm-provider.md](docs/phase3-vlm-provider.md)。当前采用 OpenAI-compatible provider，默认 mock，可切换到第三方云端 API、租用 GPU 云服务器上的 vLLM，或后续本地 / 局域网模型服务。

最终定位不是“摄像头 + ChatGPT”，而是一个包含 Web 演示端、后端记忆服务、真实 AI 能力模块和硬件输入原型的视觉记忆系统。
