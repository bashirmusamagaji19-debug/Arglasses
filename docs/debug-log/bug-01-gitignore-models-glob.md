# Bug 1：`.gitignore` 通配符误匹配导致模型模块从未被提交

**日期：** 2026-06-03
**严重程度：** 致命 — 部署直接挂掉
**关键词：** `.gitignore` 通配符、`ModuleNotFoundError`、Streamlit Cloud 部署、git 未跟踪

---

## 现象

部署到 Streamlit Community Cloud 后，页面报错：

```
ModuleNotFoundError: No module named 'ai_glasses_memory.models'
```

但本地运行完全正常。

## 排查过程

### 第一步：看完整 Traceback

Streamlit Cloud 的报错页面会隐藏原始错误信息（"redacted to prevent data leaks"），但 Traceback 还在：

```
File "/mount/src/arglasses/app.py", line 3, in <module>
    from ai_glasses_memory.ui.streamlit_app import *
File ".../site-packages/ai_glasses_memory/services/memory_store.py", line 9, in <module>
    from ai_glasses_memory.models.memory import MemoryEvent, MemoryEventCreate
```

关键线索：**包已经安装到 site-packages 了**（`ui.streamlit_app` 和 `services.memory_store` 都找到了），但 `models.memory` 找不到。

### 第二步：怀疑 Python 3.14 兼容性

Streamlit Cloud 环境是 Python 3.14（还在开发阶段）。我一开始以为是 pydantic 和 Python 3.14 的注解解析问题，做了好几轮尝试：

- 把 `str | None` 改成 `Optional[str]`
- 给 `ui/` 目录加上 `__init__.py`
- 在 `app.py` 里加 `sys.path` 后备导入

**全都没用。** 说明方向错了。

### 第三步：查 git 跟踪状态

用 `git ls-files src/ai_glasses_memory/models/` 检查 git 到底跟踪了哪些文件。

**输出为空。** 一个文件都没有。

### 第四步：找到根因

检查 `.gitignore`：

```
.superpowers/
.reasonix/
__pycache__/
.pytest_cache/
.venv/
venv/
.env
*.pyc
*.pyo
*.pyd
*.log
*.sqlite3
*.db
*.egg-info/
data/
models/
outputs/
```

看到最后一行 `models/` 了吗？

**`.gitignore` 的通配模式 `models/` 匹配了任意路径下的 `models/` 目录。** 包括 `src/ai_glasses_memory/models/`。

所以从第一次 `git init && git add . && git commit` 开始，`models/__init__.py` 和 `models/memory.py` **就从未被 git 跟踪过**。

本地跑没问题，因为文件在磁盘上。但 Streamlit Cloud 部署时是做 `git clone`，这两个文件根本不存在，pip build wheel 时也不包含 `models` 子包，于是 `ModuleNotFoundError`。

## 根因

`.gitignore` 的 `models/` 没有用斜杠开头，变成了**通配规则**：

| 写法 | 含义 |
|------|------|
| `models/` | 匹配任意目录下的 `models/`（通配） |
| `/models/` | 只匹配项目根目录下的 `models/`（锚定） |

原本的意图是忽略根目录的 `models/` 文件夹（放 ML 模型文件的），结果误伤了 `src/ai_glasses_memory/models/`（放源码数据模型的）。

## 修复

把 `models/` 改为 `/models/`：

```diff
- models/
+ /models/
```

然后重新 `git add` 并提交，确认 `src/ai_glasses_memory/models/` 中的文件被正确跟踪。

## 面试回答

> **面试官：** 你部署 Streamlit 时遇到过 ModuleNotFoundError 吗？怎么排查的？
>
> **我：** 遇到过。当时现象是本地能跑，部署后报 `ModuleNotFoundError: No module named 'xxx.models'`。
>
> 我的排查思路是三步：
>
> 1. **看 Traceback 定位哪个导入失败** — 发现包的其他部分（ui、services）都找到了，只有 models 子包找不到。
> 2. **查 git 是否真的跟踪了那个文件** — 用 `git ls-files` 确认 `src/ai_glasses_memory/models/` 目录完全没有被跟踪。
> 3. **查 `.gitignore` 是否有通配冲突** — 发现 `models/` 这个规则匹配了任意嵌套的 models 目录，把源码目录误杀了。
>
> 修复就是把 `models/` 改成 `/models/`，只匹配根目录。这也提醒我：**写 `.gitignore` 时要注意斜杠的位置，不加前导斜杠就是通配规则，可能误伤深层目录。**

## 教训

- `git ls-files` 是排查"文件为什么不在仓库里"的第一工具。
- `.gitignore` 的规则是**通配的**，`models/` 和 `/models/` 含义不同：
  - `/models/` = 根目录的 models/
  - `models/` = 任意位置的 models/
- 本地能跑 ≠ 部署能跑。本地跑的是磁盘文件，部署跑的是 git 跟踪的文件。
