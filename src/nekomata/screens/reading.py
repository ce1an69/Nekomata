"""Reading screen — displays drawn cards and triggers AI interpretation."""

import asyncio
import logging

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.events import Key
from textual.message import Message
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from nekomata.ai.interpreter import get_interpreter, template_interpret
from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.render.animations import animate_reveal
from nekomata.render.card_renderer import (
    render_card_text,
    render_card_detail,
    render_card_image,
    render_card_image_detail,
)
from nekomata.screens.interpretation import InterpretationScreen
from nekomata.screens.widgets import focus_sibling, go_home
from nekomata.spread import get_spread

log = logging.getLogger(__name__)

# Rotating messages shown while waiting for AI interpretation
_WAITING_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
CAT_WAITING_MESSAGES = [
    "命运之书翻页中…",
    "喵~ 星辰正在排列…",
    "竖起耳朵，聆听宇宙…",
    "思考猫生的意义…",
    "纸牌在软软的猫爪间飞舞…",
    "凝视水晶球…",
    "月光下解读秘密…",
    "在星图上留下猫爪印…",
]


class CardWidget(Static):
    """A focusable widget that renders a single drawn card."""

    can_focus = True

    DEFAULT_CSS = """
    CardWidget {
        margin: 0 0 1 0;
        height: auto;
    }
    CardWidget:focus {
        border: tall #cba6f7;
        background: #181825;
    }
    CardWidget:hover {
        background: #181825;
    }
    CardWidget.selected {
        background: #181825;
        border-left: tall #f9e2af;
    }
    CardWidget.selected:focus {
        border: tall #cba6f7;
    }
    CardWidget.reversed {
        border-left: tall #89b4fa;
    }
    CardWidget.reversed.selected {
        border-left: tall #f9e2af;
    }
    CardWidget.reversed:focus {
        border: tall #89b4fa;
    }
    """

    class Selected(Message):
        """Posted when a card widget is clicked, focused, or Enter-pressed."""

        def __init__(self, drawn_card: DrawnCard, widget: CardWidget) -> None:
            super().__init__()
            self.drawn_card = drawn_card
            self.widget = widget

    def __init__(self, drawn: DrawnCard, render_mode: str = "compact") -> None:
        self._drawn = drawn
        img_panel = None
        if render_mode != "text":
            img_panel = render_card_image(drawn, size=render_mode)
        super().__init__(img_panel if img_panel else render_card_text(drawn))
        if drawn.is_reversed:
            self.add_class("reversed")

    def on_click(self) -> None:
        self.post_message(self.Selected(self._drawn, self))

    def on_focus(self) -> None:
        self.post_message(self.Selected(self._drawn, self))

    def key_enter(self) -> None:
        self.post_message(self.Selected(self._drawn, self))


