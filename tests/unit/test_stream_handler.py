"""Unit tests for StreamHandler — typewriter effect and stream lifecycle."""

from unittest.mock import MagicMock

from nekomata.core.ai.interpreter import InterpretationError, StreamChunk
from nekomata.tui.screens.stream_handler import StreamHandler


def _make_handler() -> StreamHandler:
    screen = MagicMock()
    screen.is_mounted = True
    screen.app.config = MagicMock(lang="en")
    render_content = MagicMock()
    render_hints = MagicMock()
    scroll_to_bottom = MagicMock()
    return StreamHandler(screen, render_content, render_hints, scroll_to_bottom)


# --- _append_char tests ---


def test_append_char_thinking_filtered():
    h = _make_handler()
    h._append_char("thinking", "x")
    assert h._content_chars == []
    assert not h._has_content


def test_append_char_content_added():
    h = _make_handler()
    h._append_char("content", "H")
    assert h._content_chars == ["H"]
    assert h._has_content


# --- reset tests ---


def test_reset_clears_state():
    h = _make_handler()
    h._content_chars = ["a", "b"]
    h._has_content = True
    h.reset()
    assert h._content_chars == []
    assert not h._has_content
    h._render_content.assert_called_with(None)


# --- _handle_stream_error tests ---


def test_handle_stream_error_api_key():
    h = _make_handler()
    exc = Exception("api_key is missing")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True


def test_handle_stream_error_unauthorized():
    h = _make_handler()
    exc = Exception("401 Unauthorized")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True


def test_handle_stream_error_connection_refused():
    h = _make_handler()
    exc = Exception("Connection refused")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True  # connection refused = likely bad API URL


def test_handle_stream_error_generic():
    h = _make_handler()
    exc = Exception("something went wrong")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is False


def test_handle_stream_error_nodename():
    h = _make_handler()
    exc = Exception("nodename nor servname provided")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True


def test_handle_stream_error_name_or_service():
    h = _make_handler()
    exc = Exception("name or service not known")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True


def test_handle_stream_error_unknown_url_type():
    h = _make_handler()
    exc = Exception("unknown url type: 'htp://bad'")
    h._handle_stream_error(exc, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True


# --- on_done tests ---


def test_on_done_empty_queue_finishes():
    h = _make_handler()
    h.on_done()
    assert h._source_done is True


# --- _start_stream tests ---


def test_start_stream_interpretation_error():
    h = _make_handler()

    def bad_factory():
        raise InterpretationError("no api key", config_error=True)

    h._start_stream(bad_factory, lambda: False)
    msg = h._screen.post_message.call_args[0][0]
    assert msg.config_error is True


# --- _consume_stream tests ---


def test_consume_stream_cancelled():
    h = _make_handler()
    h._consume_stream(iter([StreamChunk("hello", "content")]), lambda: True)
    # Should not post any messages
    h._screen.app.call_from_thread.assert_not_called()


def test_consume_stream_error():
    h = _make_handler()

    def bad_gen():
        raise RuntimeError("boom")
        yield  # makes bad_gen a generator function

    h._consume_stream(bad_gen(), lambda: False)
    h._screen.app.call_from_thread.assert_called()
