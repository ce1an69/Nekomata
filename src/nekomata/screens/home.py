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

from nekomata.render.animations import animate_entrance
from nekomata.render.styles import (
    C_BASE,
    C_CRUST,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_SUBTEXT0,
    C_SURFACE0,
    C_SURFACE1,
    C_TEXT,
    EASE,
)
from nekomata.i18n import lazy_section
from nekomata.strings import ORNAMENT

_STR = lazy_section("home")
_STATUS_STR = lazy_section("status")

SLASH_COMMANDS = {k: tuple(v) for k, v in _STR["commands"].items()}


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

    DEFAULT_CSS = f"""
    HomeScreen {{
        align: center middle;
    }}
    HomeScreen #home-stack {{
        width: 72;
        height: auto;
        align: center middle;
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 1 2;
        transition: opacity 300ms out_quint;
    }}
    HomeScreen #title {{
        margin-bottom: 1;
        width: 100%;
        background: {C_MANTLE};
        color: {C_MAUVE};
        text-align: center;
        text-style: bold;
    }}
    HomeScreen #ornament, HomeScreen #ornament-bottom {{
        display: none;
    }}
    HomeScreen #ornament {{
        margin-bottom: 1;
    }}
    HomeScreen #ornament-bottom {{
        margin-top: 1;
    }}
    HomeScreen #input-area {{
        width: 100%;
        height: auto;
        align: center top;
        background: {C_MANTLE};
    }}
    HomeScreen #prompt-input {{
        width: 100%;
        height: 3;
        border: round {C_SURFACE1};
        background: {C_BASE};
        color: {C_TEXT};
        padding: 0 1;
    }}
    HomeScreen #prompt-input:focus {{
        border: round {C_MAUVE};
        background: {C_MANTLE};
    }}
    HomeScreen #command-suggestions {{
        width: 100%;
        height: auto;
        margin-top: 1;
        padding: 0 1;
        border: round {C_SURFACE0};
        color: {C_SUBTEXT0};
        background: {C_CRUST};
        transition: opacity 250ms out_quint, offset 250ms out_quint;
    }}
    HomeScreen .command-highlight {{
        color: {C_MAUVE};
        text-style: bold;
    }}
    HomeScreen #hints {{
        width: 100%;
        height: auto;
        background: {C_MANTLE};
        color: {C_OVERLAY0};
        text-align: center;
        margin-top: 1;
    }}
    """

    def __init__(self) -> None:
        super().__init__()
        self._suggestions_hide_timer: Timer | None = None
        self._suggestion_matches: list[str] = []
        self._suggestion_idx: int = -1
        self._suggestion_typed_prefix: str = ""
        self._navigating_suggestions: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="home-stack"):
            yield Static(_STR["title"], id="title")
            yield Static(ORNAMENT, id="ornament")
            with Vertical(id="input-area"):
                yield HomePromptInput(
                    placeholder=_STR["placeholder"],
                    id="prompt-input",
                )
                yield Static("", id="command-suggestions")
            yield Static(ORNAMENT, id="ornament-bottom")
            yield Static(_STR["hints"], id="hints")

    def resume(self) -> None:
        """Clear and refocus the input — called when returning to this screen."""
        prompt = self.query_one("#prompt-input", Input)
        prompt.value = ""
        prompt.focus()
        if self.app.animation_enabled:
            stack = self.query_one("#home-stack")
            stack.styles.opacity = 0.5
            stack.styles.animate("opacity", 1.0, duration=0.25, easing=EASE)

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
        key_status = _STATUS_STR["api_key_set"] if cfg.api_key else _STATUS_STR["api_key_not_set"]
        lines = [f"[command-highlight]{_STATUS_STR['title']}[/]\n"]
        lines.append(f"  {_STATUS_STR['api_url']}    {cfg.api_url}")
        lines.append(f"  {_STATUS_STR['api_key']}    {key_status}")
        lines.append(f"  {_STATUS_STR['model']}      {cfg.model}")
        lines.append(f"  {_STATUS_STR['render']}     {self.app.render_mode}")
        self.set_timer(0.05, lambda: self._show_suggestions("\n".join(lines)))

    def _show_suggestions(self, text: str) -> None:
        """Update and show the command suggestions panel."""
        suggestions = self.query_one("#command-suggestions", Static)
        if self._suggestions_hide_timer is not None:
            self._suggestions_hide_timer.stop()
            self._suggestions_hide_timer = None
        suggestions.display = True
        suggestions.update(text)
        animate_entrance(suggestions, duration=0.2, dy=-1)
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
        """Handle Tab completion and arrow navigation for slash commands."""
        prompt = self.query_one("#prompt-input", Input)

        if event.key == "tab":
            match = self._matching_command(prompt.value)
            if match is None:
                return
            prompt.value = match
            prompt.cursor_position = len(match)
            self._refresh_command_suggestions(match)
            event.stop()
            return

        if event.key in ("up", "down") and self._suggestion_matches:
            event.stop()
            delta = 1 if event.key == "down" else -1
            new_idx = self._suggestion_idx + delta
            if new_idx < 0:
                new_idx = len(self._suggestion_matches) - 1
            elif new_idx >= len(self._suggestion_matches):
                new_idx = 0
            self._suggestion_idx = new_idx
            self._navigating_suggestions = True
            prompt.value = self._suggestion_matches[new_idx]
            prompt.cursor_position = len(prompt.value)
            self._render_suggestions()
            self._navigating_suggestions = False
            return

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
        if self._navigating_suggestions:
            return
        suggestions = self.query_one("#command-suggestions", Static)
        matches = [cmd for cmd in SLASH_COMMANDS if cmd.startswith(value.lower())]
        if not value.startswith("/") or not matches or value.lower() in SLASH_COMMANDS:
            self._suggestion_matches = []
            self._suggestion_idx = -1
            self._hide_suggestions()
            return
        if self._suggestions_hide_timer is not None:
            self._suggestions_hide_timer.stop()
            self._suggestions_hide_timer = None
        was_hidden = not suggestions.display
        suggestions.display = True
        self._suggestion_matches = matches
        self._suggestion_idx = -1
        self._suggestion_typed_prefix = value.lower()
        self._render_suggestions()
        if was_hidden:
            animate_entrance(suggestions, duration=0.16, dy=-1)
        elif self.app.animation_enabled:
            suggestions.styles.opacity = 1.0
            suggestions.styles.offset = (0, 0)

    def _render_suggestions(self) -> None:
        """Render the suggestion list with the current selection highlighted."""
        suggestions = self.query_one("#command-suggestions", Static)
        if not self._suggestion_matches:
            suggestions.display = False
            suggestions.update("")
            return
        prefix_len = len(self._suggestion_typed_prefix)
        lines = []
        for i, cmd in enumerate(self._suggestion_matches):
            _, desc = SLASH_COMMANDS[cmd]
            if i == self._suggestion_idx:
                lines.append(f" ▸ [command-highlight]{cmd}[/]  {desc}")
            else:
                typed = cmd[:prefix_len]
                rest = cmd[prefix_len:]
                lines.append(f"   [command-highlight]{typed}[/]{rest}  {desc}")
        suggestions.update("\n".join(lines))

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
        suggestions.styles.animate("opacity", 0.0, duration=0.12, easing=EASE)
        suggestions.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, -1)),
            duration=0.12,
            easing=EASE,
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
        """Return the first slash command matching the input prefix."""
        if not value.startswith("/"):
            return None
        lower = value.lower()
        matches = [cmd for cmd in SLASH_COMMANDS if cmd.startswith(lower) and cmd != lower]
        return matches[0] if matches else None

    def _on_spread_selected(self, spread_key: str) -> None:
        """Callback when the user picks a spread — push the draw screen."""
        from nekomata.screens.draw import DrawScreen
        self.app.spread_key = spread_key
        self.app.push_screen(DrawScreen(spread_key, self.app.question))
