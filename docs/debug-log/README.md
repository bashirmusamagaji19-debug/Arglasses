# 调试日志

> 本项目部署到 Streamlit Community Cloud 过程中遇到的 Bug 及排查过程。
> 以第一人称视角记录，方便面试复盘。

## 目录

| # | Bug | 根因 | 文件 |
|---|-----|------|------|
| 1 | `ModuleNotFoundError: ai_glasses_memory.models` | `.gitignore` 的 `models/` 通配符误匹配了 `src/ai_glasses_memory/models/` | [bug-01-gitignore-models-glob.md](./bug-01-gitignore-models-glob.md) |
| 2 | `ModuleNotFoundError: ai_glasses_memory` | `pyproject.toml` 缺少 `[tool.setuptools.packages.find]`，src layout 包未注册 | [bug-02-missing-packages-find.md](./bug-02-missing-packages-find.md) |
| 3 | Streamlit Cloud 部署构建失败 | `requirements.txt` 用 `-e .` 不兼容；替换为显式依赖后漏了本地包安装 | [bug-03-requirements-txt-local-package.md](./bug-03-requirements-txt-local-package.md) |
| 4 | 点击“提交问题”后黑屏 | `app.py` 用 `import *` 转发 Streamlit UI，脚本上下文不稳定 | [bug-04-streamlit-entrypoint-black-screen.md](./bug-04-streamlit-entrypoint-black-screen.md) |
| 5 | PaddleOCR 安装后真实推理失败 | PaddleOCR 3.x API 和 Windows CPU PaddlePaddle 版本组合不匹配 | [bug-05-paddleocr-windows-cpu-version.md](./bug-05-paddleocr-windows-cpu-version.md) |
| 6 | Streamlit 图片宽度警告与 OCR 状态不透明 | `use_container_width` 即将废弃，且 PaddleOCR 首次冷启动缺少 UI 提示 | [bug-06-streamlit-width-warning-and-ocr-status.md](./bug-06-streamlit-width-warning-and-ocr-status.md) |
| 7 | 真实 VLM 调用失败后静默回退到 mock | fallback 保住了 demo，但没有记录真实 API 失败原因 | [bug-07-vlm-silent-fallback.md](./bug-07-vlm-silent-fallback.md) |
| 8 | Streamlit Cloud 缺少 `httpx` 运行依赖 | VLM provider 运行时导入 `httpx`，但依赖只放在 dev 依赖中 | [bug-08-cloud-missing-httpx-runtime-dependency.md](./bug-08-cloud-missing-httpx-runtime-dependency.md) |
| 9 | 硅基流动 VLM 请求断连 | 真实请求发出后服务端断连，优先压缩图片并降低视觉 detail | [bug-09-siliconflow-vlm-server-disconnected.md](./bug-09-siliconflow-vlm-server-disconnected.md) |
| 10 | 手机拍照上传原图过大 | 上传边界未压缩 4096x3072 原图，导致 OCR/VLM 下游被迫处理大图 | [bug-10-phone-photo-upload-too-large.md](./bug-10-phone-photo-upload-too-large.md) |
| 17 | 只有向量搜索展示还不能完整体现 RAG | 补齐 retrieval -> context -> generation 闭环，并把 Chroma 作为可选 provider | [bug-17-vector-search-is-not-full-rag.md](./bug-17-vector-search-is-not-full-rag.md) |
| 18 | Chroma 设为默认检索后端时出现依赖冲突 | Chroma 的 kubernetes 依赖和 PaddleX 的 PyYAML pin 冲突，固定兼容组合 | [bug-18-chroma-default-dependency-conflict.md](./bug-18-chroma-default-dependency-conflict.md) |
| 19 | RAG 回答像上下文拼接而不是自然问答 | 针对颜色追问抽取并合并关键信息，保留上下文列表作为证据 | [bug-19-rag-answer-context-dump.md](./bug-19-rag-answer-context-dump.md) |
| 20 | 文档和 demo 脚本落后于 RAG 实现 | 更新架构图、30 秒 demo 和 RAG smoke，让演示材料对齐当前代码能力 | [bug-20-docs-lagged-behind-rag-implementation.md](./bug-20-docs-lagged-behind-rag-implementation.md) |
| 21 | 工程包装材料落后于 RAG 实现 | 对齐检索/RAG 文档，补齐简历 bullet、面试问答和 2 分钟 demo 脚本 | [bug-21-engineering-packaging-gap.md](./bug-21-engineering-packaging-gap.md) |
