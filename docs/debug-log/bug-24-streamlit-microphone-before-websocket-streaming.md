# Bug 24：先用 Streamlit 麦克风录音，不直接上 WebSocket 流式 ASR

## 现象

用户希望把 ASR 进一步改成“流式的麦克风交互识别”。直觉方案是直接做 WebSocket 或 WebRTC，把浏览器麦克风音频分片传到后端，再边识别边更新文本。

但当前项目的主 UI 是 Streamlit，而本地版本 `1.58.0` 已经提供 `st.audio_input`。这意味着我们可以先让用户直接用浏览器麦克风录音，再调用当前的 faster-whisper ASR provider 转写，快速提升交互体验。

## 根因

WebSocket / WebRTC 级实时流式 ASR 不只是一个 UI 控件，它会引入新的工程边界：

```text
浏览器录音
-> 音频分片
-> WebSocket session
-> 后端缓冲和断句
-> ASR 分段推理
-> 增量文本状态
-> UI 实时刷新
```

同时，faster-whisper 更适合对音频片段做批式转写，不是天然的 token-by-token 实时 ASR 引擎。直接上实时流会让项目从“AI 眼镜视觉记忆系统”偏向“实时音频工程”。

## 修复

当前版本采用 Streamlit 麦克风录音优先、文件上传 fallback：

```text
st.audio_input 麦克风录音
或 st.file_uploader 上传音频
-> save_input_audio
-> MemoryPipeline.transcribe_audio
-> FasterWhisperASRProvider
-> 问题文本
```

这样用户已经可以用麦克风提问，同时保留后续升级路径。

## 面试复盘表达

> 我在做语音交互时没有直接上 WebSocket 实时流，而是先利用 Streamlit 1.58 的 `audio_input` 做麦克风录音。原因是 faster-whisper 更适合片段转写，而真正流式 ASR 会牵涉音频分片、session、断句和增量 UI。  
> 这个版本先把用户体验从“上传音频文件”推进到“浏览器麦克风提问”，同时保持 ASR provider 和视觉记忆 pipeline 不变，后续可以在这个边界上继续升级 WebSocket / WebRTC。

## 经验

- “麦克风交互”可以先用录音后转写实现，不必一开始就做 token 流式。
- 使用已有框架原生能力可以减少不必要的前端音频工程。
- 对作品集项目，要优先推进能稳定演示、能清楚讲解的版本。
