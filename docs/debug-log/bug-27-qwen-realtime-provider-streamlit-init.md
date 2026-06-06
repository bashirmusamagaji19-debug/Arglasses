# Bug 27：qwen_realtime provider 让 Streamlit 初始化崩溃

## 现象

`.env` 中设置：

```text
AI_GLASSES_ASR_PROVIDER=qwen_realtime
```

后，Streamlit 启动时在 `create_pipeline()` 阶段报：

```text
ValueError: Unsupported ASR provider: qwen_realtime
```

## 根因

上一轮只新增了 `/live/asr/ws` 后端 WebSocket 代理，但 `create_asr_provider()` 仍然只认识：

```text
mock
faster_whisper
```

Streamlit 启动时会统一创建 `MemoryPipeline`，而 `MemoryPipeline` 会通过 factory 创建 ASR provider。因此 `.env` 切到 `qwen_realtime` 后，虽然实时 ASR 逻辑在 `/live/asr/ws` 中，但 Streamlit 初始化仍会走 provider factory 并崩溃。

## 修复

新增 `QwenRealtimeASRProvider` 作为兼容 provider：

```text
create_asr_provider("qwen_realtime")
-> QwenRealtimeASRProvider
```

它不负责单文件转写；如果调用 `transcribe()`，会明确提示：

```text
Use the /live/asr/ws WebSocket route.
```

同时 Streamlit UI 在 `qwen_realtime` 模式下提示用户去 `/live` 页面使用实时识别，并禁用 Streamlit 的“转写语音”按钮。

## 面试复盘表达

> 接 Qwen-ASR-Realtime 时，我一开始只做了 `/live/asr/ws`，但忘了 Streamlit 启动时仍会创建 ASR provider。于是 `.env` 切到 `qwen_realtime` 后，factory 不认识这个 provider，导致 UI 启动失败。  
> 修复方式不是把 Qwen 实时识别塞进单文件转写接口，而是加一个兼容 provider，明确它是 streaming-only，并在 Streamlit 中提示实时识别应该走 `/live/asr/ws`。

## 经验

- 新 provider 名称必须在所有 factory 边界注册。
- Streaming provider 和 batch provider 的能力边界要明确。
- `.env` 默认值变化要同时验证 API、Streamlit 和测试环境。
