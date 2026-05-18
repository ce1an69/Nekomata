import json
from unittest.mock import patch, MagicMock

import pytest

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.ai.interpreter import (
    OpenAIInterpreter,
    StreamChunk,
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
        interp = OpenAIInterpreter(model="test-model", api_key="test-key")
        result = interp.interpret(make_drawn_cards(2), "test question")
        assert result == "AI interpretation result"


def test_openai_sends_auth_header():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "ok"}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        interp = OpenAIInterpreter(model="test-model", api_key="sk-test123")
        interp.interpret(make_drawn_cards(1), "test")
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer sk-test123"


def test_get_interpreter_returns_openai():
    config = AppConfig(api_key="sk-test")
    interp = get_interpreter(config)
    assert isinstance(interp, OpenAIInterpreter)


def test_get_interpreter_missing_api_key():
    config = AppConfig(api_key=None)
    with pytest.raises(InterpretationError, match="API key not configured"):
        get_interpreter(config)


def test_openai_interpret_satisfies_protocol():
    interp = OpenAIInterpreter(model="test-model", api_key="test-key")
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
        interp = OpenAIInterpreter(model="test-model")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is True


def test_openai_empty_choices_non_retryable():
    mock_resp = _mock_urlopen({"choices": []})
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="test-model")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is False


def test_openai_missing_message_key_non_retryable():
    mock_resp = _mock_urlopen({"choices": [{}]})
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="test-model")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is False


def test_openai_empty_content_retryable():
    mock_resp = _mock_urlopen({
        "choices": [{"message": {"content": "   "}}]
    })
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="test-model")
        with pytest.raises(InterpretationError) as exc_info:
            interp.interpret(make_drawn_cards(1), "test")
        assert exc_info.value.retryable is True


def _mock_stream_urlopen(sse_lines: list[str]):
    """Create a mock for urllib.request.urlopen that returns SSE lines."""
    mock_resp = MagicMock()
    mock_resp.__iter__ = MagicMock(return_value=iter(line.encode() + b"\n" for line in sse_lines))
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_interpret_stream_yields_chunks():
    sse_lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        'data: [DONE]',
    ]
    mock_resp = _mock_stream_urlopen(sse_lines)
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="test-model", api_key="test-key")
        chunks = list(interp.interpret_stream(make_drawn_cards(1), "test"))
    assert chunks == [StreamChunk("Hello"), StreamChunk(" world")]


def test_interpret_stream_skips_empty_delta():
    sse_lines = [
        'data: {"choices":[{"delta":{"content":"Hi"}}]}',
        'data: {"choices":[{"delta":{}}]}',
        'data: {"choices":[{"delta":{"content":"!"}}]}',
        'data: [DONE]',
    ]
    mock_resp = _mock_stream_urlopen(sse_lines)
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="test-model", api_key="test-key")
        chunks = list(interp.interpret_stream(make_drawn_cards(1), "test"))
    assert chunks == [StreamChunk("Hi"), StreamChunk("!")]


def test_interpret_stream_yields_reasoning_chunks():
    sse_lines = [
        'data: {"choices":[{"delta":{"reasoning_content":"Thinking"}}]}',
        'data: {"choices":[{"delta":{"content":"Answer"}}]}',
        'data: [DONE]',
    ]
    mock_resp = _mock_stream_urlopen(sse_lines)
    with patch("nekomata.ai.interpreter.urllib.request.urlopen", return_value=mock_resp):
        interp = OpenAIInterpreter(model="test-model", api_key="test-key")
        chunks = list(interp.interpret_stream(make_drawn_cards(1), "test"))
    assert chunks == [StreamChunk("Thinking", "thinking"), StreamChunk("Answer")]


def test_interpret_stream_failure_raises():
    import urllib.error
    with patch("nekomata.ai.interpreter.urllib.request.urlopen",
               side_effect=urllib.error.URLError("timeout")):
        interp = OpenAIInterpreter(model="test-model")
        with pytest.raises(InterpretationError) as exc_info:
            list(interp.interpret_stream(make_drawn_cards(1), "test"))
        assert exc_info.value.retryable is True
