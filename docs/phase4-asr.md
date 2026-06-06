# Phase 4：ASR 语音提问

## 目标

AI 眼镜系统不应该只有文字输入。阶段 4 的目标是补上“听见”这一环，让用户可以通过语音提出问题：

```text
语音问题
-> ASR provider 转写成文本
-> 用户确认 / 编辑问题
-> 视觉问答 pipeline
-> 记忆写入和 RAG 检索
```

第一版先做非流式音频上传，不做实时麦克风流和 WebRTC。

## 当前实现

新增 `ASRProvider` 边界：

```text
ASRProvider
├── FasterWhisperASRProvider
└── MockASRProvider
```

默认配置：

```text
AI_GLASSES_ASR_PROVIDER=faster_whisper
AI_GLASSES_ASR_MODEL=base
AI_GLASSES_ASR_DEVICE=cpu
AI_GLASSES_ASR_COMPUTE_TYPE=int8
```

Streamlit UI 新增“语音提问”区域：

1. 上传 `.wav`、`.mp3`、`.m4a` 或 `.ogg` 音频。
2. 点击“转写语音”。
3. 系统调用 `MemoryPipeline.transcribe_audio()`。
4. 转写结果填入问题输入框。
5. 用户再点击“提交问题”，进入原视觉记忆 pipeline。

FastAPI 新增接口：

```text
POST /transcribe
```

请求使用 multipart/form-data 上传音频文件，返回：

```text
text
audio_path
latency_ms
```

## 为什么先做非流式 ASR

实时语音输入会引入更多复杂度：

- 浏览器麦克风权限。
- WebRTC 或前端录音组件。
- 流式 ASR 分段、断句和增量刷新。
- 延迟和交互状态管理。
- 云端部署对音频设备和长连接的限制。

当前项目的主目标是先补齐 AI 眼镜系统链路中的“听见”能力，而不是马上做生产级实时语音交互。音频上传版已经能验证 ASR provider、配置、延迟统计和 UI 问题文本 handoff。

## faster-whisper 默认模式

当前默认 ASR provider 是 `faster_whisper`。本地安装 / 更新依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[asr]"
```

默认配置如下：

```powershell
$env:AI_GLASSES_ASR_PROVIDER="faster_whisper"
$env:AI_GLASSES_ASR_MODEL="base"
$env:AI_GLASSES_ASR_DEVICE="cpu"
$env:AI_GLASSES_ASR_COMPUTE_TYPE="int8"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

CPU 上建议先用 `base` 或更小模型，并用短音频验证延迟。

如果需要低依赖 fallback，可以临时切回 mock：

```powershell
$env:AI_GLASSES_ASR_PROVIDER="mock"
```

`FasterWhisperASRProvider` 采用懒加载：应用启动时只创建 provider，不立即加载模型；第一次点击“转写语音”时才导入 faster-whisper 并加载模型。

## 和视觉记忆 pipeline 的关系

ASR 只负责把语音变成问题文本，不直接写入 memory event。原因是：

- 用户可能需要编辑转写结果。
- 视觉记忆仍然以“用户问题 + 当前画面”为核心。
- ASR latency 可以单独展示，避免和 OCR/VLM 延迟混在一起。

提交问题后，原 pipeline 继续执行：

```text
问题文本 + 图片
-> OCR
-> VLM
-> Summary
-> SQLite memory event
-> Chroma index
```

## 后续扩展

- 浏览器录音按钮。
- 麦克风实时转写。
- 流式 ASR 分段结果。
- 端侧 RK3588 采集音频并上传。
- 把 ASR 文本、置信度和语言信息写入 memory event 扩展字段。

## 面试表述

> 我没有一开始做实时语音流，而是先做非流式 ASR provider。这样可以先验证“语音问题 -> 文本问题 -> 视觉记忆 pipeline”的系统边界，同时避免 WebRTC、浏览器麦克风权限和流式 ASR 状态管理把主线复杂化。  
> 当前默认使用 faster-whisper，mock 作为 fallback。为了避免打开 demo 时就加载模型，我把 faster-whisper provider 做成懒加载，第一次真正转写音频时才加载模型。
