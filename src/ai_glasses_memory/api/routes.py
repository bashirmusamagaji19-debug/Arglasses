from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ai_glasses_memory.models.memory import MemoryEvent
from ai_glasses_memory.services.factory import create_pipeline
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.uploads import save_input_audio, save_input_image

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    image_path: str | None = None


class MutationResult(BaseModel):
    deleted: int


class RAGAnswerRequest(BaseModel):
    question: str
    limit: int = 3


class RAGAnswerResponse(BaseModel):
    answer: str
    context_memories: list[MemoryEvent]


class TranscriptionResponse(BaseModel):
    text: str
    audio_path: str
    latency_ms: dict[str, float]


def get_pipeline() -> MemoryPipeline:
    return create_pipeline()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-glasses-memory"}


@router.get("/mobile", response_class=HTMLResponse)
def mobile_page() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 眼镜手机输入</title>
  <style>
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f7f7f8;
      color: #171717;
    }
    main {
      max-width: 520px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 {
      font-size: 22px;
      margin: 8px 0 18px;
    }
    label {
      display: block;
      font-size: 14px;
      font-weight: 600;
      margin: 16px 0 8px;
    }
    input, button {
      width: 100%;
      box-sizing: border-box;
      font-size: 16px;
    }
    input[type="text"], input[type="file"] {
      border: 1px solid #d0d5dd;
      border-radius: 8px;
      background: #fff;
      padding: 12px;
    }
    button {
      margin-top: 18px;
      border: 0;
      border-radius: 8px;
      padding: 13px 16px;
      background: #2563eb;
      color: #fff;
      font-weight: 700;
    }
    .note {
      margin-top: 14px;
      font-size: 13px;
      color: #525252;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <main>
    <h1>AI 眼镜第一视角输入</h1>
    <form action="/mobile/ask" method="post" enctype="multipart/form-data">
      <label for="question">问题</label>
      <input id="question" name="question" type="text" value="我刚才看到了什么？" required>

      <label for="image">拍照 / 选择图片</label>
      <input id="image" name="image" type="file" accept="image/*" capture="environment" required>

      <button type="submit">提交到视觉记忆系统</button>
    </form>
    <p class="note">手机只负责拍照上传，OCR、VLM、记忆写入和检索都在后端运行。</p>
  </main>
</body>
</html>
"""


@router.get("/live", response_class=HTMLResponse)
def live_page() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 眼镜实时输入</title>
  <style>
    :root {
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f4f6f8;
      color: #111827;
    }
    body {
      margin: 0;
    }
    main {
      max-width: 980px;
      margin: 0 auto;
      padding: 18px;
    }
    h1 {
      font-size: 22px;
      margin: 4px 0 14px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.7fr);
      gap: 16px;
      align-items: start;
    }
    video {
      width: 100%;
      aspect-ratio: 4 / 3;
      background: #111827;
      border-radius: 8px;
      object-fit: cover;
    }
    canvas {
      display: none;
    }
    section {
      background: #fff;
      border: 1px solid #d7dde6;
      border-radius: 8px;
      padding: 14px;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 700;
      margin: 12px 0 6px;
    }
    textarea {
      width: 100%;
      min-height: 86px;
      box-sizing: border-box;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 10px;
      font-size: 15px;
      resize: vertical;
    }
    button {
      width: 100%;
      margin-top: 10px;
      border: 0;
      border-radius: 8px;
      padding: 11px 14px;
      background: #2563eb;
      color: #fff;
      font-size: 15px;
      font-weight: 700;
    }
    button.secondary {
      background: #475569;
    }
    button.warn {
      background: #b45309;
    }
    button:disabled {
      background: #94a3b8;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px;
      min-height: 120px;
    }
    .status {
      font-size: 13px;
      color: #475569;
      line-height: 1.5;
    }
    @media (max-width: 760px) {
      .layout {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main>
    <h1>AI 眼镜实时输入</h1>
    <div class="layout">
      <section>
        <video id="preview" autoplay playsinline muted></video>
        <canvas id="frameCanvas"></canvas>
        <p class="status" id="cameraStatus">正在请求摄像头权限...</p>
      </section>
      <section>
        <label for="question">问题</label>
        <textarea id="question">我现在看到了什么？</textarea>
        <button id="startRecord" class="secondary">开始录音</button>
        <button id="stopRecord" class="warn" disabled>停止录音并转写</button>
        <button id="submitQuestion">截取当前画面并提问</button>
        <p class="status" id="voiceStatus">可手动输入问题，也可以先录音转写。</p>
        <label>回答</label>
        <pre id="result">等待提交。</pre>
      </section>
    </div>
  </main>
  <script>
    const video = document.getElementById("preview");
    const canvas = document.getElementById("frameCanvas");
    const cameraStatus = document.getElementById("cameraStatus");
    const voiceStatus = document.getElementById("voiceStatus");
    const result = document.getElementById("result");
    const question = document.getElementById("question");
    const startRecordButton = document.getElementById("startRecord");
    const stopRecordButton = document.getElementById("stopRecord");
    const submitQuestionButton = document.getElementById("submitQuestion");

    let mediaStream = null;
    let mediaRecorder = null;
    let recordedChunks = [];

    async function startCamera() {
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: true
        });
        video.srcObject = mediaStream;
        cameraStatus.textContent = "摄像头已连接。提问时会自动截取当前视频帧。";
      } catch (error) {
        cameraStatus.textContent = "无法访问摄像头或麦克风：" + error;
      }
    }

    function captureFrame() {
      const width = video.videoWidth || 1280;
      const height = video.videoHeight || 720;
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, width, height);
      return new Promise((resolve) => {
        canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.86);
      });
    }

    startRecordButton.addEventListener("click", () => {
      if (!mediaStream) {
        voiceStatus.textContent = "摄像头/麦克风还没有就绪。";
        return;
      }
      recordedChunks = [];
      mediaRecorder = new MediaRecorder(mediaStream);
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };
      mediaRecorder.onstop = async () => {
        const blob = new Blob(recordedChunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", blob, "voice.webm");
        voiceStatus.textContent = "正在转写语音...";
        const response = await fetch("/live/transcribe", {
          method: "POST",
          body: formData
        });
        const payload = await response.json();
        question.value = payload.text || question.value;
        voiceStatus.textContent = "语音已转写。";
      };
      mediaRecorder.start();
      startRecordButton.disabled = true;
      stopRecordButton.disabled = false;
      voiceStatus.textContent = "正在录音...";
    });

    stopRecordButton.addEventListener("click", () => {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
      startRecordButton.disabled = false;
      stopRecordButton.disabled = true;
    });

    submitQuestionButton.addEventListener("click", async () => {
      const frame = await captureFrame();
      if (!frame) {
        result.textContent = "当前没有可提交的视频帧。";
        return;
      }
      const formData = new FormData();
      formData.append("question", question.value || "我现在看到了什么？");
      formData.append("image", frame, "live-frame.jpg");
      result.textContent = "正在提交视觉记忆 pipeline...";
      const response = await fetch("/live/ask", {
        method: "POST",
        body: formData
      });
      const payload = await response.json();
      result.textContent = [
        "回答：",
        payload.answer || "",
        "",
        "OCR：",
        payload.ocr_text || "",
        "",
        "场景摘要：",
        payload.scene_summary || "",
        "",
        "延迟：",
        JSON.stringify(payload.latency_ms || {}, null, 2)
      ].join("\\n");
    });

    startCamera();
  </script>
</body>
</html>
"""


@router.post("/ask", response_model=MemoryEvent)
def ask(
    request: AskRequest,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MemoryEvent:
    return pipeline.ask(question=request.question, image_path=request.image_path)


@router.post("/mobile/ask", response_model=MemoryEvent)
def mobile_ask(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    question: str = Form(...),
    image: UploadFile = File(...),
) -> MemoryEvent:
    image_path = save_input_image(image)
    return pipeline.ask(question=question, image_path=image_path)


@router.post("/live/ask", response_model=MemoryEvent)
def live_ask(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    question: str = Form(...),
    image: UploadFile = File(...),
) -> MemoryEvent:
    image_path = save_input_image(image)
    return pipeline.ask(question=question, image_path=image_path)


@router.post("/transcribe", response_model=TranscriptionResponse)
def transcribe_audio(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    audio: UploadFile = File(...),
) -> TranscriptionResponse:
    audio_path = save_input_audio(audio)
    result = pipeline.transcribe_audio(audio_path or "")
    return TranscriptionResponse(
        text=result.text,
        audio_path=result.audio_path,
        latency_ms=result.latency_ms,
    )


@router.post("/live/transcribe", response_model=TranscriptionResponse)
def live_transcribe_audio(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    audio: UploadFile = File(...),
) -> TranscriptionResponse:
    audio_path = save_input_audio(audio)
    result = pipeline.transcribe_audio(audio_path or "")
    return TranscriptionResponse(
        text=result.text,
        audio_path=result.audio_path,
        latency_ms=result.latency_ms,
    )


@router.get("/memories", response_model=list[MemoryEvent])
def list_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    limit: int = 50,
) -> list[MemoryEvent]:
    return pipeline.list_memories(limit=limit)


@router.delete("/memories", response_model=MutationResult)
def clear_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MutationResult:
    return MutationResult(deleted=pipeline.clear_memories())


@router.delete("/memories/{memory_id}", response_model=MutationResult)
def delete_memory(
    memory_id: int,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MutationResult:
    return MutationResult(deleted=pipeline.delete_memory(memory_id))


@router.post("/memories/prune", response_model=MutationResult)
def prune_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    keep_latest: int = 50,
) -> MutationResult:
    return MutationResult(deleted=pipeline.prune_memories(keep_latest=keep_latest))


@router.post("/memories/dedupe", response_model=MutationResult)
def dedupe_memories(
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> MutationResult:
    return MutationResult(deleted=pipeline.dedupe_memories())


@router.get("/memories/search", response_model=list[MemoryEvent])
def search_memories(
    q: str,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
    limit: int = 20,
) -> list[MemoryEvent]:
    return pipeline.search_memories(keyword=q, limit=limit)


@router.post("/memories/rag-answer", response_model=RAGAnswerResponse)
def answer_from_memories(
    request: RAGAnswerRequest,
    pipeline: Annotated[MemoryPipeline, Depends(get_pipeline)],
) -> RAGAnswerResponse:
    result = pipeline.answer_from_memory(question=request.question, limit=request.limit)
    return RAGAnswerResponse(answer=result.answer, context_memories=result.context_memories)
