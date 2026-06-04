from pathlib import Path

from ai_glasses_memory.services.vlm import (
    MockVLMProvider,
    OpenAICompatibleVLMProvider,
    create_vlm_provider,
)


def test_create_vlm_provider_defaults_to_mock():
    provider = create_vlm_provider("mock")

    assert isinstance(provider, MockVLMProvider)
    assert "VLM" in provider.answer_question("What is here?", "OCR text", None)


def test_unknown_vlm_provider_falls_back_to_mock():
    provider = create_vlm_provider("unknown")

    assert isinstance(provider, MockVLMProvider)


def test_openai_compatible_provider_requires_connection_settings():
    provider = create_vlm_provider(
        "openai_compatible",
        base_url="",
        api_key="",
        model="",
    )

    assert isinstance(provider, MockVLMProvider)


def test_openai_compatible_provider_sends_text_and_image_payload(tmp_path):
    image_path = tmp_path / "frame.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    )
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "real vlm answer"}}]}

    class FakeHttpClient:
        def post(self, url, headers, json, timeout):
            calls.append(
                {
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "timeout": timeout,
                }
            )
            return FakeResponse()

    provider = OpenAICompatibleVLMProvider(
        base_url="https://example.com/v1/",
        api_key="secret",
        model="qwen-vl",
        http_client=FakeHttpClient(),
        max_tokens=128,
        timeout_seconds=9,
    )

    answer = provider.answer_question(
        question="What text is visible?",
        ocr_text="OCR text",
        image_path=str(image_path),
    )

    assert answer == "real vlm answer"
    assert calls[0]["url"] == "https://example.com/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer secret"
    assert calls[0]["timeout"] == 9
    payload = calls[0]["json"]
    assert payload["model"] == "qwen-vl"
    assert payload["max_tokens"] == 128
    user_content = payload["messages"][1]["content"]
    assert user_content[0]["type"] == "text"
    assert "OCR text" in user_content[0]["text"]
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"].startswith("data:image/")
    assert user_content[1]["image_url"]["detail"] == "low"


def test_openai_compatible_provider_compresses_large_image_payload(tmp_path):
    from PIL import Image

    image_path = tmp_path / "large.png"
    Image.new("RGB", (2000, 1000), color=(240, 240, 240)).save(image_path)

    provider = OpenAICompatibleVLMProvider(
        base_url="https://example.com/v1/",
        api_key="secret",
        model="qwen-vl",
        max_image_width=512,
    )

    data_url = provider._image_to_data_url(str(image_path))

    assert data_url is not None
    assert data_url.startswith("data:image/jpeg;base64,")
    assert len(data_url) < image_path.stat().st_size


def test_openai_compatible_provider_falls_back_on_http_error():
    class FailingHttpClient:
        def post(self, url, headers, json, timeout):
            raise RuntimeError("network down")

    provider = OpenAICompatibleVLMProvider(
        base_url="https://example.com/v1",
        api_key="secret",
        model="qwen-vl",
        http_client=FailingHttpClient(),
        fallback=MockVLMProvider(),
    )

    answer = provider.answer_question("Question", "OCR text", "missing.jpg")

    assert "VLM" in answer
    assert "OCR text" in answer


def test_openai_compatible_provider_logs_fallback_reason(caplog):
    class FailingHttpClient:
        def post(self, url, headers, json, timeout):
            raise RuntimeError("network down")

    provider = OpenAICompatibleVLMProvider(
        base_url="https://example.com/v1",
        api_key="secret",
        model="qwen-vl",
        http_client=FailingHttpClient(),
        fallback=MockVLMProvider(),
    )

    answer = provider.answer_question("Question", "OCR text", "missing.jpg")

    assert "VLM" in answer
    assert "VLM provider fell back to mock" in caplog.text
    assert "network down" in caplog.text
    assert "secret" not in caplog.text


def test_openai_compatible_provider_uses_text_only_payload_when_image_is_missing():
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "text only answer"}}]}

    class FakeHttpClient:
        def post(self, url, headers, json, timeout):
            calls.append(json)
            return FakeResponse()

    provider = OpenAICompatibleVLMProvider(
        base_url="https://example.com/v1",
        api_key="secret",
        model="qwen-vl",
        http_client=FakeHttpClient(),
    )

    answer = provider.answer_question("Question", "OCR text", None)

    assert answer == "text only answer"
    assert calls[0]["messages"][1]["content"][0]["type"] == "text"
    assert len(calls[0]["messages"][1]["content"]) == 1
