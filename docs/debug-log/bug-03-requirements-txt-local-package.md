# Bug 3：`requirements.txt` 里本地包的处理 —— editable vs 显式依赖

**日期：** 2026-06-03
**严重程度：** 高 — 部署失败
**关键词：** `requirements.txt`、`-e .`、editable install、Streamlit Cloud 构建

---

## 现象

在 Streamlit Cloud 上部署时，构建日志里 pip 安装步骤失败或安装后模块找不到。

这是一个**连环踩坑**——同一个问题反复了两次，每次改的方式都差一点。

## 第一次尝试：`-e .`

最初的 `requirements.txt`：

```
-e .
```

`-e .` 表示以 editable 模式安装当前目录的包。这在本地开发时很常见，pip 会读 `pyproject.toml` 安装所有依赖，并且把当前目录链接到 site-packages。

**但在 Streamlit Cloud 上：**

- Streamlit Cloud 的构建流程在临时目录里运行
- Editable install 创建的是**符号链接**，指向构建时的临时路径
- 运行时那个路径可能已经不在了，或者权限不对
- 结果：构建成功，但运行时报 `ModuleNotFoundError`

## 第二次尝试：全部换成显式依赖

吸取"教训"，我把 `-e .` 换掉，**直接列了所有依赖**：

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
streamlit>=1.36.0
python-multipart>=0.0.9
```

但 `app.py` 里有这行：

```python
from ai_glasses_memory.ui.streamlit_app import *
```

`ai_glasses_memory` 是我们自己的包，不是 PyPI 上的。只列外部依赖，**忘记装本地包本身了**。

## 第三次尝试：显式依赖 + `.`

```diff
 fastapi>=0.115.0
 uvicorn[standard]>=0.30.0
 pydantic>=2.8.0
 streamlit>=1.36.0
 python-multipart>=0.0.9
+.
```

这里的 `.` 表示**以非 editable 模式安装本地包**。pip 会 build 一个 wheel，安装到 site-packages 里。构建时的文件会被**复制**到 site-packages，不依赖符号链接。

这次成功了。

## 三种方式的对比

| 方式 | 本质 | 本地开发 | Streamlit Cloud |
|------|------|---------|----------------|
| `-e .` | 符号链接到源码目录 | ✅ 修改即时生效 | ❌ 路径/权限问题 |
| 只列 PyPI 依赖 | 只装外部包 | ✅ | ❌ 漏了本地包 |
| `.` | 安装 wheel 到 site-packages | ✅ 但修改后需重装 | ✅ 稳定 |

## 根因

Streamlit Cloud 的 pip install 是在构建环境里跑的，不是开发者的机器。Editable install 假设"源码目录会一直在同一个路径"，这在 CI/CD 里不成立。

## 最佳实践

对于 Streamlit Cloud / Render 这类部署平台：

```
# requirements.txt — Streamlit Cloud / Render 部署用
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
streamlit>=1.36.0
python-multipart>=0.0.9
.
```

```
# requirements-dev.txt — 本地开发用
-e .
```

分两个文件，各取所需。

## 面试回答

> **面试官：** 你部署 Python 项目到云平台时，遇到过依赖安装的问题吗？
>
> **我：** 遇到过，主要是 `requirements.txt` 里本地包的安装方式。
>
> 我们项目用 src layout，自己的代码作为一个包安装在 `site-packages` 里。本地开发时用 `-e .`（editable mode），这样改代码不用重装。
>
> 但第一次部署到 Streamlit Cloud 时，`-e .` 挂了。原因是 editable install 创建符号链接指向构建时的临时路径，云平台运行时的目录结构和构建时不一致，链接就断了。
>
> 修复方法很简单：把 `-e .` 改成 `.`，这样 pip 会 build 一个真正的 wheel 并复制到 site-packages，不依赖路径。
>
> 后来我们分了两个 requirements 文件：`requirements.txt` 给部署用（显式依赖 + `.`），`requirements-dev.txt` 给本地开发用（`-e .`）。这样两边都满意。

## 教训

- **`-e .` 只适合本地开发。** 部署到任何云平台时用 `.`（非 editable）。
- **列了显式依赖后别忘了加 `.` 装本地包。**
- 推荐分两个 requirements 文件：`requirements.txt`（部署）和 `requirements-dev.txt`（开发）。
