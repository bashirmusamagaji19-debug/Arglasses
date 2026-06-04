# Phase 3.2：OpenAI-compatible VLM Provider

## 目标

把当前的模拟 VLM 回答替换为可选的真实多模态模型调用，同时保持默认 demo 不依赖 API key、不产生费用、不因为模型服务不可用而崩溃。

当前阶段的设计重点不是绑定某一家模型厂商，而是建立一个可切换的 VLM provider：

```text
mock VLM
第三方云端 VLM API
租用 GPU 云服务器上的 vLLM
后续本地 / 局域网 VLM 服务
```

这些来源都通过 OpenAI-compatible API 形态接入。

## 数据流

```text
手机拍照 / 图片上传
-> 保存图片
-> OCR provider 提取文字
-> VLM provider 结合图片、OCR 文本和用户问题生成回答
-> 场景摘要
-> SQLite 记忆写入
-> Streamlit 时间线展示
```

## 配置

默认仍使用 mock，不产生费用：

```text
AI_GLASSES_VLM_PROVIDER=mock
```

启用 OpenAI-compatible VLM：

```powershell
$env:AI_GLASSES_VLM_PROVIDER="openai_compatible"
$env:AI_GLASSES_VLM_BASE_URL="https://your-provider.example/v1"
$env:AI_GLASSES_VLM_API_KEY="your-api-key"
$env:AI_GLASSES_VLM_MODEL="your-vlm-model"
$env:AI_GLASSES_VLM_MAX_TOKENS="512"
$env:AI_GLASSES_VLM_TIMEOUT_SECONDS="30"
```

`BASE_URL` 可以指向：

- 第三方云端 API。
- 自己租的 GPU 云服务器上的 vLLM。
- 后续局域网里的本地 GPU 服务。

## 成本控制

真实 VLM 每次提交都会产生一次模型调用。当前阶段只在用户点击“提交问题”时调用一次 VLM，不做自动抽帧调用。

当前成本控制策略：

- 默认 provider 是 `mock`。
- 没有完整配置 `base_url`、`api_key`、`model` 时自动使用 mock。
- 真实 VLM 请求失败时回退 mock，避免 demo 崩溃。
- 通过 `AI_GLASSES_VLM_MAX_TOKENS` 限制输出长度。
- UI 顶部显示当前 VLM 模式，并在真实 VLM 模式下提示调用成本。

后续如果做自动抽帧，需要再增加：

- 每分钟最大调用次数。
- 每日预算上限。
- 图片尺寸压缩。
- 相似帧跳过。
- 手动确认后再调用真实 VLM。

## 开源与本地部署

当前代码不绑定 OpenAI、DashScope、SiliconFlow 或某一个本地模型。只要服务兼容 `/chat/completions`，并支持 vision `image_url` 输入，就可以接入。

后续本地部署路线：

```text
Qwen-VL / 其他开源 VLM
-> vLLM 或其他 OpenAI-compatible server
-> AI_GLASSES_VLM_BASE_URL 指向本地或云服务器
-> 项目代码不改，只换环境变量
```

消费级 8GB 显存机器适合先实验小尺寸或量化 VLM；如果要跑更大的 Qwen-VL，可以租用更强 GPU 云服务器。

## 端云协同思路

后续接 RK3588 + 摄像头时，不建议把所有能力都放在端侧。推荐分工：

| 模块 | RK3588 / 端侧 | 云端 API / 云 GPU |
|---|---|---|
| 摄像头采集 | 是 | 否 |
| 帧采样 | 是 | 否 |
| 图片压缩 | 是 | 否 |
| 简单模糊过滤 | 是 | 否 |
| 隐私敏感过滤 | 优先端侧 | 可选 |
| OCR | 可端侧 | 可云端 |
| VLM | 小模型实验 | 主力模型 |
| 向量检索 | 小库可端侧 | 大库可云端 |
| 记忆数据库 | 当前本地 SQLite | 后续可云端数据库 |

面试表达可以写：

> 我把 VLM 设计成 OpenAI-compatible provider，而不是写死某个 API。这样模型来源可以在第三方云端 API、自部署 vLLM、局域网 GPU 服务之间切换。端侧 RK3588 负责采集、帧采样、图像压缩和隐私过滤，云端或 GPU 服务负责重型多模态理解。

## 当前限制

- 尚未做图片压缩，真实 VLM 成本和延迟会受图片大小影响。
- 尚未做调用预算控制，只通过“点击一次提交，调用一次”降低风险。
- 尚未接真实云端 API key 测试，当前自动化测试只验证请求体、provider 选择和 fallback。
