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


class FasterWhisperASRProvider:
    def __init__(
        self,
        model_name: str = "base",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Install the ASR optional dependency first."
            ) from exc

        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> str:
        segments, _info = self.model.transcribe(audio_path)
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
    if normalized in {"faster_whisper", "faster-whisper"}:
        return FasterWhisperASRProvider(
            model_name,
            device=device,
            compute_type=compute_type,
        )
    raise ValueError(f"Unsupported ASR provider: {provider}")
