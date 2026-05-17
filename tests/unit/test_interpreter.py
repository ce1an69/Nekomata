import json
from unittest.mock import patch, MagicMock

import pytest

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.ai.interpreter import (
    OpenAIInterpreter,
    get_interpreter,
    AIInterpreter,
    InterpretationError,
)
from nekomata.storage.config import AppConfig


def make_drawn_cards(n: int, reversed_idx: set[int] | None = None) -> list[DrawnCard]:
    reversed_idx = reversed_idx or set()
    positions = [
        Position("Past", "过去", "Past influences"),
        Position("Present", "现在", "Current situation"),
        Position("Future", "未来", "Future development"),
    ]
    return [
        DrawnCard(
            card=Card(
                id=f"major_{i:02d}", name=f"Card{i}", name_zh=f"牌{i}",
                arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
                keywords_upright=(f"keyword{i}",),
                keywords_reversed=(f"keyword{i}-rev",),
                meaning_upright=f"meaning{i}",
                meaning_reversed=f"meaning{i}-rev",
            ),
            position=positions[i],
            is_reversed=(i in reversed_idx),
        )
        for i in range(n)
    ]


def _mock_urlopen(response_body: dict):
    """Create a mock for urllib.request.urlopen that returns given JSON."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_body).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_openai_interpret_success():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "AI interpretation result"}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4", api_key="test-key")
        result = interp.interpret(make_drawn_cards(2), "test question")
        assert result == "AI interpretation result"


def test_openai_sends_auth_header():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "ok"}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        interp = OpenAIInterpreter(model="gpt-4", api_key="sk-test123")
        interp.interpret(make_drawn_cards(1), "test")
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer sk-test123"


def test_get_interpreter_openai():
    config = AppConfig(ai_backend="openai", ai_model="gpt-4", ai_api_key="sk-test")
    interp = get_interpreter(config)
    assert isinstance(interp, OpenAIInterpreter)


def test_get_interpreter_openai_compatible_alias():
    config = AppConfig(ai_backend="openai_compatible", ai_model="gpt-4", ai_api_key="sk-test")
    interp = get_interpreter(config)
    assert isinstance(interp, OpenAIInterpreter)


def test_get_interpreter_missing_api_key():
    config = AppConfig(ai_backend="openai", ai_model="gpt-4", ai_api_key=None)
    with pytest.raises(InterpretationError, match="API key not configured"):
        get_interpreter(config)


def test_get_interpreter_missing_model():
    config = AppConfig(ai_backend="openai", ai_model=None, ai_api_key="sk-test")
    with pytest.raises(InterpretationError, match="AI model not configured"):
        get_interpreter(config)


def test_get_interpreter_unknown_backend():
    config = AppConfig(ai_backend="unknown", ai_model="gpt-4", ai_api_key="sk-test")
    with pytest.raises(InterpretationError, match="Unknown AI backend"):
        get_interpreter(config)


def test_openai_interpret_satisfies_protocol():
    interp = OpenAIInterpreter(model="gpt-4", api_key="test-key")
    assert isinstance(interp, AIInterpreter)


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
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is True


def test_openai_empty_choices_non_retryable():
    mock_resp = _mock_urlopen({"choices": []})
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is False


def test_openai_missing_message_key_non_retryable():
    mock_resp = _mock_urlopen({"choices": [{}]})
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is False


def test_openai_empty_content_retryable():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "   "}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="gpt-4")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is True
