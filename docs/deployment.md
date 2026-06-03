# Deployment Guide

阶段 1 的目标是先部署一个可打开、可演示的 Web MVP。当前版本使用模拟 OCR / 模拟 VLM，不需要 API Key，也不接真实模型。

## 部署入口

- Streamlit 入口：`app.py`
- 本地 UI 源码：`src/ai_glasses_memory/ui/streamlit_app.py`
- 依赖文件：`requirements.txt`
- Render Blueprint：`render.yaml`

## 方案 A：Streamlit Community Cloud

适合最快拿到线上 demo 链接。

1. 把项目推到 GitHub。
2. 在 Streamlit Community Cloud 创建新应用。
3. 选择仓库和分支。
4. Main file path 填写：

```text
app.py
```

5. 部署完成后打开页面，输入问题并提交，确认时间线出现新记录。

说明：Streamlit Cloud 的免费环境适合演示，不适合长期保存 SQLite 数据。应用重启后，`data/memory.sqlite3` 里的线上数据可能丢失。

## 方案 B：Render Web Service

适合用 `render.yaml` 直接创建服务。

1. 把项目推到 GitHub。
2. 在 Render 选择 Blueprint 或 Web Service。
3. 如果使用 Blueprint，Render 会读取 `render.yaml`。
4. 如果手动创建 Web Service，填写：

```text
Build Command:
python -m pip install --upgrade pip && python -m pip install -r requirements.txt

Start Command:
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

5. 环境变量：

```text
AI_GLASSES_DB_PATH=data/memory.sqlite3
```

说明：当前 `render.yaml` 未配置持久磁盘，免费服务重启后 SQLite 数据可能丢失。阶段 1 重点是作品集演示入口；等需要稳定保存线上数据时，再加 Render Disk 或迁移到外部数据库。

## 本地部署前检查

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

另开一个 PowerShell 检查页面是否启动：

```powershell
Invoke-WebRequest http://127.0.0.1:8501 -UseBasicParsing
```

## 阶段 1 演示脚本

1. 打开线上 demo。
2. 上传任意图片，或不上传图片直接提问。
3. 输入问题：`我刚才看到了什么？`
4. 提交后展示模拟回答、模拟 OCR、场景摘要和 latency。
5. 在时间线中展示刚才的记忆记录。
6. 搜索关键词，例如 `模拟`，展示历史检索能力。