class ReadingScreen(Screen):
    """Displays drawn cards in the chosen spread layout and triggers AI interpretation."""

    BINDINGS = [
        ("i", "interpret", "解读"),
        ("r", "reshuffle", "重新抽牌"),
        ("escape", "handle_escape", "返回"),
    ]

    DEFAULT_CSS = """
    ReadingScreen {
        align: center top;
    }
    ReadingScreen #question-display {
        text-align: center;
        color: #a6adc8;
        margin: 1 0 0 0;
    }
    ReadingScreen #spread-label {
        text-align: center;
        color: #6c7086;
        margin: 0 0 1 0;
    }
    ReadingScreen #main-area {
        height: 1fr;
    }
    ReadingScreen #cards-container {
        width: 1fr;
        height: 1fr;
    }
    ReadingScreen #card-preview {
        width: 1fr;
        height: 1fr;
        border: round #45475a;
        padding: 1 2;
    }
    ReadingScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    ReadingScreen #waiting-msg {
        color: #cba6f7;
        text-align: center;
    }
    ReadingScreen Button {
        width: 24;
        margin: 0 1;
    }
    ReadingScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self, spread_key: str, question: str) -> None:
        super().__init__()
        self._spread_key = spread_key
        self._question = question
        self._drawn_cards: list[DrawnCard] = []
        self._wait_idx = 0
        self._wait_timer: Timer | None = None
        self._dot_timer: Timer | None = None
        self._dot_idx = 0
        self._last_preview_id: str | None = None
        self._cancelled = False

    def compose(self) -> ComposeResult:
        yield Static(f"🔮 {self._question}", id="question-display")
        yield Static("", id="spread-label")
        with Horizontal(id="main-area"):
            with VerticalScroll(id="cards-container"):
                pass
            with Vertical(id="card-preview"):
                yield Static("选择一张牌查看详情", id="preview-placeholder")
        with Center(id="actions"):
            yield Button("📖 解读", id="interpret", variant="primary")
            yield Button("🔀 重新抽牌", id="reshuffle")
            yield Button("🏠 返回首页", id="home")
        yield Static("↑↓ 选牌 · Tab 切换面板 · Enter 详情 · I 解读 · R 重新抽牌 · Esc 返回首页", id="hints")

    def on_mount(self) -> None:
        """Draw cards from the deck and mount animated CardWidgets."""
        self._draw_and_mount(animation_enabled=self.app.animation_enabled)

    def on_unmount(self) -> None:
        """Stop waiting animation timers when screen is removed."""
        if self._wait_timer is not None:
            self._wait_timer.stop()
            self._wait_timer = None
        if self._dot_timer is not None:
            self._dot_timer.stop()
            self._dot_timer = None

    def _draw_and_mount(self, animation_enabled: bool = True) -> None:
        """Shuffle, draw cards, and mount CardWidgets (used for initial draw and reshuffle)."""
        spread = get_spread(self._spread_key)
        deck = Deck()
        deck.shuffle()
        app = self.app
        spread.draw(deck, reversal_prob=app.reversal_prob)
        self._drawn_cards = spread.drawn_cards
        self._last_preview_id = None

        # Update app-level spread info and screen label
        app.spread_name = spread.name
        app.spread_name_zh = spread.name_zh
        label = f"【{spread.name_zh}】"
        if spread.description:
            label += f"  {spread.description}"
        n_up = sum(1 for dc in self._drawn_cards if not dc.is_reversed)
        n_rev = len(self._drawn_cards) - n_up
        if n_rev > 0:
            label += f"  ·  正位 {n_up} · 逆位 {n_rev}"
        self.query_one("#spread-label", Static).update(label)

        # Reset preview panel
        preview = self.query_one("#card-preview")
        preview.remove_children()
        preview.mount(Static("选择一张牌查看详情"))

        # Clear and repopulate card list
        container = self.query_one("#cards-container")
        container.remove_children()
        mode = app.render_mode

        for i, dc in enumerate(self._drawn_cards):
            widget = CardWidget(dc, render_mode=mode)
            container.mount(widget)
            if animation_enabled:
                self.set_timer(
                    max(i * 0.15, 0.01),
                    lambda w=widget: self._reveal_card(w),
                )

        if animation_enabled:
            self.set_timer(len(self._drawn_cards) * 0.15 + 0.5, self._on_cards_revealed)
        else:
            self._focus_first_card()

    def _focus_first_card(self) -> None:
        cards = list(self.query(CardWidget))
        if cards:
            cards[0].focus()

    def _on_cards_revealed(self) -> None:
        """Called after all card reveal animations complete."""
        self._focus_first_card()

    @staticmethod
    def _reveal_card(widget: CardWidget) -> None:
        widget.run_worker(animate_reveal(widget))

    def _show_waiting(self) -> None:
        """Replace action buttons with rotating cat-themed waiting messages."""
        self.query_one("#interpret").display = False
        self.query_one("#reshuffle").display = False
        self.query_one("#home").display = False
        actions = self.query_one("#actions")
        self._wait_idx = 0
        self._dot_idx = 0
        actions.mount(Static(self._waiting_text(0), id="waiting-msg"))
        self._wait_timer = self.set_interval(2.0, self._tick_waiting)
        self._dot_timer = self.set_interval(0.08, self._tick_dots)
        self.query_one("#hints", Static).update("AI 解读中… · Esc 取消")

    def _waiting_text(self, msg_idx: int) -> str:
        """Format a waiting message with the current spinner dot."""
        return f"{_WAITING_DOTS[self._dot_idx]}  {CAT_WAITING_MESSAGES[msg_idx]}"

    def _tick_waiting(self) -> None:
        """Cycle to the next cat-themed waiting message."""
        self._wait_idx = (self._wait_idx + 1) % len(CAT_WAITING_MESSAGES)
        try:
            self.query_one("#waiting-msg", Static).update(
                self._waiting_text(self._wait_idx)
            )
        except NoMatches:
            pass

    def _tick_dots(self) -> None:
        """Cycle the spinner dot for a live-loading feel."""
        self._dot_idx = (self._dot_idx + 1) % len(_WAITING_DOTS)
        try:
            self.query_one("#waiting-msg", Static).update(
                self._waiting_text(self._wait_idx)
            )
        except NoMatches:
            pass

    def _hide_waiting(self) -> None:
        """Stop waiting animation and restore action buttons."""
        if self._wait_timer is not None:
            self._wait_timer.stop()
            self._wait_timer = None
        if self._dot_timer is not None:
            self._dot_timer.stop()
            self._dot_timer = None
        try:
            self.query_one("#waiting-msg", Static).remove()
        except NoMatches:  # widget may already be gone during unmount
            pass
        self.query_one("#interpret").display = True
        self.query_one("#reshuffle").display = True
        self.query_one("#home").display = True
        self.query_one("#hints", Static).update(
            "↑↓ 选牌 · Tab 切换面板 · Enter 详情 · I 解读 · R 重新抽牌 · Esc 返回首页"
        )

    def on_card_widget_selected(self, event: CardWidget.Selected) -> None:
        """Update the detail preview and mark the selected card."""
        dc = event.drawn_card
        preview_id = f"{dc.card.id}:{dc.is_reversed}"
        if self._last_preview_id == preview_id:
            return
        self._last_preview_id = preview_id
        for w in self.query(CardWidget):
            w.remove_class("selected")
        event.widget.add_class("selected")
        preview = self.query_one("#card-preview")
        preview.remove_children()
        if self.app.render_mode != "text":
            img_detail = render_card_image_detail(dc)
            if img_detail:
                preview.mount(Static(img_detail))
                return
        preview.mount(Static(render_card_detail(dc)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle interpret, reshuffle, and home button clicks."""
        if event.button.id == "home":
            go_home(self)
        elif event.button.id == "interpret":
            self._do_interpret()
        elif event.button.id == "reshuffle":
            self._do_reshuffle()

    @property
    def _is_waiting(self) -> bool:
        """Whether AI interpretation is in progress."""
        return self._wait_timer is not None

    def action_interpret(self) -> None:
        """I key binding — trigger AI interpretation."""
        if not self._is_waiting:
            self._do_interpret()

    def action_reshuffle(self) -> None:
        """R key binding — reshuffle and redraw all cards."""
        if not self._is_waiting:
            self._do_reshuffle()

    def _do_reshuffle(self) -> None:
        """Clear cards, reshuffle the deck, and redraw."""
        animation_enabled = self.app.animation_enabled
        self._draw_and_mount(animation_enabled=animation_enabled)

    def action_handle_escape(self) -> None:
        """Cancel interpretation if waiting, otherwise go home."""
        if self._is_waiting:
            self._cancelled = True
            self._hide_waiting()
        else:
            go_home(self)

    def _do_interpret(self) -> None:
        """Trigger AI (or template fallback) interpretation in a background worker."""
        self._cancelled = False
        self._show_waiting()
        self.run_worker(self._run_interpretation(), exclusive=True)

    def key_down(self) -> None:
        """Move focus to the next CardWidget."""
        if isinstance(self.focused, CardWidget):
            focus_sibling(self, CardWidget, 1)

    def key_up(self) -> None:
        """Move focus to the previous CardWidget."""
        if isinstance(self.focused, CardWidget):
            focus_sibling(self, CardWidget, -1)

    def key_tab(self, event: Key) -> None:
        """Cycle focus: if on a card, go to first button; if on button, go to first card."""
        event.stop()
        if isinstance(self.focused, CardWidget):
            buttons = list(self.query(Button))
            if buttons:
                buttons[0].focus()
        elif isinstance(self.focused, Button):
            cards = list(self.query(CardWidget))
            if cards:
                cards[0].focus()

    async def _run_interpretation(self) -> None:
        """Run interpretation off-thread, fall back to template on any error."""
        try:
            config = self.app.config
            interp = get_interpreter(config)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, interp.interpret, self._drawn_cards, self._question
            )
        except Exception as exc:
            log.warning("AI interpretation failed, using template: %s", exc)
            result = template_interpret(self._drawn_cards, self._question)
        # Guard: screen may have been popped or interpretation cancelled
        if not self.is_mounted or self._cancelled:
            return
        self._hide_waiting()
        self.app.push_screen(InterpretationScreen(
            result, self._drawn_cards, self._question,
            spread_name=self.app.spread_name,
            spread_name_zh=self.app.spread_name_zh,
        ))
