# Bug 5：PaddleOCR Windows CPU 版真实推理失败 - PaddlePaddle 版本组合问题

**日期：** 2026-06-04  
**严重程度：** 高 - PaddleOCR 能安装但真实推理回退到 mock  
**关键词：** PaddleOCR、PaddlePaddle、Windows CPU、oneDNN、PIR、版本组合

---

## 现象

阶段 3.1 接入 PaddleOCR 后，`AI_GLASSES_OCR_PROVIDER=paddleocr` 没有直接崩溃，但 OCR 输出仍然是 mock 文本：

```text
模拟 OCR：画面中可能包含电脑屏幕、课程笔记、水杯和一张写着 AI 眼镜项目计划的纸。
```

这说明 provider 里的异常回退生效了，但真实 PaddleOCR 没有跑通。

## 排查过程

1. 先安装 Windows CPU 版 PaddlePaddle：

```powershell
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install paddleocr
```

2. 用项目内的 `PaddleOCRProvider` 跑测试图片，发现输出仍是 mock。
3. 绕过 provider，直接调用 PaddleOCR API，拿到具体异常：

```text
TypeError: PaddleOCR.predict() got an unexpected keyword argument 'cls'
```

4. 继续直接调用 `engine.predict(...)`，又触发 PaddlePaddle runtime 错误：

```text
NotImplementedError:
(Unimplemented) ConvertPirAttribute2RuntimeAttribute not support
[pir::ArrayAttribute<pir::DoubleAttribute>]
...\onednn_instruction.cc:118
```

5. 尝试设置 `FLAGS_use_mkldnn=0`，仍然触发同一类 oneDNN/PIR 错误。
6. 进一步验证发现 `paddlepaddle==3.3.0` 会把环境带到不稳定状态。
7. 降级到 `paddlepaddle==3.2.0` 后，pip 又把 `numpy/pillow/protobuf/httpx` 升到了和 Streamlit/Anaconda 不兼容的版本。
8. 手动恢复关键依赖版本，并用 `pip check` 验证环境干净。

## 根因

有两个问题叠在一起：

1. PaddleOCR 3.x 的 API 已经偏向 `predict()`，旧写法 `ocr(..., cls=True)` 会触发不兼容参数。
2. `paddlepaddle==3.3.0 + paddleocr==3.6.0` 在 Windows CPU 环境下会触发 PaddlePaddle oneDNN/PIR runtime 错误。

## 修复

代码层面：

- provider 改为调用 `engine.predict(image_path)`。
- 初始化时关闭文档方向分类、文档矫正和文本行方向分类，降低模型数量和推理复杂度：

```python
PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="ch",
)
```

- 解析 PaddleOCR 3.x 的 `rec_texts`：

```python
result[0]["rec_texts"]
```

环境层面：

```powershell
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install paddleocr==3.6.0
python -m pip install numpy==1.26.4 pillow==10.4.0 protobuf==4.25.3 httpx==0.27.0
```

## 验证

依赖一致性：

```powershell
python -m pip check
```

结果：

```text
No broken requirements found.
```

自动化测试：

```powershell
python -m pytest -q
```

结果：

```text
20 passed, 1 warning
```

真实 OCR smoke test：

```powershell
python -c "from ai_glasses_memory.services.ocr import PaddleOCRProvider; print(PaddleOCRProvider().extract_text('data/ocr_test.png'))"
```

结果：

```text
PaddleOCR：AI Glasses Memory 123
```

## 面试回答

> **面试官：** 你接入真实 OCR 的时候遇到过什么工程问题？
>
> **我：** 遇到过 PaddleOCR 在 Windows CPU 环境下安装成功但推理失败的问题。  
> 一开始我没有直接把失败暴露给用户，而是在 OCR provider 里做了 mock fallback，所以 demo 不会崩。随后我单独绕过 provider 调 PaddleOCR，发现问题分两层：第一是 PaddleOCR 3.x API 已经转向 `predict()`，旧版 `ocr(..., cls=True)` 不兼容；第二是 `paddlepaddle 3.3.0` 在 Windows CPU 上触发 oneDNN/PIR runtime 错误。  
> 最后我把代码适配到 PaddleOCR 3.x 的 `predict()` 和 `rec_texts` 结构，并把本地可行环境固定为 `paddlepaddle 3.2.0 + paddleocr 3.6.0`。同时我用 `pip check` 保证没有破坏 Streamlit 的依赖，再用一张本地文字图片验证真实 OCR 输出。

## 教训

- 重依赖不要直接塞进主部署链路，先做 provider + fallback。
- 安装成功不等于推理成功，要用真实图片做 smoke test。
- PaddleOCR 这种库要同时锁 Python、PaddlePaddle、PaddleOCR 和基础科学计算依赖版本。
- 调试时不要只看业务输出，必须绕过回退层拿到真实异常。
