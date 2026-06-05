"""Stream handler for AI interpretation with typewriter effect.

Uses callbacks for synchronous UI updates (required by timer-driven animation)
and posts Messages (StreamDone, StreamError) for one-shot lifecycle events
where asynchronous dispatch is appropriate.
"""

from collections import deque

from rich.markdown import Markdown
from rich.text import Text

from nekomata.core.ai.interpreter import InterpretationError, StreamChunk, get_interpreter
from nekomata.core.ai.prompts import build_followup_prompt
from nekomata.core.i18n import lazy_strings as _s
from nekomata.core.render.styles import C_OVERLAY0, C_TEXT
from nekomata.tui.screens.draw_messages import StreamDone, StreamError


class StreamHandler:
    """Manages AI streaming interpretation state and typewriter rendering.

    Callbacks (synchronous, called from timer callbacks):
      render_content(parts: list | None) — update interp content; None = reset
      render_hints(text: Text) — update interp hints bar
      scroll_to_bottom() — scroll interp panel to bottom

    Messages (asynchronous, for one-shot lifecycle events):
      StreamDone — posted when streaming finishes successfully
      StreamError — posted on stream errors
    """

    def __init__(
        self,
        screen,
        render_content,
        render_hints,
        scroll_to_bottom,
    ) -> None:
        self._screen = screen
        self._render_content = render_content
        self._render_hints = render_hints
        self._scroll_to_bottom = scroll_to_bottom

        self._thinking_chars: list[str] = []
        self._content_chars: list[str] = []
        self._queue: deque[StreamChunk] = deque()
        self._timer = None
        self._source_done = False
        self._has_thinking = False
        self._has_content = False
        self._loading_timer = None
        self._loading_frame = 0
        self.messages: list[dict] = []

    def reset(self, append: bool = False) -> None:
        self._thinking_chars.clear()
        self._content_chars.clear()
        self._queue.clear()
        self._source_done = False
        self._has_thinking = False
        self._has_content = False
        if not append:
            self._render_content(None)
        self.start_loading()

    def start_loading(self) -> None:
        s = _s()
        self._loading_frame = 0
        self._tick_loading()
        self._loading_timer = self._screen.set_interval(s["loading_interval_ms"] / 1000.0, self._tick_loading)

    def _stop_loading(self) -> None:
        if self._loading_timer is not None:
            self._loading_timer.stop()
            self._loading_timer = None

    def _tick_loading(self) -> None:
        s = _s()
        frames = s["loading_frames"]
        msgs = s["loading_messages"]
        interval = s["loading_interval_ms"] / 1000.0
        msg_interval = s["loading_message_interval_s"]
        frame = frames[self._loading_frame % len(frames)]
        msg_idx = int(self._loading_frame * interval / msg_interval) % len(msgs)
        self._loading_frame += 1
        self._render_hints(Text(f"{frame} {msgs[msg_idx]}", style=C_OVERLAY0))

    def stop(self, stop_loading: bool = True) -> None:
        if stop_loading:
            self._stop_loading()
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._queue.clear()

    def append_chunk(self, chunk: StreamChunk) -> None:
        if not chunk.text:
            return
        self._queue.append(chunk)
        if self._timer is None:
            s = _s()
            self._timer = self._screen.set_interval(s["stream_tick_ms"] / 1000.0, self._tick)

    def _tick(self) -> None:
        """Typewriter tick: drain a few characters from the queue per interval."""
        if not self._queue:
            if self._source_done:
                self._finish()
                return
            self.stop(stop_loading=False)
            return

        s = _s()
        for _ in range(s["stream_chars_per_tick"]):
            if not self._queue:
                break
            chunk = self._queue[0]
            if not chunk.text:
                self._queue.popleft()
                continue
            self._append_char(chunk.kind, chunk.text[0])
            rest = chunk.text[1:]
            if rest:
                # Partially consumed — update in place
                self._queue[0] = StreamChunk(rest, chunk.kind)
            else:
                self._queue.popleft()

        self._render()
        self._scroll_to_bottom()

    def _append_char(self, kind: str, char: str) -> None:
        if kind == "thinking":
            self._thinking_chars.append(char)
            self._has_thinking = True
        else:
            self._content_chars.append(char)
            self._has_content = True

    def _render(self) -> None:
        parts = []
        if self._content_chars:
            parts.append(Markdown("".join(self._content_chars), style=C_TEXT))
        self._render_content(parts)

    def on_done(self) -> None:
        self._source_done = True
        if self._queue and self._timer is None:
            s = _s()
            self._timer = self._screen.set_interval(s["stream_tick_ms"] / 1000.0, self._tick)
            return
        if not self._queue:
            self._finish()

    def _finish(self) -> None:
        self.stop()
        self._screen.post_message(StreamDone())

    async def run(self, drawn_cards, question, cancelled_check) -> None:
        from nekomata.core.ai.interpreter import _DEFAULT_STYLE, build_messages

        config = self._screen.app.config
        lang = config.lang
        self.messages = build_messages(_DEFAULT_STYLE, question, drawn_cards, lang=lang)
        self._start_stream(
            lambda: get_interpreter(config).interpret_stream(drawn_cards, question, lang=lang),
            cancelled_check,
        )

    async def run_followup(self, messages_history: list[dict], question: str, cancelled_check) -> None:
        """Stream a follow-up interpretation using conversation history."""
        config = self._screen.app.config
        followup_msg = build_followup_prompt(question, lang=config.lang)
        messages = list(messages_history) + [{"role": "user", "content": followup_msg}]
        self.messages = list(messages)
        self._start_stream(
            lambda: get_interpreter(config).stream_raw(messages, thinking=False),
            cancelled_check,
        )

    def _start_stream(self, stream_fn_factory, cancelled_check) -> None:
        """Launch the blocking stream consumer in a Textual thread worker."""
        try:
            stream_fn = stream_fn_factory()
        except InterpretationError as exc:
            self._stop_loading()
            if self._screen.is_mounted and not cancelled_check():
                self._screen.post_message(
                    StreamError(
                        _s()["errors"]["interp_failed"].format(error=exc),
                        config_error=exc.config_error,
                    )
                )
            return
        except Exception as exc:
            self._stop_loading()
            if self._screen.is_mounted and not cancelled_check():
                self._handle_stream_error(exc, cancelled_check)
            return

        self._screen.run_worker(
            self._consume_stream(stream_fn, cancelled_check),
            thread=True,
            exclusive=True,
        )

    def _consume_stream(self, stream_fn, cancelled_check) -> None:
        """Blocking thread worker: consume stream chunks and post to main thread."""
        try:
            for chunk in stream_fn:
                if cancelled_check():
                    return
                if isinstance(chunk, str):
                    chunk = StreamChunk(chunk, "content")
                self._screen.app.call_from_thread(self.append_chunk, chunk)
        except InterpretationError as exc:
            if self._screen.is_mounted and not cancelled_check():
                self._screen.app.call_from_thread(
                    self._screen.post_message,
                    StreamError(
                        _s()["errors"]["interp_failed"].format(error=exc),
                        config_error=exc.config_error,
                    ),
                )
            return
        except Exception as exc:
            if self._screen.is_mounted and not cancelled_check():
                self._screen.app.call_from_thread(self._handle_stream_error, exc, cancelled_check)
            return
        if self._screen.is_mounted and not cancelled_check():
            self._screen.app.call_from_thread(self.on_done)

    def _handle_stream_error(self, exc: Exception, cancelled_check) -> None:
        """Map common stream errors to user-facing messages."""
        msg = str(exc).lower()
        errors = _s()["errors"]
        is_config = any(
            s in msg
            for s in (
                "api_key",
                "unauthorized",
                "nodename",
                "name or service",
                "connection refused",
                "unknown url type",
            )
        )
        if "api_key" in msg or "unauthorized" in msg:
            self._screen.post_message(StreamError(errors["api_key_missing"], config_error=True))
        else:
            self._screen.post_message(StreamError(errors["interp_failed"].format(error=exc), config_error=is_config))
