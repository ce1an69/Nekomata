"""Spread selection screen — choose a card layout before drawing."""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.spread import SPREAD_REGISTRY


class SpreadSelectScreen(Screen):
    """Choose a card spread layout before drawing cards."""

    BINDINGS = [("escape", "go_back", "返回")]

    DEFAULT_CSS = """
    SpreadSelectScreen {
        align: center middle;
    }
    SpreadSelectScreen #question {
        text-align: center;
        color: #a6adc8;
        margin-bottom: 1;
    }
    SpreadSelectScreen #prompt {
        text-align: center;
        color: #cba6f7;
        text-style: bold;
        margin-bottom: 1;
    }
    SpreadSelectScreen Button {
        width: 48;
        margin-bottom: 1;
    }
    SpreadSelectScreen Button:hover {
        text-style: bold;
    }
    SpreadSelectScreen #back {
        border: tall #585b70;
        color: #a6adc8;
    }
    SpreadSelectScreen #spread-preview {
        width: 48;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 0;
        margin-bottom: 0;
    }
    SpreadSelectScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Build the spread selection screen with numbered buttons."""
        with Center():
            question = self.app.question
            if question:
                yield Static(f"🔮 {question}", id="question")
            yield Static("请选择牌阵：", id="prompt")
            with Vertical():
                for i, (key, desc, cls) in enumerate(SPREAD_REGISTRY, 1):
                    n_pos = len(cls().positions)
                    yield Button(
                        f"{i}  {cls.name_zh}（{n_pos}牌）— {desc}",
                        id=f"spread-{key}",
                    )
                yield Button("↩ 返回", id="back")
            yield Static("", id="spread-preview")
            yield Static("数字键快速选择 · ↑↓ 导航 · Enter 确认 · Esc 返回", id="hints")

    def on_mount(self) -> None:
        """Auto-focus the first spread button and show its preview."""
        buttons = list(self.query(Button))
        if buttons:
            buttons[0].focus()
            if buttons[0].id:
                self._update_preview(buttons[0].id)

    def _update_preview(self, btn_id: str) -> None:
        """Show position breakdown for the focused spread button."""
        preview = self.query_one("#spread-preview", Static)
        for key, _, cls in SPREAD_REGISTRY:
            if btn_id == f"spread-{key}":
                positions = " → ".join(p.name_zh for p in cls().positions)
                preview.update(f"位置：{positions}")
                return
        preview.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dispatch on button click: back pops, spread buttons dismiss with key."""
        if event.button.id == "back":
            self.app.pop_screen()
            return
        for key, _, _ in SPREAD_REGISTRY:
            if event.button.id == f"spread-{key}":
                self.dismiss(key)
                return

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

    # Digit key handlers for quick spread selection
    def key_1(self) -> None: self._select_by_index(0)
    def key_2(self) -> None: self._select_by_index(1)
    def key_3(self) -> None: self._select_by_index(2)
    def key_4(self) -> None: self._select_by_index(3)
    def key_5(self) -> None: self._select_by_index(4)
    def key_6(self) -> None: self._select_by_index(5)

    def key_down(self) -> None:
        """Move focus to the next spread button."""
        if isinstance(self.focused, Button):
            target = self._next_button(1)
            if target is not None and target.id:
                self._update_preview(target.id)

    def key_up(self) -> None:
        """Move focus to the previous spread button."""
        if isinstance(self.focused, Button):
            target = self._next_button(-1)
            if target is not None and target.id:
                self._update_preview(target.id)

    def _next_button(self, delta: int) -> Button | None:
        """Focus the next/previous button and return it."""
        buttons = list(self.query(Button))
        if not buttons:
            return None
        try:
            idx = buttons.index(self.focused)
        except ValueError:
            buttons[0].focus()
            return buttons[0]
        new_idx = idx + delta
        if 0 <= new_idx < len(buttons):
            buttons[new_idx].focus()
            return buttons[new_idx]
        return None
