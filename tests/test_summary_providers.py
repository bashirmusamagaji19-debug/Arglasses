from ai_glasses_memory.services.summary import RuleBasedSummaryProvider, create_summary_provider


def test_create_summary_provider_defaults_to_rule_based():
    provider = create_summary_provider("rule_based")

    summary = provider.summarize_scene(
        question="手上是什么？",
        answer="手上拿的是一个黑色无线鼠标。",
        ocr_text="OCR：无明显文字",
    )

    assert "用户提问：手上是什么？" in summary
    assert "视觉回答：手上拿的是一个黑色无线鼠标。" in summary
    assert "模拟场景摘要" not in summary


def test_unknown_summary_provider_falls_back_to_rule_based():
    provider = create_summary_provider("unknown")

    assert isinstance(provider, RuleBasedSummaryProvider)


def test_rule_based_summary_omits_empty_ocr_text():
    provider = RuleBasedSummaryProvider()

    summary = provider.summarize_scene(
        question="手上是什么？",
        answer="手上拿的是一个黑色无线鼠标。",
        ocr_text="",
    )

    assert "OCR 文字" not in summary
    assert "视觉回答：手上拿的是一个黑色无线鼠标。" in summary
