# 调试日志

> 本项目部署到 Streamlit Community Cloud 过程中遇到的 Bug 及排查过程。
> 以第一人称视角记录，方便面试复盘。

## 目录

| # | Bug | 根因 | 文件 |
|---|-----|------|------|
| 1 | `ModuleNotFoundError: ai_glasses_memory.models` | `.gitignore` 的 `models/` 通配符误匹配了 `src/ai_glasses_memory/models/` | [bug-01-gitignore-models-glob.md](./bug-01-gitignore-models-glob.md) |
| 2 | `ModuleNotFoundError: ai_glasses_memory` | `pyproject.toml` 缺少 `[tool.setuptools.packages.find]`，src layout 包未注册 | [bug-02-missing-packages-find.md](./bug-02-missing-packages-find.md) |
| 3 | Streamlit Cloud 部署构建失败 | `requirements.txt` 用 `-e .` 不兼容；替换为显式依赖后漏了本地包安装 | [bug-03-requirements-txt-local-package.md](./bug-03-requirements-txt-local-package.md) |
