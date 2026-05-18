"""Home screen with animated banner, question input, and slash commands."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.css.scalar import ScalarOffset
from textual.events import Key
from textual.geometry import Offset
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Input, Static

SLASH_COMMANDS = {
    "/browse": ("card_browser", "Browse all 78 cards"),
    "/help": ("help", "Show available commands"),
    "/status": ("status", "Show current configuration"),
    "/quit": ("quit", "Exit application"),
}


class HomePromptInput(Input):
    """Prompt input that reserves bare Q for quitting from an empty prompt."""

    def on_key(self, event: Key) -> None:
        if event.key == "q" and not self.value:
            self.app.exit()
            event.stop()
            return


class HomeScreen(Screen):
    """Landing screen with animated banner, question input, and slash commands."""

    BINDINGS = [
        Binding("q", "quit_if_empty", "Quit", priority=True),
    ]

    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }
    HomeScreen #home-stack {
        width: 72;
        height: auto;
        align: center middle;
        border: round #313244;
        background: #181825;
        padding: 1 2;
        transition: opacity 300ms out_cubic;
    }
    HomeScreen #title {
        margin-bottom: 1;
        width: 100%;
        background: #181825;
        color: #cba6f7;
        text-align: center;
        text-style: bold;
    }
    HomeScreen #ornament, HomeScreen #ornament-bottom {
        display: none;
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
        background: #181825;
    }
    HomeScreen #prompt-input {
        width: 100%;
        height: 3;
        border: round #45475a;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 1;
    }
    HomeScreen #prompt-input:focus {
        border: round #cba6f7;
        background: #181825;
    }
    HomeScreen #command-suggestions {
        width: 100%;
        height: auto;
        margin-top: 1;
        padding: 0 1;
        border: round #313244;
        color: #a6adc8;
        background: #11111b;
        transition: opacity 250ms out_cubic, offset 250ms out_cubic;
    }
    HomeScreen .command-highlight {
        color: #cba6f7;
        text-style: bold;
    }
    HomeScreen #hints {
        width: 100%;
        height: auto;
        background: #181825;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._suggestions_hide_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="home-stack"):
            yield Static("Nekomata", id="title")
            yield Static("─── ✦ ───", id="ornament")
            with Vertical(id="input-area"):
                yield HomePromptInput(
                    placeholder="> ask your question...",
                    id="prompt-input",
                )
                yield Static("", id="command-suggestions")
            yield Static("─── ✦ ───", id="ornament-bottom")
            yield Static("Enter confirm · / commands · Q quit", id="hints")

    def resume(self) -> None:
        """Clear and refocus the input — called when returning to this screen."""
        prompt = self.query_one("#prompt-input", Input)
        prompt.value = ""
        prompt.focus()
        if self.app.animation_enabled:
            stack = self.query_one("#home-stack")
            stack.styles.opacity = 0.5
            stack.styles.animate("opacity", 1.0, duration=0.25, easing="out_cubic")

    def _show_help(self) -> None:
        """Display help text in the command suggestions area."""
        lines = ["[command-highlight]Commands[/]\n"]
        for cmd, (_, desc) in SLASH_COMMANDS.items():
            lines.append(f"  {cmd:<10s} {desc}")
        lines.append("\nType a question to start a reading")
        self.set_timer(0.05, lambda: self._show_suggestions("\n".join(lines)))

    def _show_status(self) -> None:
        """Display current configuration in the command suggestions area."""
        cfg = self.app.config
        lines = ["[command-highlight]Configuration[/]\n"]
        lines.append(f"  API URL    {cfg.api_url}")
        lines.append(f"  API Key    {'(set)' if cfg.api_key else '(not set)'}")
        lines.append(f"  Model      {cfg.model}")
        lines.append(f"  Render     {self.app.render_mode}")
        self.set_timer(0.05, lambda: self._show_suggestions("\n".join(lines)))

    def _show_suggestions(self, text: str) -> None:
        """Update and show the command suggestions panel."""
        suggestions = self.query_one("#command-suggestions", Static)
        if self._suggestions_hide_timer is not None:
            self._suggestions_hide_timer.stop()
            self._suggestions_hide_timer = None
        suggestions.display = True
        suggestions.update(text)
        if self.app.animation_enabled:
            suggestions.styles.opacity = 0
            suggestions.styles.offset = (0, -1)
            suggestions.styles.animate("opacity", 1.0, duration=0.2, easing="out_cubic")
            suggestions.styles.animate("offset", ScalarOffset.from_offset(Offset(0, 0)), duration=0.2, easing="out_cubic")
        self.query_one("#prompt-input", Input).focus()

    def on_mount(self) -> None:
        """Hide command suggestions, focus input."""
        self.query_one("#command-suggestions", Static).display = False
        self.query_one("#prompt-input", Input).focus()

    def on_unmount(self) -> None:
        """Stop timers when screen is removed."""
        if self._suggestions_hide_timer is not None:
            self._suggestions_hide_timer.stop()
            self._suggestions_hide_timer = None

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update command suggestions dropdown as the user types."""
        if event.input.id != "prompt-input":
            return
        self._refresh_command_suggestions(event.value)

    def on_key(self, event: Key) -> None:
        """Handle home keyboard shortcuts."""
        prompt = self.query_one("#prompt-input", Input)
        if event.key != "tab":
            return
        match = self._matching_command(prompt.value)
        if match is None:
            return
        prompt.value = match
        prompt.cursor_position = len(match)
        self._refresh_command_suggestions(match)
        event.stop()

    def action_quit_if_empty(self) -> None:
        """Quit from the empty home prompt with Q."""
        if not self.query_one("#prompt-input", Input).value:
            self.app.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter: dispatch slash commands or proceed to spread selection."""
        if event.input.id != "prompt-input":
            return
        value = event.value.strip()
        if not value:
            return

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
            self._hide_suggestions()
            return
        if self._suggestions_hide_timer is not None:
            self._suggestions_hide_timer.stop()
            self._suggestions_hide_timer = None
        was_hidden = not suggestions.display
        suggestions.display = True
        prefix_len = len(value)
        lines = []
        for cmd in matches:
            typed = cmd[:prefix_len]
            rest = cmd[prefix_len:]
            lines.append(f"[command-highlight]{typed}[/]{rest}  {SLASH_COMMANDS[cmd][1]}")
        suggestions.update("\n".join(lines))
        if self.app.animation_enabled:
            if was_hidden:
                suggestions.styles.opacity = 0
                suggestions.styles.offset = (0, -1)
                suggestions.styles.animate("opacity", 1.0, duration=0.16, easing="out_cubic")
                suggestions.styles.animate(
                    "offset",
                    ScalarOffset.from_offset(Offset(0, 0)),
                    duration=0.16,
                    easing="out_cubic",
                )
            else:
                suggestions.styles.opacity = 1.0
                suggestions.styles.offset = (0, 0)

    def _hide_suggestions(self) -> None:
        suggestions = self.query_one("#command-suggestions", Static)
        if self._suggestions_hide_timer is not None:
            self._suggestions_hide_timer.stop()
            self._suggestions_hide_timer = None
        if not suggestions.display:
            suggestions.update("")
            return
        if not self.app.animation_enabled:
            suggestions.display = False
            suggestions.update("")
            return
        suggestions.styles.animate("opacity", 0.0, duration=0.12, easing="out_cubic")
        suggestions.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, -1)),
            duration=0.12,
            easing="out_cubic",
        )
        self._suggestions_hide_timer = self.set_timer(0.13, self._finish_hide_suggestions)

    def _finish_hide_suggestions(self) -> None:
        suggestions = self.query_one("#command-suggestions", Static)
        suggestions.display = False
        suggestions.update("")
        suggestions.styles.opacity = 1.0
        suggestions.styles.offset = (0, 0)
        self._suggestions_hide_timer = None

    def _matching_command(self, value: str) -> str | None:
        """Return the unique slash command matching the input, or None."""
        if not value.startswith("/"):
            return None
        matches = [cmd for cmd in SLASH_COMMANDS if cmd.startswith(value.lower())]
        return matches[0] if len(matches) == 1 else None

    def _on_spread_selected(self, spread_key: str) -> None:
        """Callback when the user picks a spread — push the draw screen."""
        from nekomata.screens.draw import DrawScreen
        self.app.spread_key = spread_key
        self.app.push_screen(DrawScreen(spread_key, self.app.question))
