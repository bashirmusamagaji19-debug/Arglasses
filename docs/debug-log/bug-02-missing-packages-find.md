# Bug 2：`pyproject.toml` 缺少 `packages.find`，src layout 包未注册

**日期：** 2026-06-03
**严重程度：** 致命 — 部署直接挂掉
**关键词：** src layout、`[tool.setuptools.packages.find]`、包发现、pip install

---

## 现象

本地 `pip install -e .` 后可以运行。但推到 GitHub 后，同事/CI 拉下来 `pip install -r requirements.txt` 后报：

```
ModuleNotFoundError: No module named 'ai_glasses_memory'
```

注意：这个 Bug 是在 Bug 1 之前的——在修复 `.gitignore` 之前我们就遇到了。两次 `ModuleNotFoundError` 的根因不同，但症状类似，容易混淆。

## 排查过程

### 第一步：确认 pip 安装成功了

```
pip install -r requirements.txt
```

输出显示安装成功。但尝试导入就报错。

### 第二步：查看 site-packages

```python
pip show ai-glasses-memory
```

发现包确实安装了，但里面**只有 metadata，没有实际代码**。

### 第三步：看 pyproject.toml

```toml
[project]
name = "ai-glasses-memory"
version = "0.1.0"
description = "AI 眼镜实时视觉记忆助手"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.8.0",
    "streamlit>=1.36.0",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "httpx>=0.27.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

**注意：没有 `[tool.setuptools.packages.find]`。**

### 第四步：定位到根因

项目的代码结构是 **src layout**：

```
pyproject.toml
src/
  ai_glasses_memory/
    __init__.py
    api/
    models/
    services/
    ui/
```

Setuptools 默认只在项目根目录下找包。如果代码在 `src/` 下面，必须显式告诉它：

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

没有这个配置，setuptools 找不到任何包，build 出来的 wheel 只有 metadata，没有代码文件。

## 根因

| 缺失配置 | 后果 |
|---------|------|
| `[tool.setuptools.packages.find] where = ["src"]` | Setuptools 不知道去 `src/` 下找包，wheel 是空的 |

之前本地能跑是因为先用了 `pip install -e .` 的 editable 模式，而且在开发过程中 Python 的 `sys.path` 可能直接包含了 `src/` 目录（IDE 帮忙加的），没有真正测试过非 editable 安装。

## 修复

在 `pyproject.toml` 里加上：

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

放在 `[project]` 和 `[tool.pytest.ini_options]` 之间。

加了之后重新 build，确认 wheel 里包含了所有模块文件。

## 面试回答

> **面试官：** 你的项目用 src layout 还是 flat layout？为什么？
>
> **我：** 我们用的是 src layout，代码放在 `src/` 下面。好处是：
>
> 1. **避免导入混乱** —— 测试时不会意外导入项目根目录的脚本而不是已安装的包。
> 2. **更接近真实部署** —— 部署时 pip 安装的是 wheel，不是直接跑源码，src layout 强制你验证安装流程。
>
> 说到这个，我们部署时就在这踩了个坑。`pyproject.toml` 里忘了写 `[tool.setuptools.packages.find] where = ["src"]`，setuptools 找不到包，build 出来的 wheel 是空的。本地开发时用 `pip install -e .`（editable mode）没暴露这个问题，但 CI 和 Streamlit Cloud 上直接挂了。
>
> 修复就是加上这 3 行配置。之后我们养成了一个习惯：**每次改包结构后，都做一次「从零安装测试」——删掉 `.egg-info` 和 `build/`，重新 `pip install .`，确认能导入。**

## 教训

- **Editable install（`-e .`）和正式 install（`.`）不同。** 前者在开发时很方便，但掩盖了包发现配置的问题。上线前必须用正式安装方式测试一遍。
- **src layout 必须配 `[tool.setuptools.packages.find]`。** 这是最容易被忽视的配置项。
- **每次修改包结构后，做一次 clean rebuild 验证。**

## 验证命令

```bash
# 从零验证安装
pip uninstall ai-glasses-memory -y
rm -rf build/ *.egg-info
pip install .
python -c "from ai_glasses_memory.models.memory import MemoryEvent; print('OK')"
```
