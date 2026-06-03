# Phase 2：手机摄像头模拟眼镜第一视角

## 目标

在 Phase 1 Web MVP 的基础上，把输入方式从“普通图片上传”升级为“手机浏览器摄像头拍照”。这样演示时可以用手机打开线上 demo，直接拍当前环境，模拟 AI 眼镜第一视角输入。

## 当前实现

数据流：

```text
手机浏览器摄像头
-> st.camera_input 拍照
-> 保存到 data/uploads
-> MemoryPipeline.ask(question, image_path)
-> 模拟 OCR / 模拟 VLM
-> SQLite 记忆写入
-> Streamlit 时间线展示
```

## 设计取舍

本阶段不做实时视频流、不做自动抽帧、不做 WebRTC。原因是阶段 2 的目标是让作品形态更接近 AI 眼镜第一视角，而不是先解决视频流工程复杂度。

当前选择 `st.camera_input`：

- 优点：无需新增依赖，手机浏览器可直接调用摄像头。
- 优点：返回对象和 `st.file_uploader` 类似，可以复用保存逻辑。
- 缺点：是拍照输入，不是连续视频流。

保留 `st.file_uploader` 作为备用入口，避免手机摄像头权限或浏览器兼容问题影响演示。

## 修改点

| 文件 | 作用 |
|------|------|
| `src/ai_glasses_memory/ui/streamlit_app.py` | 新增 `st.camera_input`，提交时优先使用摄像头图片 |
| `src/ai_glasses_memory/services/uploads.py` | 抽出图片保存 helper，兼容拍照和上传 |
| `tests/test_uploads.py` | 验证图片保存逻辑 |
| `tests/test_deployment.py` | 验证 UI 暴露摄像头和上传入口 |

## 演示脚本

1. 手机打开线上 demo。
2. 允许浏览器摄像头权限。
3. 对准桌面、屏幕或学习资料拍照。
4. 输入：`我刚才看到了什么？`
5. 点击“提交问题”。
6. 展示模拟 OCR、模拟 VLM 回答、场景摘要。
7. 向下滚动查看时间线新增记录。
8. 搜索 `模拟` 或 `AI 眼镜`，展示历史检索。

## 后续扩展

Phase 2 完成后，如果还要增强第一视角体验，可以继续做：

- 自动提交最近一次拍照。
- 定时抽帧上传。
- 手机端轻量页面或 FastAPI 上传接口。
- 再进入 Phase 3，用真实 OCR / VLM 替换模拟模块。
