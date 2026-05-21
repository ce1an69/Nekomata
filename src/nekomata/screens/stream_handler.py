"""Stream handler for AI interpretation with typewriter effect."""

import asyncio
import json
from collections import deque
from pathlib import Path

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

from nekomata.ai.interpreter import InterpretationError, StreamChunk, get_interpreter

STREAM_TYPE_INTERVAL = 0.025
STREAM_CHARS_PER_TICK = 3

_UI_STRINGS = json.loads(
    (Path(__file__).resolve().parents[3] / "data" / "ui_strings.json").read_text(encoding="utf-8")
)
_LOADING_FRAMES = tuple(_UI_STRINGS["loading_frames"])
_LOADING_INTERVAL = _UI_STRINGS["loading_interval_ms"] / 1000.0
_LOADING_MESSAGE_INTERVAL = _UI_STRINGS["loading_message_interval_s"]
_LOADING_MESSAGES = tuple(_UI_STRINGS["loading_messages"])


class StreamHandler:
    """Manages AI streaming interpretation state and typewriter rendering.

    Callbacks:
      render_content(parts: list | None) — update interp content; None = reset
      render_hints(text: Text) — update interp hints bar
      scroll_to_bottom() — scroll interp panel to bottom
      show_error(message: str) — hide dialog and show error
    """

    def __init__(
        self,
        screen,
        render_content,
        render_hints,
        scroll_to_bottom,
        show_error,
    ) -> None:
        self._screen = screen
        self._render_content = render_content
        self._render_hints = render_hints
        self._scroll_to_bottom = scroll_to_bottom
        self._show_error = show_error

        self.streaming = False
        self._thinking_text = ""
        self._content_text = ""
        self._queue: deque[StreamChunk] = deque()
        self._timer = None
        self._source_done = False
        self._has_thinking = False
        self._has_content = False
        self._loading_timer = None
        self._loading_frame = 0

    def reset(self) -> None:
        self._thinking_text = ""
        self._content_text = ""
        self._queue.clear()
        self._source_done = False
        self._has_thinking = False
        self._has_content = False
        self._render_content(None)
        self.start_loading()

    def start_loading(self) -> None:
        self._loading_frame = 0
        self._tick_loading()
        self._loading_timer = self._screen.set_interval(
            _LOADING_INTERVAL, self._tick_loading
        )

    def _stop_loading(self) -> None:
        if self._loading_timer is not None:
            self._loading_timer.stop()
            self._loading_timer = None

    def _tick_loading(self) -> None:
        from nekomata.render.styles import C_OVERLAY0

        frame = _LOADING_FRAMES[self._loading_frame % len(_LOADING_FRAMES)]
        msg_idx = int(
            self._loading_frame * _LOADING_INTERVAL / _LOADING_MESSAGE_INTERVAL
        ) % len(_LOADING_MESSAGES)
        self._loading_frame += 1
        self._render_hints(Text(f"{frame} {_LOADING_MESSAGES[msg_idx]}", style=C_OVERLAY0))

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
            self._timer = self._screen.set_interval(
                STREAM_TYPE_INTERVAL, self._tick
            )

    def _tick(self) -> None:
        if not self._queue:
            if self._source_done:
                self._finish()
                return
            self.stop(stop_loading=False)
            return

        for _ in range(STREAM_CHARS_PER_TICK):
            if not self._queue:
                break
            chunk = self._queue[0]
            if not chunk.text:
                self._queue.popleft()
                continue
            self._append_char(chunk.kind, chunk.text[0])
            rest = chunk.text[1:]
            if rest:
                self._queue[0] = StreamChunk(rest, chunk.kind)
            else:
                self._queue.popleft()

        self._render()
        self._scroll_to_bottom()

    def _append_char(self, kind: str, char: str) -> None:
        if kind == "thinking":
            self._thinking_text += char
            self._has_thinking = True
        else:
            self._content_text += char
            self._has_content = True

    def _render(self) -> None:
        from nekomata.render.styles import C_MAUVE, C_OVERLAY0, C_TEXT

        parts = []
        if self._thinking_text:
            style = f"italic dim {C_OVERLAY0}"
            parts.append(Text("思考", style=f"bold {style}"))
            parts.append(Text(self._thinking_text, style=style))
        if self._content_text:
            if parts:
                parts.append(Text(""))
            parts.append(Text("解读", style=f"bold {C_MAUVE}"))
            parts.append(Markdown(self._content_text, style=C_TEXT))
        self._render_content(parts)

    def on_done(self) -> None:
        self._source_done = True
        if self._queue and self._timer is None:
            self._timer = self._screen.set_interval(
                STREAM_TYPE_INTERVAL, self._tick
            )
            return
        if not self._queue:
            self._finish()

    def _finish(self) -> None:
        from nekomata.render.styles import C_OVERLAY0

        self.stop()
        self.streaming = False
        self._render_hints(Text("── 完成 ──  Q 关闭", style=C_OVERLAY0))

    async def run(self, drawn_cards, question, cancelled_check) -> None:
        try:
            config = self._screen.app.config
            interp = get_interpreter(config)
            loop = asyncio.get_running_loop()

            def _consume():
                for chunk in interp.interpret_stream(drawn_cards, question):
                    if cancelled_check():
                        return
                    if isinstance(chunk, str):
                        chunk = StreamChunk(chunk, "content")
                    self._screen.app.call_from_thread(self.append_chunk, chunk)

            await loop.run_in_executor(None, _consume)
        except InterpretationError as exc:
            if not self._screen.is_mounted or cancelled_check():
                return
            self._show_error(f"解读失败: {exc}")
            return
        except Exception as exc:
            if not self._screen.is_mounted or cancelled_check():
                return
            msg = str(exc)
            if "api_key" in msg.lower() or "unauthorized" in msg.lower():
                self._show_error("API key 未配置，请在 .neko/settings.json 中设置 api_key")
            else:
                self._show_error(f"解读失败: {exc}")
            return
        if not self._screen.is_mounted or cancelled_check():
            return
        self.on_done()
