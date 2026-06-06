from pathlib import Path

from ai_glasses_memory.config import get_settings, load_dotenv


def test_load_dotenv_sets_missing_environment_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_GLASSES_OCR_PROVIDER=paddleocr",
                "AI_GLASSES_VLM_PROVIDER=openai_compatible",
                "AI_GLASSES_VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
                "AI_GLASSES_VLM_MODEL=qwen3-vl-plus",
                "AI_GLASSES_VLM_MAX_IMAGE_WIDTH=768",
            ]
        ),
        encoding="utf-8",
    )
    for name in [
        "AI_GLASSES_OCR_PROVIDER",
        "AI_GLASSES_VLM_PROVIDER",
        "AI_GLASSES_VLM_BASE_URL",
        "AI_GLASSES_VLM_MODEL",
        "AI_GLASSES_VLM_MAX_IMAGE_WIDTH",
    ]:
        monkeypatch.delenv(name, raising=False)

    load_dotenv(env_file)
    settings = get_settings(env_file=None)

    assert settings.ocr_provider == "paddleocr"
    assert settings.vlm_provider == "openai_compatible"
    assert settings.vlm_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.vlm_model == "qwen3-vl-plus"
    assert settings.vlm_max_image_width == 768


def test_load_dotenv_does_not_override_existing_environment_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("AI_GLASSES_VLM_MODEL=qwen3-vl-plus\n", encoding="utf-8")
    monkeypatch.setenv("AI_GLASSES_VLM_MODEL", "manual-model")

    load_dotenv(env_file)
    settings = get_settings(env_file=None)

    assert settings.vlm_model == "manual-model"


def test_load_dotenv_ignores_comments_blank_lines_and_malformed_lines(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# local settings",
                "",
                "MALFORMED",
                "AI_GLASSES_VLM_TIMEOUT_SECONDS=45",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("AI_GLASSES_VLM_TIMEOUT_SECONDS", raising=False)

    load_dotenv(env_file)
    settings = get_settings(env_file=None)

    assert settings.vlm_timeout_seconds == 45


def test_settings_include_search_and_embedding_options(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_GLASSES_SEARCH_PROVIDER=vector",
                "AI_GLASSES_VECTOR_DB_PATH=data/test_vectors.sqlite3",
                "AI_GLASSES_EMBEDDING_PROVIDER=hash",
                "AI_GLASSES_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5",
                "AI_GLASSES_EMBEDDING_DIMENSIONS=64",
            ]
        ),
        encoding="utf-8",
    )
    for name in [
        "AI_GLASSES_SEARCH_PROVIDER",
        "AI_GLASSES_VECTOR_DB_PATH",
        "AI_GLASSES_EMBEDDING_PROVIDER",
        "AI_GLASSES_EMBEDDING_MODEL",
        "AI_GLASSES_EMBEDDING_DIMENSIONS",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings(env_file)

    assert settings.search_provider == "vector"
    assert settings.vector_db_path.as_posix() == "data/test_vectors.sqlite3"
    assert settings.embedding_provider == "hash"
    assert settings.embedding_model == "BAAI/bge-small-zh-v1.5"
    assert settings.embedding_dimensions == 64


def test_default_settings_use_chroma_rag_search(monkeypatch):
    for name in [
        "AI_GLASSES_SEARCH_PROVIDER",
        "AI_GLASSES_CHROMA_PATH",
        "AI_GLASSES_CHROMA_COLLECTION",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings(env_file=None)

    assert settings.search_provider == "chroma"
    assert settings.chroma_path.as_posix() == "data/chroma"
    assert settings.chroma_collection == "visual_memory"


def test_settings_include_chroma_vector_store_options(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_GLASSES_SEARCH_PROVIDER=chroma",
                "AI_GLASSES_CHROMA_PATH=data/chroma",
                "AI_GLASSES_CHROMA_COLLECTION=visual_memory",
            ]
        ),
        encoding="utf-8",
    )
    for name in [
        "AI_GLASSES_SEARCH_PROVIDER",
        "AI_GLASSES_CHROMA_PATH",
        "AI_GLASSES_CHROMA_COLLECTION",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings(env_file)

    assert settings.search_provider == "chroma"
    assert settings.chroma_path.as_posix() == "data/chroma"
    assert settings.chroma_collection == "visual_memory"


def test_settings_include_asr_options(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_GLASSES_ASR_PROVIDER=faster_whisper",
                "AI_GLASSES_ASR_MODEL=small",
                "AI_GLASSES_ASR_DEVICE=cpu",
                "AI_GLASSES_ASR_COMPUTE_TYPE=int8",
            ]
        ),
        encoding="utf-8",
    )
    for name in [
        "AI_GLASSES_ASR_PROVIDER",
        "AI_GLASSES_ASR_MODEL",
        "AI_GLASSES_ASR_DEVICE",
        "AI_GLASSES_ASR_COMPUTE_TYPE",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings(env_file)

    assert settings.asr_provider == "faster_whisper"
    assert settings.asr_model == "small"
    assert settings.asr_device == "cpu"
    assert settings.asr_compute_type == "int8"


def test_default_settings_use_faster_whisper_asr(monkeypatch):
    for name in [
        "AI_GLASSES_ASR_PROVIDER",
        "AI_GLASSES_ASR_MODEL",
        "AI_GLASSES_ASR_DEVICE",
        "AI_GLASSES_ASR_COMPUTE_TYPE",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings(env_file=None)

    assert settings.asr_provider == "faster_whisper"
    assert settings.asr_model == "base"
    assert settings.asr_device == "cpu"
    assert settings.asr_compute_type == "int8"


def test_settings_include_qwen_realtime_asr_options(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_GLASSES_ASR_PROVIDER=qwen_realtime",
                "AI_GLASSES_QWEN_ASR_MODEL=qwen3-asr-flash-realtime",
                "AI_GLASSES_QWEN_ASR_WS_URL=wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
                "DASHSCOPE_API_KEY=test-key",
            ]
        ),
        encoding="utf-8",
    )
    for name in [
        "AI_GLASSES_ASR_PROVIDER",
        "AI_GLASSES_QWEN_ASR_MODEL",
        "AI_GLASSES_QWEN_ASR_WS_URL",
        "DASHSCOPE_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings(env_file)

    assert settings.asr_provider == "qwen_realtime"
    assert settings.qwen_asr_model == "qwen3-asr-flash-realtime"
    assert settings.qwen_asr_ws_url == "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
    assert settings.dashscope_api_key == "test-key"
