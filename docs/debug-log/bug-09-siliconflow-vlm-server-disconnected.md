# Bug 09：硅基流动 VLM 请求断连

## 现象

启用硅基流动 Qwen3-VL 后，VLM provider 进入真实调用，但随后回退到 mock：

```text
VLM provider fell back to mock:
provider=openai_compatible
model=Qwen/Qwen3-VL-8B-Instruct
base_url=https://api.siliconflow.com/v1
error=Server disconnected without sending a response.
```

## 排查判断

这条日志说明：

- API key、base_url、model 至少已经进入当前 Streamlit 进程。
- provider 确实向硅基流动发起了请求。
- 服务端没有返回普通 4xx/5xx JSON 错误，而是直接断开连接。

常见原因包括：

- 图片 base64 payload 太大。
- 图片格式或尺寸导致服务端预处理失败。
- 服务商对视觉 payload 有额外限制。
- 网络连接在服务端处理期间被中断。

当前项目的第一反应不应该是关闭 fallback，而是增强请求前处理和日志可观测性。

## 处理方式

1. VLM 请求前把图片压缩成 JPEG。
2. 默认最大图片宽度限制为 `1024`。
3. `image_url` 增加 `detail: low`，降低服务端视觉处理成本。
4. 增加 `AI_GLASSES_VLM_MAX_IMAGE_WIDTH` 配置项。
5. 记录发送给 VLM 前的图片 payload 字节数、最大宽度和 detail。

## 验证

新增测试覆盖：

- VLM payload 带 `image_url.detail = low`。
- 大图会被压缩为 `data:image/jpeg;base64,...`。
- `.env.example` 文档包含 `AI_GLASSES_VLM_MAX_IMAGE_WIDTH=1024`。

聚焦测试通过：

```text
8 passed
1 passed
```

## 面试可讲点

这个问题体现了多模态 API 接入时的实际工程问题：

- 图片请求不是普通文本请求，payload 大小和图片预处理会影响云端稳定性。
- VLM 请求失败不能只看模型名和 API key，也要看图片尺寸、格式、base64 后体积。
- 端云协同场景下，端侧或后端应先做图像压缩和采样，再调用重模型。
- 保留 fallback 可以保护 demo，但必须配合日志，否则无法定位真实模型失败原因。
