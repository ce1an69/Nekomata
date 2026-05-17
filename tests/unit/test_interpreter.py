import json
from unittest.mock import patch, MagicMock

import pytest

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.ai.interpreter import (
    template_interpret,
    OpenAIInterpreter,
    get_interpreter,
    TemplateFallback,
    AIInterpreter,
    InterpretationError,
)
from nekomata.storage.config import AppConfig


def make_drawn_cards(n: int, reversed_idx: set[int] | None = None) -> list[DrawnCard]:
    reversed_idx = reversed_idx or set()
    positions = [
        Position("Past", "过去", "过去的影响"),
        Position("Present", "现在", "当前状况"),
        Position("Future", "未来", "未来发展"),
    ]
    return [
        DrawnCard(
            card=Card(
                id=f"major_{i:02d}", name=f"Card{i}", name_zh=f"牌{i}",
                arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
                keywords_upright=(f"正位关键词{i}",),
                keywords_reversed=(f"逆位关键词{i}",),
                meaning_upright=f"正位含义{i}",
                meaning_reversed=f"逆位含义{i}",
            ),
            position=positions[i],
            is_reversed=(i in reversed_idx),
        )
        for i in range(n)
    ]


def test_template_interpret_contains_question():
    assert "今天运势如何？" in template_interpret(make_drawn_cards(1), "今天运势如何？")


def test_template_interpret_single_card():
    result = template_interpret(make_drawn_cards(1), "test")
    assert "牌0" in result
    assert "正位关键词0" in result


def test_template_interpret_reversed():
    result = template_interpret(make_drawn_cards(3, reversed_idx={1}), "test")
    assert "逆位" in result
    assert "逆位关键词1" in result


def test_template_interpret_three_cards():
    result = template_interpret(make_drawn_cards(3), "三牌阵测试")
    assert "过去" in result
    assert "现在" in result
    assert "未来" in result


def test_template_interpret_includes_position_description():
    result = template_interpret(make_drawn_cards(1), "测试")
    assert "过去的影响" in result


def test_template_interpret_multi_card_has_summary():
    """Multi-card template interpretation includes an overall summary section."""
    result = template_interpret(make_drawn_cards(3), "总结测试")
    assert "综合概述" in result
    assert "正位" in result
    assert "主题关键词" in result


def test_template_interpret_all_reversed_summary():
    """All-reversed draw mentions challenges in summary."""
    result = template_interpret(make_drawn_cards(3, reversed_idx={0, 1, 2}), "全逆位")
    assert "挑战" in result


def test_template_interpret_single_card_no_summary():
    """Single-card draw should not include the multi-card summary section."""
    result = template_interpret(make_drawn_cards(1), "单牌测试")
    assert "综合概述" not in result


def test_template_fallback_satisfies_protocol():
    fb = TemplateFallback()
    assert isinstance(fb, AIInterpreter)


def test_template_fallback_output():
    fb = TemplateFallback()
    result = fb.interpret(make_drawn_cards(1), "test")
    assert "牌0" in result


def _mock_urlopen(response_body: dict):
    """Create a mock for urllib.request.urlopen that returns given JSON."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_body).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_openai_interpret_success():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "OpenAI解读内容"}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4", api_key="test-key")
        result = interp.interpret(make_drawn_cards(2), "问题")
        assert result == "OpenAI解读内容"


def test_openai_sends_auth_header():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "ok"}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        interp = OpenAIInterpreter(model="gpt-4", api_key="sk-test123")
        interp.interpret(make_drawn_cards(1), "test")
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer sk-test123"


def test_get_interpreter_template():
    config = AppConfig(ai_backend="template")
    interp = get_interpreter(config)
    assert isinstance(interp, TemplateFallback)


def test_get_interpreter_openai():
    config = AppConfig(ai_backend="openai", ai_model="gpt-4", ai_api_key="sk-test")
    interp = get_interpreter(config)
    assert isinstance(interp, OpenAIInterpreter)


def test_get_interpreter_openai_compatible_alias():
    config = AppConfig(ai_backend="openai_compatible", ai_model="gpt-4", ai_api_key="sk-test")
    interp = get_interpreter(config)
    assert isinstance(interp, OpenAIInterpreter)


def test_interpretation_error_retryable():
    err = InterpretationError("timeout", retryable=True)
    assert err.retryable is True
    assert "timeout" in str(err)


def test_interpretation_error_not_retryable():
    err = InterpretationError("bad response", retryable=False)
    assert err.retryable is False


def test_openai_interpret_failure_raises():
    import urllib.error
    with patch("nekomata.ai.interpreter.urllib.request.urlopen",
               side_effect=urllib.error.URLError("connection refused")):
        interp = OpenAIInterpreter(model="gpt-4")
        try:
            interp.interpret(make_drawn_cards(1), "test")
            assert False, "Should have raised"
        except InterpretationError as e:
            assert e.retryable is True


def test_openai_empty_choices_non_retryable():
    """Empty choices list triggers non-retryable error."""
    mock_resp = _mock_urlopen({"choices": []})
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4")
        try:
            interp.interpret(make_drawn_cards(1), "test")
            assert False, "Should have raised"
        except InterpretationError as e:
            assert e.retryable is False


def test_openai_missing_message_key_non_retryable():
    """Response with missing 'message' key triggers non-retryable error."""
    mock_resp = _mock_urlopen({"choices": [{}]})
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4")
        try:
            interp.interpret(make_drawn_cards(1), "test")
            assert False, "Should have raised"
        except InterpretationError as e:
            assert e.retryable is False


def test_openai_empty_content_retryable():
    """API returning empty content string triggers retryable error."""
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "   "}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4")
        try:
            interp.interpret(make_drawn_cards(1), "test")
            assert False, "Should have raised"
        except InterpretationError as e:
            assert e.retryable is True
