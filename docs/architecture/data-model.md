# Memory Event 数据模型

## 为什么需要 memory event

AI 眼镜记忆助手不是普通视觉问答 demo。普通 demo 只回答当前图片的问题，而本项目要让系统“记住”过去发生过的场景和交互。

因此需要一个最小数据单元来表示一次记忆，这就是 `memory event`。

## 当前字段

- `id`：数据库自增主键。
- `created_at`：记忆创建时间，用于时间线展示。
- `question`：用户当时问了什么。
- `answer`：系统当时回答了什么。
- `scene_summary`：系统对当前场景的摘要。
- `ocr_text`：从画面里识别出的文字。
- `image_path`：图片保存路径，第一周可以为空。
- `latency_ms`：本次交互的耗时统计。

## 为什么这样设计

`question` 和 `answer` 记录了用户意图和系统反馈。`scene_summary` 让系统即使不保存完整图片，也能保留可检索的场景语义。`ocr_text` 对 AI 眼镜场景很重要，因为路牌、菜单、屏幕和 PPT 都依赖文字理解。`created_at` 支持“刚才”“昨天”“上一次”这类时间线问题。

## 后续如何扩展到向量检索

后续可以把下面内容拼成 embedding 文本：

```text
用户问题 + 系统回答 + 场景摘要 + OCR 文本
```

然后写入 Chroma 或 FAISS。SQLite 继续保存结构化数据，向量库负责语义检索，两者通过 `memory_event.id` 关联。

