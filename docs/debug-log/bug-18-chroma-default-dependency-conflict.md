# Bug 18：把 Chroma 设为默认检索后端时出现依赖冲突

## 现象

为了让项目更明确体现 RAG 技术栈，决定把默认历史检索后端从 `lightweight` 改为 `chroma`，并把 Chroma 安装进项目虚拟环境。

安装后运行：

```powershell
.\.venv\Scripts\python.exe -m pip check
```

发现依赖冲突：

```text
paddlex 3.6.1 has requirement PyYAML==6.0.2, but you have pyyaml 6.0.3.
```

如果把 `PyYAML` 降回 `6.0.2`，又出现：

```text
kubernetes 36.0.2 has requirement pyyaml>=6.0.3, but you have pyyaml 6.0.2.
```

## 排查过程

1. 安装 `chromadb>=0.5.0` 后，实际解析到：

```text
chromadb 1.5.9
kubernetes 36.0.2
PyYAML 6.0.3
```

2. 但 PaddleOCR 依赖链里的 `paddlex 3.6.1` 严格要求：

```text
PyYAML==6.0.2
```

3. 尝试改用旧版 `chromadb==0.5.23`，结果 Windows 上需要本机编译 `chroma-hnswlib`：

```text
Microsoft Visual C++ 14.0 or greater is required.
```

这会显著提高本地安装门槛，不适合当前 demo。

4. 保留有 Windows wheel 的 `chromadb 1.5.9`，将其间接依赖 `kubernetes` 降到仍满足 Chroma 要求、且兼容 `PyYAML==6.0.2` 的版本：

```text
kubernetes==35.0.0
PyYAML==6.0.2
```

5. 验证：

```text
chromadb 1.5.9
kubernetes 35.0.0
yaml 6.0.2
pip check -> No broken requirements found.
```

并做 Chroma provider smoke：写入一条 memory，索引到 Chroma，再按“鼠标”检索回对应 memory id。

## 根因

这是 Chroma 默认依赖链和 PaddleOCR/PaddleX 依赖链之间的版本约束冲突：

- 新版 `kubernetes` 要求 `PyYAML>=6.0.3`。
- `paddlex 3.6.1` 要求 `PyYAML==6.0.2`。
- 旧版 Chroma 在 Windows 上可能需要编译 `chroma-hnswlib`，安装门槛更高。

## 修复

1. 将默认检索后端改为：

```text
AI_GLASSES_SEARCH_PROVIDER=chroma
```

2. 将 Chroma 作为运行依赖写入 `pyproject.toml` 和 `requirements.txt`。

3. 显式 pin 兼容组合：

```text
chromadb>=0.5.0
kubernetes==35.0.0
PyYAML==6.0.2
```

4. 更新 `.env.example` 和本地 `.env`，默认使用：

```text
AI_GLASSES_CHROMA_PATH=data/chroma
AI_GLASSES_CHROMA_COLLECTION=visual_memory
```

## 面试复盘说法

> 我把项目默认检索后端升级为 Chroma，以便更清楚地体现 RAG 的向量数据库层。但安装后没有只看 import 是否成功，而是用 `pip check` 检查依赖一致性，发现 Chroma 的 `kubernetes` 依赖和 PaddleOCR 的 `paddlex` 对 PyYAML 的版本要求冲突。  
>  
> 我没有简单升级或降级某一个包，而是比较了 Chroma 版本在 Windows 上的安装成本。旧版 Chroma 会触发 `chroma-hnswlib` 本地编译，需要 C++ Build Tools；所以我保留有 wheel 的新版 Chroma，同时把 `kubernetes` pin 到 35.0.0，并保留 `PyYAML==6.0.2` 来兼容 PaddleX。最后用 `pip check`、Chroma import 和 provider smoke 验证依赖组合是干净可运行的。
