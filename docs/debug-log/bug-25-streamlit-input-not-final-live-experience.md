# Bug 25：Streamlit 输入控件不是最终实时交互形态

## 现象

项目已经支持 Streamlit 的 `st.camera_input` 和 `st.audio_input`，但这两个控件仍然更像 demo 过渡形态：

- 摄像头输入是拍照控件，不是持续第一视角预览。
- 语音输入是录音后转写，不支持和当前画面自然联动。
- 用户提问时不能明确表达“就用当前看到的这一帧”。

对于 AI 眼镜项目，最终输入体验应该更接近：

```text
实时第一视角画面
-> 用户语音 / 文本提问
-> 提问时截取当前帧
-> 进入视觉记忆 pipeline
```

## 根因

Streamlit 适合快速搭建 dashboard，但不适合承担最终的实时多模态输入体验。浏览器原生 API 更适合处理摄像头、麦克风和 canvas：

```text
getUserMedia
MediaRecorder
canvas.toBlob
fetch multipart/form-data
```

这类能力如果继续塞在 Streamlit 控件里，会限制交互表达，也不利于后续接 WebSocket、自动抽帧或硬件端输入。

## 修复

新增 FastAPI `/live` 页面：

```text
GET /live
-> getUserMedia 实时视频预览
-> MediaRecorder 录音
-> /live/transcribe 转写问题
-> canvas 截取当前视频帧
-> /live/ask 提交当前帧和问题
-> MemoryPipeline.ask
```

Streamlit 保留为 dashboard 和 fallback：

- 查看记忆时间线。
- 做历史检索和 RAG 问答。
- 展示调试信息和延迟。

## 面试复盘表达

> 我一开始用 Streamlit 的 camera/audio 控件快速跑通输入链路，但后来发现它不适合作为 AI 眼镜最终交互形态。  
> 所以后来我新增 `/live` 页面，用浏览器原生 `getUserMedia` 做实时第一视角预览，用 `MediaRecorder` 录音，用 canvas 在用户提问时截取当前帧。这样后端 pipeline 不需要重写，但输入体验更接近真实 AI 眼镜。

## 经验

- Streamlit 适合 dashboard，不一定适合最终输入体验。
- 输入层和业务 pipeline 解耦后，可以替换交互形态而不重写核心逻辑。
- 对 AI 眼镜项目来说，“当前帧 + 当前问题”的时序关系很重要。
