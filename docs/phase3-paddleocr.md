# Phase 3.1：接入 PaddleOCR

## 目标

把阶段 1/2 的模拟 OCR 替换为可选的真实 OCR 能力。当前阶段只接 PaddleOCR，不接真实 VLM、向量检索或 ASR。

## 数据流

```text
手机拍照 / 图片上传
-> 保存图片到 data/uploads
-> PaddleOCR 识别文字
-> mock VLM 基于真实 OCR 文本回答
-> 写入 SQLite
-> 时间线展示 OCR 文本和回答
```

## 配置开关

默认仍然使用 mock OCR：

```text
AI_GLASSES_OCR_PROVIDER=mock
```

启用 PaddleOCR：

```text
AI_GLASSES_OCR_PROVIDER=paddleocr
```

如果 PaddleOCR 未安装、模型初始化失败、识别失败或没有图片输入，系统会自动回退到 mock OCR，避免 demo 崩溃。

## 本地安装

建议使用项目内虚拟环境，避免 PaddleOCR 的重依赖污染 Anaconda 或系统 Python：

```powershell
cd D:\ARglasses
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

先安装 PaddlePaddle CPU 版：

```powershell
.\.venv\Scripts\python.exe -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

再安装项目和 OCR 可选依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ocr]"
.\.venv\Scripts\python.exe -m pip install "numpy==1.26.4" "pillow==10.4.0" "protobuf==4.25.3" "httpx==0.27.0"
```

然后设置环境变量并启动：

```powershell
$env:AI_GLASSES_OCR_PROVIDER="paddleocr"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

第一次运行 PaddleOCR 可能会下载模型，耗时较长。建议先在本地跑通，再决定是否放到线上部署环境。

当前在 Windows + Python 3.12 本机验证通过的组合：

```text
paddlepaddle==3.2.0
paddleocr==3.6.0
numpy==1.26.4
pillow==10.4.0
protobuf==4.25.3
httpx==0.27.0
```

不要直接用 `paddlepaddle==3.3.0`。本项目验证时，`paddlepaddle 3.3.0 + paddleocr 3.6.0` 在 Windows CPU 上触发过 PaddlePaddle oneDNN/PIR runtime 错误。

## 线上部署建议

主 `requirements.txt` 暂时不包含 PaddleOCR。原因：

- PaddleOCR / PaddlePaddle 依赖较重。
- 免费云平台构建时间和磁盘空间可能不稳定。
- 阶段 1/2 的线上 demo 需要保持可打开、可演示。

如果要在线上启用 PaddleOCR，先单独验证云平台是否能安装 PaddleOCR 和 PaddlePaddle，再把 OCR 依赖加入部署依赖。

## 后续优化先记录，不打断主线

当前 PaddleOCR 的目标是先证明真实 OCR 能进入视觉记忆 pipeline。后续再优化两个方向：

- OCR 识别速度：处理首次冷启动慢、CPU 推理慢、图片过大等问题。
- 外文翻译成中文：把英文、日文、韩文等 OCR 文本翻译成中文，再参与回答和记忆写入。

详细优化计划见 [docs/optimization-backlog.md](optimization-backlog.md)。这些优化等完整项目主链路跑通后再做。

## 面试表述

> 我把 OCR 模块设计成 provider 形式，通过 `AI_GLASSES_OCR_PROVIDER` 在 `mock` 和 `paddleocr` 之间切换。  
> PaddleOCR 是重依赖，所以我没有直接塞进主部署依赖，而是做成可选依赖。  
> 这样本地可以启用真实 OCR，线上 demo 即使没有安装 PaddleOCR 也会自动回退到 mock，不影响作品展示。
