from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ASRProvider(Protocol):
    def transcribe(self, audio_path: str) -> str:
        ...


@dataclass(frozen=True)
class ASRResult:
    text: str
    audio_path: str
    latency_ms: dict[str, float]


class MockASRProvider:
    def transcribe(self, audio_path: str) -> str:
        return "我刚才看到了什么？"


class QwenRealtimeASRProvider:
    def transcribe(self, audio_path: str) -> str:
        raise RuntimeError(
            "Qwen-ASR-Realtime is a streaming provider. Use the /live/asr/ws WebSocket route."
        )


class FasterWhisperASRProvider:
    def __init__(
        self,
        model_name: str = "base",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def _get_model(self):
        if self.model is not None:
            return self.model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Install the ASR optional dependency first."
            ) from exc

        self.model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )
        return self.model

    def transcribe(self, audio_path: str) -> str:
        segments, _info = self._get_model().transcribe(audio_path)
        text = "".join(segment.text for segment in segments).strip()
        return text


def create_asr_provider(
    provider: str,
    *,
    model_name: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
) -> ASRProvider:
    normalized = provider.strip().lower()
    if normalized in {"", "mock"}:
        return MockASRProvider()
    if normalized in {"qwen_realtime", "qwen-realtime", "qwen_asr_realtime"}:
        return QwenRealtimeASRProvider()
    if normalized in {"faster_whisper", "faster-whisper"}:
        return FasterWhisperASRProvider(
            model_name,
            device=device,
            compute_type=compute_type,
        )
    raise ValueError(f"Unsupported ASR provider: {provider}")
