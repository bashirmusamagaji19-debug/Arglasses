from ai_glasses_memory.services.ocr import (
    MockOCRProvider,
    PaddleOCRProvider,
    create_ocr_provider,
)


def test_create_ocr_provider_defaults_to_mock():
    provider = create_ocr_provider("mock")

    assert isinstance(provider, MockOCRProvider)
    assert "模拟 OCR" in provider.extract_text(None)


def test_unknown_ocr_provider_falls_back_to_mock():
    provider = create_ocr_provider("unknown")

    assert isinstance(provider, MockOCRProvider)


def test_paddleocr_provider_falls_back_when_package_is_unavailable():
    provider = PaddleOCRProvider(
        fallback=MockOCRProvider(),
        paddleocr_class_loader=lambda: (_ for _ in ()).throw(ModuleNotFoundError("paddleocr")),
    )

    text = provider.extract_text("assets/samples/default.txt")

    assert "模拟 OCR" in text


def test_paddleocr_provider_flattens_paddleocr_3_predict_result():
    class FakePaddleOCR:
        def __init__(self, *args, **kwargs):
            assert kwargs["use_doc_orientation_classify"] is False
            assert kwargs["use_doc_unwarping"] is False
            assert kwargs["use_textline_orientation"] is False

        def predict(self, image_path):
            assert image_path == "image.jpg"
            return [{"rec_texts": ["第一行", "second line"]}]

    provider = PaddleOCRProvider(
        fallback=MockOCRProvider(),
        paddleocr_class_loader=lambda: FakePaddleOCR,
    )

    assert provider.extract_text("image.jpg") == "PaddleOCR：第一行\nsecond line"


def test_paddleocr_provider_still_parses_legacy_ocr_result_shape():
    legacy_result = [
        [
            [[[0, 0], [1, 0], [1, 1], [0, 1]], ("第一行", 0.99)],
            [[[0, 2], [1, 2], [1, 3], [0, 3]], ("second line", 0.95)],
        ]
    ]

    assert PaddleOCRProvider._extract_lines(legacy_result) == ["第一行", "second line"]
