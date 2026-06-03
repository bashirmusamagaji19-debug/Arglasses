# Bug 4：Streamlit 点击提交后黑屏 - 入口脚本导入方式导致 UI 不挂载

**日期：** 2026-06-03  
**严重程度：** 高 - 线上 demo 可打开但交互后无法展示内容  
**关键词：** Streamlit、黑屏、entrypoint、`app.py`、`runpy.run_path`

---

## 现象

阶段 1 部署成功后，页面可以打开，但点击“提交问题”按钮后，用户看到界面黑屏。

本地复现时，浏览器里只剩 Streamlit 顶部栏，页面主体内容没有挂载出来。服务端 `/healthz` 和 `/_stcore/health` 都返回 `ok`，说明不是服务进程直接崩溃，而是 Streamlit app 脚本没有按预期渲染 UI。

## 排查过程

1. 先暂停阶段 2，不继续加新功能，避免把新问题叠到旧问题上。
2. 本地启动 Streamlit：

```powershell
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8765 --server.headless true
```

3. 用浏览器打开 `http://127.0.0.1:8765`，复现到只有 Streamlit 顶栏、没有应用主体内容。
4. 检查 Streamlit 服务日志，未发现 Python traceback。
5. 检查浏览器 console，未发现直接解释业务异常的错误。
6. 对比 `app.py` 和真实 UI 文件 `src/ai_glasses_memory/ui/streamlit_app.py`，发现入口文件使用了普通 Python import：

```python
from ai_glasses_memory.ui.streamlit_app import *
```

这会把 Streamlit UI 文件当作普通模块导入，而不是让 Streamlit 按脚本文件路径执行真实 UI 文件。

## 根因

Streamlit 对脚本运行上下文敏感。云端和本地运行时是通过 `streamlit run app.py` 启动的，因此 `app.py` 应该是一个稳定的 Streamlit 脚本入口。

原来的 `app.py` 只是 import 另一个模块：

```python
from ai_glasses_memory.ui.streamlit_app import *
```

这种方式在普通 Python 里能导入，但在 Streamlit 的脚本执行模型中不够稳，容易出现页面主体不挂载、交互后重新运行异常或黑屏现象。

## 修复

把 `app.py` 改为：

```python
import runpy
import sys
from pathlib import Path

_root = Path(__file__).parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

runpy.run_path(str(_src / "ai_glasses_memory" / "ui" / "streamlit_app.py"))
```

修复点有两个：

- `app.py` 仍然作为云平台入口，方便 Streamlit Cloud / Render 选择根目录文件。
- 真正的 UI 代码通过 `runpy.run_path(...)` 直接执行，避免用 `import *` 破坏 Streamlit 的脚本执行语义。

## 验证

自动化测试：

```powershell
python -m pytest -q
```

结果：

```text
11 passed, 1 warning
```

本地手动验证：

1. 启动 `streamlit run app.py`。
2. 浏览器打开本地页面。
3. 页面主体正常显示。
4. 不上传图片，直接点击“提交问题”。
5. 页面正常展示模拟回答、OCR 文本、场景摘要和延迟统计。
6. 时间线新增一条记录。
7. `/_stcore/health` 返回 `ok`。

## 面试回答

> **面试官：** 你部署 Streamlit 项目时遇到过什么线上问题？
>
> **我：** 遇到过一次线上 demo 点击按钮后黑屏的问题。第一反应不是直接改 UI，而是先定位它到底是服务端崩了、浏览器报错，还是 Streamlit 脚本没有正常挂载。  
> 我本地启动同样的 `streamlit run app.py`，发现可以复现：页面只剩 Streamlit 顶栏，主体内容不显示。但 health check 是正常的，服务端也没有 Python traceback。  
> 后来我检查入口文件，发现 `app.py` 里用的是 `from ai_glasses_memory.ui.streamlit_app import *`，也就是把真正的 UI 文件当普通模块导入。Streamlit 对脚本运行上下文比较敏感，这种入口方式不稳定。  
> 最后我把入口改成 `runpy.run_path(...)` 直接执行真实 UI 脚本，同时保留 `src` 路径注入。修复后，本地点击提交可以正常生成回答、写入 SQLite、刷新时间线，自动化测试也通过。

## 教训

- Streamlit 云部署入口最好是直接可执行的脚本，不要用 `import *` 转发 UI。
- “黑屏但 health 正常”通常说明进程没死，重点要查前端挂载、脚本执行上下文和浏览器日志。
- 修 bug 时先复现和收集证据，再改入口方式；不要在没确认根因时同时改 UI、依赖和业务逻辑。
