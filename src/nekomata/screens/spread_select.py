"""Spread selection screen — choose a card layout before drawing."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset

from nekomata.render.styles import (
    C_CRUST,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_SUBTEXT0,
    C_SURFACE0,
    C_TEXT,
)
from nekomata.spread import SPREAD_REGISTRY


class SpreadOption(Static):
    """Focusable spread selection row with soft Catppuccin styling."""

    can_focus = True

    DEFAULT_CSS = f"""
    SpreadOption {{
        height: 3;
        padding: 0 2;
        margin-bottom: 1;
        border: round {C_MANTLE};
        background: {C_MANTLE};
        color: {C_SUBTEXT0};
        transition: offset 300ms out_cubic, opacity 300ms out_cubic,
                    background 200ms, border 200ms, color 200ms;
    }}
    SpreadOption:hover {{
        background: #1e1e2e;
        color: {C_TEXT};
    }}
    SpreadOption:focus {{
        background: #1e1e2e;
        border: round {C_MAUVE};
        color: {C_TEXT};
        text-style: bold;
    }}
    SpreadOption.back {{
        margin-top: 1;
        color: {C_SUBTEXT0};
    }}
    """

    class Selected(Message):
        """Posted when a spread row is activated."""

        def __init__(self, option_id: str) -> None:
            super().__init__()
            self.option_id = option_id

    def __init__(self, label: str, option_id: str, *, back: bool = False) -> None:
        super().__init__(label, id=option_id)
        if back:
            self.add_class("back")

    def on_click(self) -> None:
        if self.id:
            self.post_message(self.Selected(self.id))

    def key_enter(self) -> None:
        if self.id:
            self.post_message(self.Selected(self.id))


class SpreadSelectScreen(Screen):
    """Choose a card spread layout before drawing cards."""

    BINDINGS = [
        ("q", "go_back", "Back"),
        ("escape", "go_back", "Back"),
    ]

    DEFAULT_CSS = f"""
    SpreadSelectScreen {{
        align: center middle;
    }}
    SpreadSelectScreen #spread-shell {{
        width: 86;
        height: auto;
    }}
    SpreadSelectScreen #question {{
        text-align: center;
        color: {C_TEXT};
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 0 2;
        margin-bottom: 1;
        width: 100%;
    }}
    SpreadSelectScreen #prompt {{
        text-align: center;
        color: {C_MAUVE};
        text-style: bold;
        margin-bottom: 1;
    }}
    SpreadSelectScreen #spread-body {{
        height: auto;
    }}
    SpreadSelectScreen #spread-buttons {{
        width: 44;
        height: auto;
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 1 1;
    }}
    SpreadSelectScreen #spread-preview {{
        width: 1fr;
        height: 100%;
        color: {C_OVERLAY0};
        text-align: left;
        margin-left: 1;
        margin-bottom: 0;
        border: round {C_SURFACE0};
        background: {C_CRUST};
        padding: 1 2;
        transition: opacity 250ms out_cubic;
    }}
    SpreadSelectScreen #preview-title {{
        background: {C_CRUST};
        color: {C_MAUVE};
        text-style: bold;
        margin-bottom: 1;
    }}
    SpreadSelectScreen #preview-desc {{
        background: {C_CRUST};
        color: {C_SUBTEXT0};
        margin-bottom: 1;
    }}
    SpreadSelectScreen #preview-positions {{
        background: {C_CRUST};
        color: {C_OVERLAY0};
        padding: 0 2;
    }}
    SpreadSelectScreen #hints {{
        width: 100%;
        height: auto;
        color: {C_OVERLAY0};
        text-align: center;
        margin-top: 1;
    }}
    """

    def compose(self) -> ComposeResult:
        """Build the spread selection screen with numbered buttons."""
        question = self.app.question
        with Vertical(id="spread-shell"):
            if question:
                yield Static(question, id="question")
            yield Static("Choose a spread", id="prompt")
            with Horizontal(id="spread-body"):
                with Vertical(id="spread-buttons"):
                    for i, (key, _, cls) in enumerate(SPREAD_REGISTRY, 1):
                        n_pos = len(cls().positions)
                        yield SpreadOption(
                            f"{i:02d}  {cls.name:<24s} {n_pos:>2d}",
                            f"spread-{key}",
                        )
                    yield SpreadOption("Q   Back", "back", back=True)
                with Vertical(id="spread-preview"):
                    yield Static("", id="preview-title")
                    yield Static("", id="preview-desc")
                    yield Static("", id="preview-positions")
            yield Static("↑/↓/←/→ move · Enter confirm · Q back", id="hints")

    def on_mount(self) -> None:
        """Auto-focus the first spread button, show preview, and animate entrance."""
        options = list(self.query(SpreadOption))
        if options:
            options[0].focus()
            if options[0].id:
                self._update_preview(options[0].id)
        if self.app.animation_enabled:
            shell = self.query_one("#spread-shell")
            shell.styles.opacity = 0
            shell.styles.offset = (0, 1)
            shell.styles.animate("opacity", 1.0, duration=0.35, easing="out_cubic")
            shell.styles.animate("offset", ScalarOffset.from_offset(Offset(0, 0)), duration=0.35, easing="out_cubic")
            for i, opt in enumerate(options):
                opt.styles.opacity = 0
                opt.styles.offset = (0, 1)
                self.set_timer(
                    max(i * 0.05, 0.001),
                    lambda w=opt: (
                        w.styles.animate("opacity", 1.0, duration=0.28, easing="out_cubic"),
                        w.styles.animate("offset", ScalarOffset.from_offset(Offset(0, 0)), duration=0.28, easing="out_cubic"),
                    ),
                )

    def _update_preview(self, btn_id: str) -> None:
        """Show position breakdown for the focused spread button."""
        preview = self.query_one("#spread-preview")
        if self.app.animation_enabled:
            preview.styles.opacity = 0.3
        title = self.query_one("#preview-title", Static)
        desc_text = self.query_one("#preview-desc", Static)
        positions_text = self.query_one("#preview-positions", Static)
        for key, desc, cls in SPREAD_REGISTRY:
            if btn_id == f"spread-{key}":
                spread = cls()
                positions = "\n".join(
                    f"{idx:02d}  {position.name}"
                    for idx, position in enumerate(spread.positions, 1)
                )
                title.update(spread.name)
                desc_text.update(desc)
                positions_text.update(positions)
                if self.app.animation_enabled:
                    self.set_timer(
                        0.06,
                        lambda: preview.styles.animate("opacity", 1.0, duration=0.2, easing="out_cubic"),
                    )
                return
        title.update("Back")
        desc_text.update("Return to the question prompt.")
        positions_text.update("")

    def on_spread_option_selected(self, event: SpreadOption.Selected) -> None:
        """Dispatch when a spread option is clicked or Enter-pressed."""
        self._activate_option(event.option_id)

    def action_go_back(self) -> None:
        """Escape key binding — return to home and refocus input."""
        self.app.pop_screen()
        from nekomata.screens.home import HomeScreen
        if isinstance(self.app.screen, HomeScreen):
            self.app.screen.resume()

    def _select_by_index(self, index: int) -> None:
        """Dismiss this screen with the spread at the given registry index."""
        if 0 <= index < len(SPREAD_REGISTRY):
            self.dismiss(SPREAD_REGISTRY[index][0])

    def key_1(self) -> None: self._select_by_index(0)
    def key_2(self) -> None: self._select_by_index(1)
    def key_3(self) -> None: self._select_by_index(2)
    def key_4(self) -> None: self._select_by_index(3)
    def key_5(self) -> None: self._select_by_index(4)
    def key_6(self) -> None: self._select_by_index(5)

    def key_down(self) -> None:
        """Move focus to the next spread option."""
        self._move_option(1)

    def key_right(self) -> None:
        """Move focus to the next spread option."""
        self._move_option(1)

    def key_left(self) -> None:
        """Move focus to the previous spread option."""
        self._move_option(-1)

    def key_up(self) -> None:
        """Move focus to the previous spread option."""
        self._move_option(-1)

    def _move_option(self, delta: int) -> None:
        """Move focus between spread options and refresh the preview."""
        if isinstance(self.focused, SpreadOption):
            target = self._next_option(delta)
            if target is not None and target.id:
                self._update_preview(target.id)

    def _next_option(self, delta: int) -> SpreadOption | None:
        """Focus the next/previous spread option and return it."""
        options = list(self.query(SpreadOption))
        if not options:
            return None
        try:
            idx = options.index(self.focused)
        except ValueError:
            options[0].focus()
            return options[0]
        new_idx = idx + delta
        if 0 <= new_idx < len(options):
            options[new_idx].focus()
            return options[new_idx]
        return None

    def _activate_option(self, option_id: str) -> None:
        """Activate a spread row by id."""
        if option_id == "back":
            self.action_go_back()
            return
        for key, _, _ in SPREAD_REGISTRY:
            if option_id == f"spread-{key}":
                self.dismiss(key)
                return
