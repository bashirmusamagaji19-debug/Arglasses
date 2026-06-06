# 浏览器原生 Live 输入页

## 目标

`/live` 是当前更接近 AI 眼镜交互的输入页。它不再依赖 Streamlit 的拍照控件或音频上传控件，而是使用浏览器原生能力：

```text
getUserMedia 实时摄像头预览
-> canvas 截取当前视频帧
-> MediaRecorder 录音
-> Qwen-ASR-Realtime 或 faster-whisper 转写问题
-> 当前帧 + 问题文本提交到 MemoryPipeline
```

Streamlit 继续适合作为 dashboard：查看时间线、RAG 检索、调试延迟和管理记忆。真正的第一视角输入优先使用 `/live`。

## 启动方式

启动 FastAPI：

```powershell
.\.venv\Scripts\python.exe -m uvicorn ai_glasses_memory.main:app --host 0.0.0.0 --port 8000 --reload
```

电脑本机打开：

```text
http://127.0.0.1:8000/live
```

手机和电脑在同一 Wi-Fi 时，手机打开：

```text
http://电脑局域网IP:8000/live
```

浏览器需要允许摄像头和麦克风权限。

## 页面行为

1. 页面打开后请求摄像头和麦克风权限。
2. `<video>` 实时显示第一视角画面。
3. 点击“开始实时识别”时，浏览器通过 WebSocket 连接 `/live/asr/ws`，后端代理到 Qwen-ASR-Realtime。
4. 也可以点击“开始录音”和“停止录音并转写”，浏览器用 `MediaRecorder` 录制音频并提交到 `/live/transcribe` 作为 fallback。
5. ASR 文本自动填入问题框。
6. 点击“截取当前画面并提问”，页面用 `<canvas>` 截取当前视频帧，并把图片和问题提交到 `/live/ask`。
7. 后端复用现有 `MemoryPipeline.ask()`，执行 OCR、VLM、摘要、记忆写入和检索索引更新。

## API

```text
GET /live
POST /live/ask
POST /live/transcribe
WS /live/asr/ws
```

`POST /live/ask` 使用 multipart/form-data：

```text
question: 文本问题
image: 当前视频帧 JPEG
```

`POST /live/transcribe` 使用 multipart/form-data：

```text
audio: 浏览器录音 webm
```

`WS /live/asr/ws` 是后端代理通道：

```text
浏览器麦克风音频 chunk
-> /live/asr/ws
-> DashScope Qwen-ASR-Realtime
-> 转写文本返回浏览器
```

DashScope API Key 只放在后端环境变量：

```text
DASHSCOPE_API_KEY=...
```

## 为什么不是直接 WebSocket 真流式

当前版本已经新增 `/live/asr/ws` 作为 Qwen-ASR-Realtime 后端代理。仍然没有直接把 DashScope API Key 放在前端，也没有把整个视频流上传到云端。后续如果要继续优化，需要重点处理：

- 音频编码格式和 DashScope 支持格式的严格匹配。
- 中间结果和最终结果的 UI 合并策略。
- 网络断开后的重连和状态恢复。
- 长时间识别的 session 生命周期。

## 面试表述

> 我发现 Streamlit 的 camera/audio 控件更适合作为 demo 过渡，不适合作为 AI 眼镜最终输入形态。所以我新增了 `/live` 浏览器原生输入页，用 `getUserMedia` 做实时第一视角预览，用 canvas 在用户提问时截取当前帧。  
> 语音侧进一步增加了 `/live/asr/ws`，由后端代理到阿里云 Qwen-ASR-Realtime，避免前端暴露 API Key。这样输入体验更接近真实 AI 眼镜，同时后端视觉记忆 pipeline 不需要重写。
