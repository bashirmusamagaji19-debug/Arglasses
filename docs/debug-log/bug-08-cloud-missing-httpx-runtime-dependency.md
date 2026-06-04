# Bug 08：Streamlit Cloud 缺少 httpx 运行依赖

## 现象

Streamlit Cloud 部署后页面报 `ModuleNotFoundError`，回溯显示：

```text
File "/mount/src/arglasses/src/ai_glasses_memory/services/vlm.py", line 9, in <module>
    import httpx
```

本地测试通过，但云端启动失败。

## 排查判断

`httpx` 是 VLM provider 的运行时依赖，因为 `OpenAICompatibleVLMProvider` 用它调用 `/chat/completions`。

问题在于：

```text
pyproject.toml 的 dev 依赖里有 httpx
requirements.txt 和 project dependencies 里没有 httpx
Streamlit Cloud 只安装运行依赖
-> 云端 import ai_glasses_memory.services.vlm 时找不到 httpx
```

所以根因不是 Streamlit Cloud 本身，而是把运行时要用的库错误地放在了 dev-only 依赖中。

## 处理方式

1. 在 `pyproject.toml` 的 `[project].dependencies` 中加入：

```text
httpx>=0.27.0
```

2. 在 `requirements.txt` 中加入：

```text
httpx>=0.27.0
```

3. 从 dev 依赖中移除重复的 `httpx`，避免依赖职责混乱。
4. 添加部署测试，确保云部署依赖中包含 `httpx`。

## 验证

先写测试验证云部署依赖必须包含 `httpx`，测试先失败：

```text
assert 'httpx' in requirements.txt
```

修复后再运行完整测试。

## 面试可讲点

这个问题体现了部署依赖和开发依赖的区别：

- 本地测试能通过，不代表云端运行依赖完整。
- 如果一个库在 production import path 上被导入，就必须进入运行依赖，而不是 dev 依赖。
- VLM provider 即使默认 mock，也会在模块加载时 import `httpx`，所以 Cloud 启动阶段就会失败。
- 部署问题要用自动化测试锁住，避免之后新增 provider 时再次漏依赖。
