"""Tests for AI prompt templates."""

from nekomata.ai.prompts import SYSTEM_PROMPT, build_interpretation_prompt


def test_system_prompt_has_style_placeholder():
    assert "{style}" in SYSTEM_PROMPT


def test_system_prompt_mentions_cat():
    assert "猫" in SYSTEM_PROMPT or "猫咪" in SYSTEM_PROMPT


def test_build_interpretation_prompt_includes_question():
    result = build_interpretation_prompt("今天运势如何？", "牌面信息")
    assert "今天运势如何？" in result
    assert "牌面信息" in result


def test_build_interpretation_prompt_asks_for_analysis():
    result = build_interpretation_prompt("测试", "测试牌")
    assert "解读" in result


def test_system_prompt_requests_markdown():
    assert "Markdown" in SYSTEM_PROMPT


def test_build_interpretation_prompt_requests_synthesis():
    result = build_interpretation_prompt("测试", "测试牌")
    assert "综合" in result
