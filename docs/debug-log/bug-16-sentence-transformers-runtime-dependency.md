# Bug 16：真实向量检索启动时报 `sentence-transformers is not installed`

## 现象

在 Streamlit 页面使用历史检索时，搜索触发向量索引重建，页面报错：

```text
RuntimeError: sentence-transformers is not installed. Install the embedding optional dependency first.
```

此前终端还出现过：

```text
ModuleNotFoundError: No module named 'torchvision'
```

## 排查过程

1. 先检查 `.env`，确认当前不是轻量检索，而是：

```text
AI_GLASSES_SEARCH_PROVIDER=vector
AI_GLASSES_EMBEDDING_PROVIDER=sentence_transformers
AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

2. 检查命令解析路径，发现直接运行 `python` / `streamlit` 时优先命中 Anaconda：

```text
D:\Anaconda\python.exe
D:\Anaconda\Scripts\streamlit.exe
```

3. 再检查项目虚拟环境 `.venv`，发现 `.venv` 里其实已经安装了真实 embedding 依赖：

```text
sentence-transformers 5.5.1
transformers 5.10.2
torch 2.12.0+cpu
```

4. 继续检查可选依赖缺口，发现 `.venv` 里缺少 `torchvision`。Streamlit 文件监听器扫描 `transformers` 的 image processor 模块时，会触发 `torchvision.transforms.v2` 导入。

5. 根据当前 `torch 2.12.0+cpu` 选择匹配版本：

```text
torchvision==0.27.0
```

安装后验证：

```text
torch 2.12.0+cpu
torchvision 0.27.0+cpu
sentence_transformers 5.5.1
transformers 5.10.2
```

并实际运行 `BAAI/bge-small-zh-v1.5` embedding，输出 512 维向量，归一化长度约为 1.0。

## 根因

这是两个问题叠加：

- 启动命令有时使用了 Anaconda 的 Python / Streamlit，而不是项目 `.venv`，所以页面看不到 `.venv` 里的 `sentence-transformers`。
- `sentence-transformers` 依赖链里的 `transformers` 会被 Streamlit watcher 扫描到图像处理模块，缺少 `torchvision` 时会产生运行时噪音或错误。

## 修复

1. 启动 demo 时固定使用项目虚拟环境：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.fileWatcherType none
```

2. 将 `torchvision==0.27.0` 加入 `pyproject.toml` 的 `embedding` 可选依赖，避免后续重新安装 embedding extra 时漏装。

3. 增加部署测试，锁定 `embedding` extra 必须包含 `sentence-transformers` 和 matching `torchvision`。

## 面试复盘说法

> 我在接入真实向量检索时遇到一个典型的 Windows 环境问题：报错表面上是 `sentence-transformers` 没安装，但排查路径后发现实际启动的是 Anaconda 的 Streamlit，而不是项目虚拟环境。进一步验证 `.venv` 后，确认真实 embedding 依赖已安装，但 `transformers` 在 Streamlit watcher 扫描 image processor 时还需要 `torchvision`。  
>  
> 最后我把启动命令固定为 `.venv\Scripts\python.exe -m streamlit`，并按当前 `torch 2.12.0+cpu` 补了 matching `torchvision==0.27.0`，同时把这个版本写进项目的 optional dependency 和测试里。这个过程的关键不是盲目安装包，而是先确认“当前运行环境”和“项目虚拟环境”是否一致。
