"""Unit tests for StreamHandler — typewriter effect and stream lifecycle."""

from unittest.mock import MagicMock, patch

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


def test_reset_append_keeps_existing_content_rendered():
    h = _make_handler()
    h._content_chars = ["a"]
    h._has_content = True
    h.reset(append=True)
    assert h._content_chars == []
    h._render_content.assert_not_called()


def test_start_and_stop_loading_timer():
    h = _make_handler()
    timer = MagicMock()
    h._screen.set_interval.return_value = timer

    h.start_loading()
    assert h._loading_timer is timer
    assert h._render_hints.called

    h._stop_loading()
    timer.stop.assert_called_once()
    assert h._loading_timer is None


def test_stop_stops_stream_timer_and_clears_queue():
    h = _make_handler()
    timer = MagicMock()
    loading_timer = MagicMock()
    h._timer = timer
    h._loading_timer = loading_timer
    h._queue.append(StreamChunk("x", "content"))

    h.stop()

    timer.stop.assert_called_once()
    loading_timer.stop.assert_called_once()
    assert h._timer is None
    assert h._loading_timer is None
    assert list(h._queue) == []


def test_append_chunk_ignores_empty_text():
    h = _make_handler()
    h.append_chunk(StreamChunk("", "content"))
    assert list(h._queue) == []
    h._screen.set_interval.assert_not_called()


def test_append_chunk_starts_typewriter_timer_once():
    h = _make_handler()
    timer = MagicMock()
    h._screen.set_interval.return_value = timer

    h.append_chunk(StreamChunk("hi", "content"))
    h.append_chunk(StreamChunk("!", "content"))

    assert list(h._queue) == [StreamChunk("hi", "content"), StreamChunk("!", "content")]
    h._screen.set_interval.assert_called_once()
    assert h._timer is timer


def test_tick_drains_content_and_scrolls():
    h = _make_handler()
    h._queue.append(StreamChunk("hi", "content"))

    h._tick()

    assert h._content_chars == ["h", "i"]
    assert h._has_content is True
    h._render_content.assert_called_once()
    h._scroll_to_bottom.assert_called_once()


def test_tick_ignores_thinking_but_removes_chunk():
    h = _make_handler()
    h._queue.append(StreamChunk("h", "thinking"))

    h._tick()

    assert h._content_chars == []
    assert list(h._queue) == []
    h._render_content.assert_called_once_with([])


def test_tick_discards_empty_queued_chunk():
    h = _make_handler()
    h._queue.append(StreamChunk("", "content"))
    h._queue.append(StreamChunk("x", "content"))

    h._tick()

    assert h._content_chars == ["x"]
    assert list(h._queue) == []


def test_tick_without_queue_stops_timer_until_source_done():
    h = _make_handler()
    timer = MagicMock()
    h._timer = timer

    h._tick()

    timer.stop.assert_called_once()
    assert h._timer is None


def test_tick_without_queue_finishes_when_source_done():
    h = _make_handler()
    h._source_done = True

    h._tick()

    msg = h._screen.post_message.call_args.args[0]
    assert msg.__class__.__name__ == "StreamDone"


def test_on_done_restarts_timer_when_queue_has_pending_content():
    h = _make_handler()
    timer = MagicMock()
    h._screen.set_interval.return_value = timer
    h._queue.append(StreamChunk("x", "content"))
    h._timer = None

    h.on_done()

    assert h._source_done is True
    assert h._timer is timer
    h._screen.post_message.assert_not_called()


def test_run_builds_messages_and_starts_interpretation_stream():
    h = _make_handler()
    drawn_cards = [MagicMock()]
    cancelled = MagicMock()
    stream = iter([StreamChunk("x", "content")])
    interpreter = MagicMock()
    interpreter.interpret_stream.return_value = stream

    with (
        patch("nekomata.tui.screens.stream_handler.get_interpreter", return_value=interpreter),
        patch.object(h, "_start_stream") as start_stream,
    ):
        h.run(drawn_cards, "question", cancelled)
        factory = start_stream.call_args.args[0]
        assert factory() is stream

    assert h.messages[0]["role"] == "system"
    assert h.messages[1]["role"] == "user"
    assert start_stream.call_args.args[1] is cancelled
    interpreter.interpret_stream.assert_called_once_with(drawn_cards, "question", lang="en")


