"""Home screen with animated banner, question input, and slash commands."""

from rich.highlighter import Highlighter
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
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
from nekomata.i18n import ORNAMENT

_STR = lazy_section("home")

SLASH_COMMANDS = {k: tuple(v) for k, v in _STR["commands"].items()}


class _SlashCommandHighlighter(Highlighter):
    """Colors the command portion (before first space) in mauve, rest in normal."""

    def highlight(self, text: Text) -> None:
        value = text.plain
        if not value.startswith("/"):
            text.stylize(Style(color=C_TEXT))
            return
        space_idx = value.find(" ")
        if space_idx > 0:
            text.stylize(Style(color=C_MAUVE), 0, space_idx)
            text.stylize(Style(color=C_TEXT), space_idx)
        else:
            text.stylize(Style(color=C_MAUVE))


class HomePromptInput(Input):
    """Prompt input with per-character command coloring."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(highlighter=_SlashCommandHighlighter(), **kwargs)


class HomeScreen(Screen):
    """Landing screen with animated banner, question input, and slash commands."""

    BINDINGS = []

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
        padding: 0 1;
    }}
    HomeScreen #prompt-input:focus {{
        border: round {C_MAUVE};
        background: {C_MANTLE};
    }}
    HomeScreen #command-suggestions {{
        width: auto;
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

    def _on_config_done(self, _result: None) -> None:
        """Callback after /config setup screen is dismissed."""
        self.resume()

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
            if self._suggestion_idx >= 0 and self._suggestion_matches:
                match = self._suggestion_matches[self._suggestion_idx]
            else:
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
            self._render_suggestions()
            return

        if event.key == "right" and self._suggestion_idx >= 0 and self._suggestion_matches:
            match = self._suggestion_matches[self._suggestion_idx]
            prompt.value = match
            prompt.cursor_position = len(match)
            self._refresh_command_suggestions(match)
            event.stop()
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter: dispatch slash commands or proceed to spread selection."""
        if event.input.id != "prompt-input":
            return
        value = event.value.strip()

        # If a suggestion is highlighted, use that as the command
        if self._suggestion_idx >= 0 and self._suggestion_matches:
            value = self._suggestion_matches[self._suggestion_idx]

        if not value:
            return

        cmd_entry = SLASH_COMMANDS.get(value.lower())
        if cmd_entry is not None:
            self.query_one("#prompt-input", Input).value = ""
            self._hide_suggestions()
            cmd = cmd_entry[0]
            if cmd == "card_browser":
                from nekomata.screens.card_browser import CardBrowserScreen

                self.app.push_screen(CardBrowserScreen())
                return
            if cmd == "config":
                from nekomata.screens.setup import SetupScreen

                self.app.push_screen(
                    SetupScreen(self.app.config), callback=self._on_config_done
                )
                return
            if cmd == "quit":
                self.app.exit()
                return
        elif value.startswith("/"):
            self._show_suggestions(
                f"[command-highlight]{_STR['unknown_command']}[/]  {value}"
            )
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
        """Render the suggestion list with full-row highlight for selection."""
        suggestions = self.query_one("#command-suggestions", Static)
        if not self._suggestion_matches:
            suggestions.display = False
            suggestions.update("")
            return
        prefix_len = len(self._suggestion_typed_prefix)
        # Pad all lines to the same visible width so the highlight background
        # covers the full row instead of just the text characters.
        visible_widths = [
            2 + len(cmd) + 2 + len(desc)
            for cmd in self._suggestion_matches
            for (_, desc) in [SLASH_COMMANDS[cmd]]
        ]
        max_width = max(visible_widths) if visible_widths else 0
        lines = []
        for i, cmd in enumerate(self._suggestion_matches):
            _, desc = SLASH_COMMANDS[cmd]
            plain = f"  {cmd}  {desc}"
            padding = " " * (max_width - len(plain))
            if i == self._suggestion_idx:
                lines.append(
                    f"[{C_MAUVE} bold on {C_SURFACE0}]{plain}{padding}[/]"
                )
            else:
                typed = cmd[:prefix_len]
                rest = cmd[prefix_len:]
                lines.append(
                    f"  [bold {C_MAUVE}]{typed}[/]{rest}  {desc}{padding}"
                )
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
        self._suggestions_hide_timer = self.set_timer(
            0.13, self._finish_hide_suggestions
        )

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
        matches = [
            cmd for cmd in SLASH_COMMANDS if cmd.startswith(lower) and cmd != lower
        ]
        return matches[0] if matches else None

    def _on_spread_selected(self, spread_key: str) -> None:
        """Callback when the user picks a spread — push the draw screen."""
        from nekomata.screens.draw import DrawScreen

        self.app.spread_key = spread_key
        self.app.push_screen(DrawScreen(spread_key, self.app.question, lang=self.app.config.lang))
