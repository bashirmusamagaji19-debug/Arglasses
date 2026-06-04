# Bug 07：真实 VLM 调用失败后静默回退到 mock

## 现象

启用 `AI_GLASSES_VLM_PROVIDER=openai_compatible` 后，页面提交问题时 `vlm` 延迟明显不是 0，例如约 2 秒：

```json
{
  "ocr": 0.01,
  "vlm": 2130.028,
  "summary": 0.033,
  "total": 2130.079
}
```

但是页面输出仍然是：

```text
模拟 VLM 回答：...
```

PowerShell 里也没有说明真实 VLM 为什么没有返回内容。

## 排查判断

这个现象说明 pipeline 确实进入了 VLM 阶段，而且大概率尝试过真实 API 请求。`vlm` 延迟约 2 秒，说明不是直接走 mock，而是请求失败后 fallback 到 mock。

根因不是“VLM 没接入”，而是：

```text
OpenAI-compatible VLM 请求失败
-> provider 捕获异常
-> 自动回退 MockVLMProvider
-> 没有把失败原因写到日志
-> 用户只能看到模拟回答，不知道真实请求哪里失败
```

可能的真实失败原因包括：

- API key 不正确或没有传到当前 Streamlit 进程。
- 账户余额不足。
- 模型名不可用。
- 服务商不接受当前 `image_url` / base64 data URL 格式。
- 请求超时或网络失败。

## 处理方式

在 `OpenAICompatibleVLMProvider.answer_question()` 中保留 fallback 机制，但增加安全日志：

```text
VLM provider fell back to mock: provider=openai_compatible model=... base_url=... error=...
```

日志不输出 API key，只输出模型名、base_url 和异常信息。

## 验证

先写测试验证 fallback 必须记录原因，并且不能泄露 API key。测试先失败：

```text
assert 'VLM provider fell back to mock' in ''
```

加日志后，聚焦测试通过：

```text
7 passed
4 passed
```

## 面试可讲点

这个问题体现了真实 AI 服务接入时的工程取舍：

- fallback 能保证 demo 不崩，但如果完全静默，会掩盖真实 API 失败原因。
- 日志需要提供足够诊断信息，但不能泄露 API key。
- 延迟统计可以帮助判断代码是否真的尝试过外部调用。
- 对外部模型服务，错误可观测性和保底策略同样重要。
