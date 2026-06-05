# Bug 15：误以为已经启用真实向量检索

## 现象

用户反馈历史检索效果仍然很差，并贴出了后台日志：

```text
Creating model: ('PP-OCRv5_server_det', None, None)
Creating model: ('PP-OCRv5_server_rec', None, None)
```

这些日志来自 PaddleOCR 初始化，不是历史检索模块。

## 排查过程

1. 检查 `.env` 中搜索相关配置，发现没有设置：

```text
AI_GLASSES_SEARCH_PROVIDER
AI_GLASSES_EMBEDDING_PROVIDER
```

2. 读取 `get_settings()`，实际配置是：

```text
search_provider=lightweight
embedding_provider=hash
```

3. 检查本地依赖，发现 `sentence-transformers`、`torch`、`transformers` 还没有安装。
4. 运行 hash embedding smoke，发现它只能验证架构，不能稳定提供真实语义排序。
5. 安装 `.[embedding]` 后，成功加载 `BAAI/bge-small-zh-v1.5`，向量维度 512，归一化正常。
6. 使用真实 embedding smoke：

```text
无线鼠标 -> 鼠标在哪里
喝水的杯子 -> 水杯在哪里
```

结果符合预期。

## 根因

这是配置和期望不一致：

- 默认仍是 `lightweight`，不是 `vector`。
- `hash embedding` 只是测试/架构验证 fallback，不是真正语义模型。
- UI 原本没有清楚显示当前 search provider 和 embedding provider，容易误以为已经启用真实向量检索。

## 修复

1. Streamlit UI 增加：

```text
当前检索模式
当前 Embedding 模式
```

2. 如果使用 `vector + hash`，页面提示：

```text
Hash embedding 只用于验证向量检索架构，不是真正语义模型
```

3. 本地 `.env` 切换到：

```text
AI_GLASSES_SEARCH_PROVIDER=vector
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
AI_GLASSES_EMBEDDING_DIMENSIONS=512
```

4. 增加 `scripts/vector_search_smoke.py`，用于验证真实 embedding 检索效果。

## 面试复盘说法

> 我第一次实现向量检索时先用 hash embedding 验证架构，但真实测试发现检索效果仍然不理想。排查后发现系统实际还在 lightweight 模式，而且 hash embedding 本身不是语义模型。  
> 后续我把 UI 加上当前 search/embedding provider 状态，避免配置误判；并安装 sentence-transformers，切换到 bge-small-zh-v1.5 做中文语义 embedding。这样把“架构验证”和“效果验证”分开，问题定位更清楚。
