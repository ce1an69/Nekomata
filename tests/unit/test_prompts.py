"""Tests for AI prompt templates."""

from nekomata.ai.prompts import load_system_prompt, load_spread_prompt, build_user_prompt


def test_system_prompt_has_style_placeholder():
    assert "{style}" in load_system_prompt()


def test_system_prompt_requests_markdown():
    assert "Markdown" in load_system_prompt()


def test_load_spread_prompt_returns_content():
    for key in ("single", "past_present_future", "five_card_cross"):
        content = load_spread_prompt(key)
        assert len(content) > 0


def test_load_spread_prompt_missing_key_returns_empty():
    assert load_spread_prompt("nonexistent") == ""


def test_build_user_prompt_includes_question():
    result = build_user_prompt("今天运势如何？", "牌面信息")
    assert "今天运势如何？" in result
    assert "牌面信息" in result


def test_build_user_prompt_asks_for_analysis():
    result = build_user_prompt("测试", "测试牌")
    assert "解读" in result


def test_build_user_prompt_requests_synthesis():
    result = build_user_prompt("测试", "测试牌")
    assert "综合" in result
