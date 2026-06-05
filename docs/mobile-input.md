# 独立手机输入页

## 目标

`st.camera_input` 有时会受浏览器权限、HTTPS、内置浏览器和页面状态影响。为了让手机第一视角输入更稳定，新增一个独立 FastAPI 手机页面：

```text
手机浏览器
-> /mobile
-> 拍照 / 选择图片
-> POST /mobile/ask
-> MemoryPipeline
-> OCR / VLM / 摘要 / SQLite
```

手机只负责拍照上传，所有依赖仍然运行在本地电脑或云端后端。

后端会在保存上传图片时统一压缩图片，默认最长边 `1600`，避免手机 4096x3072 原图直接进入 OCR / VLM。

## 启动方式

在电脑上启动 FastAPI，并监听局域网地址：

```powershell
cd D:\ARglasses
.\.venv\Scripts\python.exe -m uvicorn ai_glasses_memory.main:app --host 0.0.0.0 --port 8000 --reload
```

查电脑局域网 IP：

```powershell
ipconfig
```

手机和电脑连接同一个 Wi-Fi，然后手机浏览器打开：

```text
http://电脑局域网IP:8000/mobile
```

例如：

```text
http://192.168.1.23:8000/mobile
```

## 页面行为

手机页面使用原生 HTML：

```html
<input type="file" accept="image/*" capture="environment">
```

在大多数手机浏览器中，点击后会打开后置摄像头拍照；如果浏览器不支持，也会退化为选择图片。

## 和 Streamlit 的关系

Streamlit 继续作为主展示端：

```text
http://localhost:8501
```

它负责：

- 当前回答展示。
- OCR / VLM / 摘要展示。
- 时间线。
- 搜索。

手机页负责：

- 更稳定的拍照上传。
- 模拟 AI 眼镜第一视角输入。
- 为后续 RK3588 摄像头 HTTP 上传做接口铺垫。

## 后续扩展

下一步可以让手机页面提交后显示更友好的结果页，或者只负责上传帧，由 Streamlit 自动刷新时间线。

硬件阶段可以复用 `/mobile/ask` 的思路，把 RK3588 摄像头采集到的图片用 multipart/form-data 上传到同一个后端 pipeline。
