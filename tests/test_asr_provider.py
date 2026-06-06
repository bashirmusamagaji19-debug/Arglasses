import pytest

from ai_glasses_memory.services.asr import (
    MockASRProvider,
    create_asr_provider,
)


def test_mock_asr_provider_returns_stable_transcription(tmp_path):
    audio_path = tmp_path / "question.wav"
    audio_path.write_bytes(b"fake audio")

    provider = MockASRProvider()

    assert provider.transcribe(str(audio_path)) == "我刚才看到了什么？"


def test_create_asr_provider_defaults_to_mock():
    provider = create_asr_provider("mock")

    assert isinstance(provider, MockASRProvider)


def test_create_asr_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported ASR provider"):
        create_asr_provider("unknown")


def test_faster_whisper_provider_reports_missing_optional_dependency(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("missing faster_whisper")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="faster-whisper is not installed"):
        create_asr_provider("faster_whisper")
