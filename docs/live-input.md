# 浏览器原生 Live 输入页

## 目标

`/live` 是当前更接近 AI 眼镜交互的输入页。它不再依赖 Streamlit 的拍照控件或音频上传控件，而是使用浏览器原生能力：

```text
getUserMedia 实时摄像头预览
-> canvas 截取当前视频帧
-> MediaRecorder 录音
-> ASR 转写问题
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
3. 点击“开始录音”和“停止录音并转写”，浏览器用 `MediaRecorder` 录制音频并提交到 `/live/transcribe`。
4. ASR 文本自动填入问题框。
5. 点击“截取当前画面并提问”，页面用 `<canvas>` 截取当前视频帧，并把图片和问题提交到 `/live/ask`。
6. 后端复用现有 `MemoryPipeline.ask()`，执行 OCR、VLM、摘要、记忆写入和检索索引更新。

## API

```text
GET /live
POST /live/ask
POST /live/transcribe
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

## 为什么不是直接 WebSocket 真流式

当前版本先做浏览器原生 live interaction，不做 WebSocket / WebRTC 级实时流式。原因：

- 当前主线是视觉记忆系统，不是实时音视频传输系统。
- faster-whisper 更适合音频片段转写，不是天然 token 流式 ASR。
- 真流式需要音频分片、session 管理、断句、增量 UI 和错误恢复。
- `/live` 已经把用户体验从“拍照/上传文件”推进到“实时预览 + 录音 + 当前帧提问”。

## 面试表述

> 我发现 Streamlit 的 camera/audio 控件更适合作为 demo 过渡，不适合作为 AI 眼镜最终输入形态。所以我新增了 `/live` 浏览器原生输入页，用 `getUserMedia` 做实时第一视角预览，用 canvas 在用户提问时截取当前帧，用 MediaRecorder 录音并转写。  
> 这一步没有改后端核心 pipeline，而是把输入体验从 Streamlit 控件迁移到 browser-native live input。后续如果继续做 WebSocket / WebRTC 流式，只需要替换 live 页的音视频传输层。
