"""Unit tests for _compose_copy_text from draw_interpret.py."""

from nekomata.cli.run import _draw_cards
from nekomata.tui.screens.draw_interpret import _compose_copy_text


def test_compose_copy_text_with_question_and_cards():
    drawn, _ = _draw_cards("single", seed=42)
    result = _compose_copy_text("Will I find love?", drawn, "Great things ahead.", "en")
    assert "# Will I find love?" in result
    assert "Great things ahead." in result
    # Should contain card entry with status
    assert "- " in result


def test_compose_copy_text_empty_question():
    drawn, _ = _draw_cards("single", seed=42)
    result = _compose_copy_text("", drawn, "Interpretation text.", "en")
    assert "# " not in result
    assert "Interpretation text." in result


def test_compose_copy_text_multiple_cards():
    drawn, _ = _draw_cards("past_present_future", seed=42)
    result = _compose_copy_text("My question", drawn, "The reading says...", "en")
    # Should have 3 card entries (one per drawn card)
    lines = [l for l in result.split("\n") if l.startswith("- ")]
    assert len(lines) == 3


def test_compose_copy_text_zh_lang():
    drawn, _ = _draw_cards("single", seed=42)
    result = _compose_copy_text("测试问题", drawn, "解读内容", "zh")
    assert "测试问题" in result
    assert "解读内容" in result
