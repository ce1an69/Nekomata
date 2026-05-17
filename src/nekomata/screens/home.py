"""Home screen with animated banner, question input, and slash commands."""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.timer import Timer
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
    "/browse": ("card_browser", "浏览 78 张塔罗牌"),
    "/help": ("help", "显示帮助"),
    "/history": ("history", "查看占卜日记"),
    "/status": ("status", "查看当前配置"),
    "/quit": ("quit", "退出应用"),
}


class HomeScreen(Screen):
    """Landing screen with animated banner, question input, and slash commands."""

    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }
    HomeScreen #home-stack {
        width: 100%;
        height: auto;
        align: center middle;
    }
    HomeScreen #title {
        margin-bottom: 1;
        width: 71;
        color: #cba6f7;
    }
    HomeScreen #title-row {
        width: 100%;
        height: auto;
    }
    HomeScreen #subtitle {
        width: 100%;
        height: auto;
        color: #a6adc8;
        text-align: center;
        margin-bottom: 0;
    }
    HomeScreen #ornament, HomeScreen #ornament-bottom {
        width: 100%;
        height: 1;
        color: #585b70;
        text-align: center;
    }
    HomeScreen #ornament {
        margin-bottom: 1;
    }
    HomeScreen #ornament-bottom {
        margin-top: 1;
    }
    HomeScreen #input-area {
        width: 100%;
        height: auto;
        align: center top;
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
    HomeScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._banner_frame = 0
        self._banner_timer: Timer | None = None
        self._shimmer_idx = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="home-stack"):
            with Center(id="title-row"):
                yield Static("", id="title")
            yield Static("猫又塔罗 · Pixel Cat Tarot", id="subtitle")
            yield Static("──── ✦ ────", id="ornament")
            with Vertical(id="input-area"):
                yield Input(
                    placeholder="> 向猫咪提出你的问题…",
                    id="prompt-input",
                )
                yield Static("", id="command-suggestions")
            yield Static("──── ✦ ────", id="ornament-bottom")
            yield Static("Enter 提交 · Tab 补全 · /help 帮助 · /status 配置 · /browse 牌库 · /history 日记 · /quit 退出", id="hints")

    def resume(self) -> None:
        """Clear and refocus the input — called by go_home when returning."""
        prompt = self.query_one("#prompt-input", Input)
        prompt.value = ""
        prompt.focus()

    def _show_help(self) -> None:
        """Display help text in the command suggestions area."""
        lines = ["[command-highlight]可用命令[/]\n"]
        for cmd, (_, desc) in SLASH_COMMANDS.items():
            lines.append(f"  {cmd:<10s} {desc}")
        lines.append("\n输入问题即可开始占卜")
        # Delay display to avoid being hidden by the Input.Changed callback
        self.set_timer(0.05, lambda: self._show_suggestions("\n".join(lines)))

    def _show_status(self) -> None:
        """Display current configuration in the command suggestions area."""
        cfg = self.app.config
        lines = ["[command-highlight]当前配置[/]\n"]
        lines.append(f"  AI 后端　{cfg.ai_backend}")
        lines.append(f"  模型　　{cfg.ai_model or '（未设置）'}")
        lines.append(f"  风格　　{cfg.ai_style}")
        lines.append(f"  动画　　{'开启' if cfg.display_animation else '关闭'}")
        lines.append(f"  主题　　{cfg.display_theme}")
        lines.append(f"  逆位概率 {cfg.reversal_prob:.0%}")
        lines.append(f"  渲染　　{self.app.render_mode}")
        self.set_timer(0.05, lambda: self._show_suggestions("\n".join(lines)))

    def _show_suggestions(self, text: str) -> None:
        """Update and show the command suggestions panel."""
        suggestions = self.query_one("#command-suggestions", Static)
        suggestions.display = True
        suggestions.update(text)
        self.query_one("#prompt-input", Input).focus()

    def on_mount(self) -> None:
        """Hide command suggestions, focus input, start banner animation."""
        self.query_one("#command-suggestions", Static).display = False
        self.query_one("#prompt-input", Input).focus()
        animation_enabled = self.app.animation_enabled
        if animation_enabled:
            self._banner_frame = 0
            self._banner_timer = self.set_interval(0.035, self._animate_banner)
        else:
            self._update_banner(len(BANNER_LINES), None)

    def on_unmount(self) -> None:
        """Stop the banner animation timer when screen is removed."""
        if self._banner_timer is not None:
            self._banner_timer.stop()
            self._banner_timer = None

    def _animate_banner(self) -> None:
        """Advance the banner animation: scan-wave first, then shimmer."""
        if self._banner_frame >= BANNER_SCAN_FRAMES:
            # Scan complete — start column-by-column shimmer
            self._shimmer_idx = (self._shimmer_idx + 1) % len(BANNER_LINES[0])
            self._update_banner(len(BANNER_LINES), self._shimmer_idx)
            return
        self._update_etched_banner(self._banner_frame)
        self._banner_frame += 5

    def _update_banner(self, visible_lines: int, shimmer_idx: int | None) -> None:
        """Render the banner with the given number of visible lines and optional shimmer column."""
        lines = BANNER_LINES[:visible_lines]
        if shimmer_idx is not None:
            lines = [self._highlight_banner_column(line, shimmer_idx) for line in lines]
        self.query_one("#title", Static).update("\n".join(lines))

    def _update_etched_banner(self, frame: int) -> None:
        """Render the etched scan-wave banner at the given frame position."""
        rendered = [self._etch_line(line, frame) for line in BANNER_LINES]
        self.query_one("#title", Static).update("\n".join(rendered))

    def _etch_line(self, line: str, frame: int) -> str:
        """Render a banner line with a left-to-right scan-wave effect.

        Each character's appearance depends on its distance from the scan
        cursor (frame): blank far ahead, faint dots approaching, pink edge
        at the front, purple "lit" behind.
        """
        cells: list[str] = []
        for idx, char in enumerate(line):
            if char == " ":
                cells.append(" ")
                continue
            distance = frame - idx
            if distance < -8:
                cells.append(" ")                       # Not yet reached
            elif distance < -4:
                cells.append("[banner-ghost]░[/]")      # Faint preview
            elif distance < -1:
                cells.append("[banner-ghost]▒[/]")      # Brighter preview
            elif distance < 3:
                cells.append(f"[banner-edge]{char}[/]") # Pink leading edge
            else:
                cells.append(f"[banner-lit]{char}[/]")  # Settled purple
        return "".join(cells)

    def _highlight_banner_column(self, line: str, idx: int) -> str:
        """Highlight a single column in a banner line for the shimmer effect."""
        if not line.strip():
            return line
        idx = min(idx, len(line) - 1)
        return line[:idx] + f"[banner-shimmer]{line[idx]}[/]" + line[idx + 1:]

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update command suggestions dropdown as the user types."""
        if event.input.id != "prompt-input":
            return
        self._refresh_command_suggestions(event.value)

    def on_key(self, event: Key) -> None:
        """Handle Tab key for command autocomplete."""
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
        """Handle Enter: dispatch slash commands or proceed to spread selection."""
        if event.input.id != "prompt-input":
            return
        value = event.value.strip()
        if not value:
            return

        # Check for slash commands first (help/status handle their own input clearing)
        cmd_entry = SLASH_COMMANDS.get(value.lower())
        if cmd_entry is not None:
            cmd = cmd_entry[0]
            if cmd == "card_browser":
                self.query_one("#prompt-input", Input).value = ""
                from nekomata.screens.card_browser import CardBrowserScreen
                self.app.push_screen(CardBrowserScreen())
                return
            if cmd == "help":
                self.query_one("#prompt-input", Input).value = ""
                self._show_help()
                return
            if cmd == "history":
                self.query_one("#prompt-input", Input).value = ""
                from nekomata.screens.journal import JournalScreen
                self.app.push_screen(JournalScreen())
                return
            if cmd == "status":
                self.query_one("#prompt-input", Input).value = ""
                self._show_status()
                return
            if cmd == "quit":
                self.app.exit()
                return

        # Not a command — treat as a divination question
        self.query_one("#prompt-input", Input).value = ""
        self.app.question = value
        from nekomata.screens.spread_select import SpreadSelectScreen
        self.app.push_screen(SpreadSelectScreen(), callback=self._on_spread_selected)

    def _refresh_command_suggestions(self, value: str) -> None:
        """Show or hide the command suggestions dropdown based on input."""
        suggestions = self.query_one("#command-suggestions", Static)
        matches = [cmd for cmd in SLASH_COMMANDS if cmd.startswith(value.lower())]
        if not value.startswith("/") or not matches or value.lower() in SLASH_COMMANDS:
            suggestions.display = False
            suggestions.update("")
            return
        suggestions.display = True
        prefix_len = len(value)
        lines = []
        for cmd in matches:
            # Highlight the typed prefix in a different color
            typed = cmd[:prefix_len]
            rest = cmd[prefix_len:]
            lines.append(f"[command-highlight]{typed}[/]{rest}  {SLASH_COMMANDS[cmd][1]}")
        suggestions.update("\n".join(lines))

    def _matching_command(self, value: str) -> str | None:
        """Return the unique slash command matching the input, or None."""
        if not value.startswith("/"):
            return None
        matches = [cmd for cmd in SLASH_COMMANDS if cmd.startswith(value.lower())]
        return matches[0] if len(matches) == 1 else None

    def _on_spread_selected(self, spread_key: str) -> None:
        """Callback when the user picks a spread — push the reading screen."""
        from nekomata.screens.reading import ReadingScreen
        self.app.spread_key = spread_key
        self.app.push_screen(ReadingScreen(spread_key, self.app.question))
