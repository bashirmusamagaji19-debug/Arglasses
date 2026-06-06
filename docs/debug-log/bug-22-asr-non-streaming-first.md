# Bug 22：ASR 如果一开始做实时流会打断主线

## 现象

原始设计里阶段 4 是语音交互，也就是让 AI 眼镜系统具备“听见”的能力。直接想到的方案是实时麦克风输入和流式 ASR，但这样会立刻引入很多额外问题：

- 浏览器麦克风权限。
- WebRTC 或前端录音组件。
- 流式转写的分段、断句和状态刷新。
- 长连接和部署兼容性。
- ASR 模型冷启动和实时延迟。

如果在当前阶段直接做实时流，很容易把时间消耗在前端音频工程上，而不是验证 AI 眼镜记忆系统的主链路。

## 根因

语音交互不是单一功能，而是多个子系统的组合：

```text
音频采集
-> 音频编码
-> ASR 推理
-> 增量文本状态
-> 用户确认
-> 视觉问答 pipeline
```

当前项目更需要先证明 ASR provider 可以接入系统边界，而不是一次性实现完整实时语音产品。

## 修复

第一版采用非流式音频上传：

```text
上传音频文件
-> save_input_audio
-> MemoryPipeline.transcribe_audio
-> ASRProvider
-> 返回文本和 asr latency
-> 用户提交视觉问题
```

同时保留 provider 边界：

- 默认 `MockASRProvider`，保证 demo 不依赖重模型。
- 可选 `FasterWhisperASRProvider`，本地安装 `.[asr]` 后启用。
- Streamlit 只新增音频上传和转写按钮。
- FastAPI 新增 `/transcribe` endpoint。

## 面试复盘表达

> 我在接 ASR 时没有直接做实时语音流，而是先做音频上传版。因为实时流会牵涉 WebRTC、浏览器权限、增量转写和长连接部署，容易让项目偏离“视觉记忆系统”主线。  
> 第一版我先抽象 ASR provider，默认 mock，本地可切换 faster-whisper。这样项目已经具备“语音问题 -> 文本问题 -> 视觉记忆 pipeline”的能力，同时保留后续升级到实时 ASR 的清晰路径。

## 经验

- 对 AI 眼镜项目来说，先补齐系统链路比先追求实时体验更重要。
- 重模型能力应该 provider 化，并保持 mock fallback。
- 每个新模态都要先想清楚它和 memory event、latency、UI 状态的关系。