def test_run_followup_appends_prompt_and_starts_raw_stream():
    h = _make_handler()
    history = [{"role": "assistant", "content": "Initial"}]
    cancelled = MagicMock()
    stream = iter([StreamChunk("x", "content")])
    interpreter = MagicMock()
    interpreter.stream_raw.return_value = stream

    with (
        patch("nekomata.tui.screens.stream_handler.get_interpreter", return_value=interpreter),
        patch.object(h, "_start_stream") as start_stream,
    ):
        h.run_followup(history, "clarify", cancelled)
        factory = start_stream.call_args.args[0]
        assert factory() is stream

    assert h.messages[0] == history[0]
    assert h.messages[-1]["role"] == "user"
    assert "clarify" in h.messages[-1]["content"]
    assert start_stream.call_args.args[1] is cancelled
    interpreter.stream_raw.assert_called_once_with(h.messages, thinking=False)


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


def test_start_stream_generic_factory_error_is_handled():
    h = _make_handler()

    def bad_factory():
        raise RuntimeError("boom")

    h._start_stream(bad_factory, lambda: False)

    msg = h._screen.post_message.call_args[0][0]
    assert "boom" in msg.message


def test_start_stream_error_ignored_when_cancelled():
    h = _make_handler()

    def bad_factory():
        raise InterpretationError("no api key", config_error=True)

    h._start_stream(bad_factory, lambda: True)

    h._screen.post_message.assert_not_called()


def test_start_stream_defers_consumption_to_worker():
    h = _make_handler()
    consumed = False

    def stream():
        nonlocal consumed
        consumed = True
        yield StreamChunk("hello", "content")

    h._start_stream(stream, lambda: False)

    run_worker_call = h._screen.run_worker.call_args
    work = run_worker_call.args[0]

    assert callable(work)
    assert run_worker_call.kwargs["thread"] is True
    assert run_worker_call.kwargs["exclusive"] is True
    assert consumed is False
    h._screen.app.call_from_thread.assert_not_called()

    work()

    assert consumed is True
    h._screen.app.call_from_thread.assert_called()


# --- _consume_stream tests ---


def test_consume_stream_cancelled():
    h = _make_handler()
    h._consume_stream(iter([StreamChunk("hello", "content")]), lambda: True)
    # Should not post any messages
    h._screen.app.call_from_thread.assert_not_called()


def test_consume_stream_converts_plain_strings_and_posts_done():
    h = _make_handler()
    h._consume_stream(iter(["hello"]), lambda: False)

    first_call = h._screen.app.call_from_thread.call_args_list[0]
    assert first_call.args[0] == h.append_chunk
    assert first_call.args[1] == StreamChunk("hello", "content")
    assert h._screen.app.call_from_thread.call_args_list[-1].args[0] == h.on_done


def test_consume_stream_interpretation_error_posts_stream_error():
    h = _make_handler()

    def bad_gen():
        raise InterpretationError("provider failed", config_error=True)
        yield

    h._consume_stream(bad_gen(), lambda: False)

    callback, message = h._screen.app.call_from_thread.call_args.args
    assert callback == h._screen.post_message
    assert message.config_error is True
    assert "provider failed" in message.message


def test_consume_stream_errors_ignored_when_unmounted_or_cancelled():
    h = _make_handler()
    h._screen.is_mounted = False

    def bad_gen():
        raise RuntimeError("boom")
        yield

    h._consume_stream(bad_gen(), lambda: False)
    h._screen.app.call_from_thread.assert_not_called()

    h = _make_handler()
    h._consume_stream(bad_gen(), lambda: True)
    h._screen.app.call_from_thread.assert_not_called()


def test_consume_stream_error():
    h = _make_handler()

    def bad_gen():
        raise RuntimeError("boom")
        yield  # makes bad_gen a generator function

    h._consume_stream(bad_gen(), lambda: False)
    h._screen.app.call_from_thread.assert_called()
