# Bug 06：Streamlit 图片宽度警告与 OCR 状态不透明

## 现象

本地使用 PaddleOCR 模式启动 Streamlit：

```powershell
$env:AI_GLASSES_OCR_PROVIDER="paddleocr"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

页面可以打开，提交问题后也能识别出图片文字，但终端出现 Streamlit 警告：

```text
Please replace `use_container_width` with `width`.
`use_container_width` will be removed after 2025-12-31.
```

同时 PaddleOCR 首次识别耗时约 24 秒，页面本身没有说明当前使用的是 mock OCR 还是真实 PaddleOCR，演示时容易误以为系统卡住。

## 排查判断

这个问题不是功能崩溃：

- OCR 已经返回了 `PaddleOCR：你好`
- VLM、摘要、SQLite 写入和时间线展示都能继续工作
- 主要风险是演示体验差，以及未来 Streamlit 版本升级后参数被移除

PaddleOCR 首次慢的原因主要是模型初始化、加载和 CPU 推理启动成本。后续请求通常会比首次快。

## 处理方式

1. 将 `st.image(..., use_container_width=True)` 替换为 `st.image(..., width="stretch")`，消除 Streamlit 弃用警告。
2. 在 Streamlit 页面顶部展示当前 OCR 模式，例如 `当前 OCR 模式：paddleocr`。
3. 当 OCR provider 是 `paddleocr` 时，显示提示：首次识别会加载模型，可能需要 10-30 秒。
4. 添加回归测试，确保 UI 中保留 OCR 模式提示，并且不再出现 `use_container_width`。

## 验证

新增测试先失败，证明 UI 还没有这些能力：

```text
FAILED test_streamlit_ui_reports_ocr_provider_and_uses_supported_image_width
assert '当前 OCR 模式' in contents
```

修改后聚焦测试通过：

```text
6 passed in 0.02s
```

## 面试可讲点

这个问题体现了上线演示前的工程处理：

- 不是所有日志都代表功能失败，需要先判断是否影响主链路。
- PaddleOCR 首次慢属于模型冷启动问题，应该通过 UI 状态提示降低用户误解。
- Streamlit 的弃用警告虽然当前不阻塞，但会影响后续维护，所以提前替换为新参数。
- 用测试锁住演示关键文案和 API 参数，避免之后改 UI 时把提示删掉。
