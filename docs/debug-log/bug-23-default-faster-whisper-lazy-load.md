# Bug 23：默认 faster-whisper 后启动阶段不能直接加载模型

## 现象

将 ASR 默认 provider 从 `mock` 改成 `faster_whisper` 后，如果 provider 在初始化时就导入并加载 Whisper 模型，Streamlit 页面打开时可能出现明显卡顿，甚至在依赖未安装或模型首次下载时直接失败。

这和用户期望不一致：默认使用真实 ASR 是为了让 demo 更接近真实项目，但不应该让“打开页面”这一步就承担模型下载和冷启动成本。

## 根因

真实 ASR 模型有两个成本：

```text
应用启动
-> 创建 provider
-> 导入 faster-whisper
-> 加载 / 下载 Whisper 模型
-> 页面可用
```

如果把模型加载放在 provider 构造函数里，启动阶段会被 ASR 阻塞。实际上只有用户点击“转写语音”时才需要模型。

## 修复

将 `FasterWhisperASRProvider` 改为懒加载：

```text
应用启动
-> 创建 FasterWhisperASRProvider
-> model = None
-> 页面可用

用户点击“转写语音”
-> _get_model()
-> 导入 faster-whisper
-> 加载模型
-> transcribe(audio_path)
```

同时做了配套调整：

- `AI_GLASSES_ASR_PROVIDER` 默认改为 `faster_whisper`。
- `requirements.txt` 加入 `faster-whisper>=1.1.0`，因为它已经是默认运行能力。
- `.env.example` 和文档同步默认值。
- 保留 `mock` provider 作为低依赖 fallback。

## 面试复盘表达

> 我把 ASR 默认切到 faster-whisper 后，没有把模型加载放在应用启动阶段，而是做了懒加载。这样页面启动只创建 provider，不下载或加载模型；只有用户真正上传音频并点击转写时才触发模型加载。  
> 这个取舍可以降低 demo 首屏失败概率，同时仍然体现默认真实 ASR 能力。

## 经验

- 当一个真实模型成为默认 provider 后，它也必须进入运行依赖。
- 重模型默认启用时要特别关注冷启动边界。
- “provider 默认真实”不等于“应用启动时立即加载真实模型”。
