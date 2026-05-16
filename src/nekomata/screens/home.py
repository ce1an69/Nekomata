from __future__ import annotations

from textual.containers import Center, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Input, Static


BANNER_LINES = [
    "███╗   ██╗███████╗██╗  ██╗ ██████╗ ███╗   ███╗ █████╗ ████████╗ █████╗",
    "████╗  ██║██╔════╝██║ ██╔╝██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝██╔══██╗",
    "██╔██╗ ██║█████╗  █████╔╝ ██║   ██║██╔████╔██║███████║   ██║   ███████║",
    "██║╚██╗██║██╔══╝  ██╔═██╗ ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══██║",
    "██║ ╚████║███████╗██║  ██╗╚██████╔╝██║ ╚═╝ ██║██║  ██║   ██║   ██║  ██║",
    "╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝",
]
BANNER_WIDTH = max(len(line) for line in BANNER_LINES)
BANNER_SCAN_FRAMES = BANNER_WIDTH + 10

SLASH_COMMANDS = {
    "/browse": "card_browser",
    "/quit": "quit",
}


class HomeScreen(Screen):
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
        background: #11111b;
        color: #cdd6f4;
    }
    HomeScreen #home-stack {
        width: 100%;
        height: auto;
        align: center middle;
        background: #11111b;
    }
    HomeScreen #title {
        margin-bottom: 1;
        width: 71;
        color: #cba6f7;
        background: #11111b;
    }
    HomeScreen #title-row {
        width: 100%;
        height: auto;
    }
    HomeScreen #ornament {
        width: 100%;
        height: 1;
        margin-bottom: 1;
        color: #585b70;
        text-align: center;
        background: #11111b;
    }
    HomeScreen #input-area {
        width: 100%;
        height: auto;
        align: center top;
        background: #11111b;
    }
    HomeScreen #prompt-input {
        width: 60;
        height: 3;
        border: tall #89b4fa;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 1;
    }
    HomeScreen #prompt-input:focus {
        border: tall #cba6f7;
        background: #181825;
    }
    HomeScreen #command-suggestions {
        width: 60;
        height: auto;
        margin-top: 0;
        padding: 0 1;
        border: tall #89b4fa;
        color: #a6adc8;
        background: #181825;
    }
    HomeScreen .command-highlight {
        color: #cba6f7;
        text-style: bold;
    }
    HomeScreen .banner-shimmer {
        color: #f5c2e7;
        text-style: bold;
    }
    HomeScreen .banner-lit {
        color: #cba6f7;
        text-style: bold;
    }
    HomeScreen .banner-edge {
        color: #f5c2e7;
        text-style: bold;
    }
    HomeScreen .banner-ghost {
        color: #6c7086;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._banner_frame = 0
        self._banner_timer = None
        self._shimmer_idx = 0

    def compose(self):
        with Vertical(id="home-stack"):
            with Center(id="title-row"):
                yield Static("", id="title")
            yield Static("──── ✦ ────", id="ornament")
            with Vertical(id="input-area"):
                yield Input(
                    placeholder="> Ask the cats anything…",
                    id="prompt-input",
                )
                yield Static("", id="command-suggestions")

    def on_mount(self) -> None:
        self.query_one("#command-suggestions", Static).display = False
        animation_enabled = getattr(self.app, "animation_enabled", True)
        if animation_enabled:
            self._banner_frame = 0
            self._banner_timer = self.set_interval(0.035, self._animate_banner)
        else:
            self._update_banner(len(BANNER_LINES), None)

    def _animate_banner(self) -> None:
        if self._banner_frame >= BANNER_SCAN_FRAMES:
            self._shimmer_idx = (self._shimmer_idx + 1) % len(BANNER_LINES[0])
            self._update_banner(len(BANNER_LINES), self._shimmer_idx)
            return
        self._update_etched_banner(self._banner_frame)
        self._banner_frame += 5

    def _update_banner(self, visible_lines: int, shimmer_idx: int | None) -> None:
        lines = BANNER_LINES[:visible_lines]
        if shimmer_idx is not None:
            lines = [
                self._highlight_banner_column(line, shimmer_idx)
                for line in lines
            ]
        self.query_one("#title", Static).update("\n".join(lines))

    def _update_etched_banner(self, frame: int) -> None:
        rendered = [self._etch_line(line, frame) for line in BANNER_LINES]
        self.query_one("#title", Static).update("\n".join(rendered))

    def _etch_line(self, line: str, frame: int) -> str:
        cells: list[str] = []
        for idx, char in enumerate(line):
            if char == " ":
                cells.append(" ")
                continue
            distance = frame - idx
            if distance < -8:
                cells.append(" ")
            elif distance < -4:
                cells.append("[banner-ghost]░[/]")
            elif distance < -1:
                cells.append("[banner-ghost]▒[/]")
            elif distance < 3:
                cells.append(f"[banner-edge]{char}[/]")
            else:
                cells.append(f"[banner-lit]{char}[/]")
        return "".join(cells)

    def _highlight_banner_column(self, line: str, idx: int) -> str:
        if not line.strip():
            return line
        idx = min(idx, len(line) - 1)
        return (
            line[:idx]
            + f"[banner-shimmer]{line[idx]}[/]"
            + line[idx + 1 :]
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "prompt-input":
            return
        self._refresh_command_suggestions(event.value)

    def on_key(self, event: Key) -> None:
        if event.key != "tab":
            return
        prompt = self.query_one("#prompt-input", Input)
        match = self._matching_command(prompt.value)
        if match is None:
            return
        prompt.value = match
        prompt.cursor_position = len(match)
        self._refresh_command_suggestions(match)
        event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "prompt-input":
            return
        value = event.value.strip()
        if not value:
            return

        cmd = SLASH_COMMANDS.get(value.lower())
        if cmd == "card_browser":
            from nekomata.screens.card_browser import CardBrowserScreen
            self.app.push_screen(CardBrowserScreen())
            return
        if cmd == "quit":
            self.app.exit()
            return

        self.app.question = value
        from nekomata.screens.spread_select import SpreadSelectScreen
        self.app.push_screen(
            SpreadSelectScreen(), callback=self._on_spread_selected
        )

    def _refresh_command_suggestions(self, value: str) -> None:
        suggestions = self.query_one("#command-suggestions", Static)
        matches = [
            command for command in SLASH_COMMANDS if command.startswith(value.lower())
        ]
        if not value.startswith("/") or not matches or value.lower() in SLASH_COMMANDS:
            suggestions.display = False
            suggestions.update("")
            return
        suggestions.display = True
        suggestions.update("\n".join(f"[command-highlight]{cmd}[/]" for cmd in matches))

    def _matching_command(self, value: str) -> str | None:
        if not value.startswith("/"):
            return None
        matches = [
            command for command in SLASH_COMMANDS if command.startswith(value.lower())
        ]
        if len(matches) != 1:
            return None
        return matches[0]

    def _on_spread_selected(self, spread_key: str) -> None:
        from nekomata.screens.reading import ReadingScreen
        self.app.spread_key = spread_key
        self.app.push_screen(ReadingScreen(spread_key, self.app.question))
