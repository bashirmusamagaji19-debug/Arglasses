# Bug 26：Qwen-ASR-Realtime 不能让前端直接连阿里云

## 现象

用户希望直接接入 Qwen-ASR-Realtime，替代 Hugging Face / 本地 faster-whisper 下载模型的路径。最直接的想法是让浏览器从 `/live` 页面直接连接 DashScope WebSocket。

但这样会暴露 `DASHSCOPE_API_KEY`，因为浏览器 WebSocket 请求头和脚本都可以被用户看到。

## 根因

实时 ASR 的数据流涉及两个连接：

```text
浏览器麦克风
-> 本地后端
-> 阿里云 DashScope Qwen-ASR-Realtime
```

API Key 必须只存在于后端环境变量中。如果前端直接连接阿里云，就需要把 key 放到 JS 里，安全上不可接受。

## 修复

新增后端 WebSocket 代理：

```text
/live/asr/ws
-> 读取 DASHSCOPE_API_KEY
-> 连接 wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-asr-flash-realtime
-> 转发浏览器音频 chunk
-> 转发识别文本回浏览器
```

同时保留：

- `/live/transcribe`：录音后 faster-whisper fallback。
- `faster_whisper` provider：本地 ASR fallback。
- `/live/ask`：当前帧 + 问题进入视觉记忆 pipeline。

## 面试复盘表达

> 接 Qwen-ASR-Realtime 时，我没有让前端直接连阿里云，而是做了后端 WebSocket 代理。前端只连接 `/live/asr/ws`，DashScope API Key 只在后端 `.env` 中读取。这样既能做实时 ASR，又不会把密钥暴露在浏览器里。

## 经验

- 云端实时 API 的密钥必须后端代理，不能写进前端。
- 实时 ASR 是传输层能力，不应该重写视觉记忆 pipeline。
- 保留本地 ASR fallback 可以避免云服务不可用时 demo 完全失效。
