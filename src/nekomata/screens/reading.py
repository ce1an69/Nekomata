from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.render.card_renderer import (
    render_card_text,
    render_card_detail,
    render_card_image,
    render_card_image_detail,
)
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult, BodyMindSpirit
from nekomata.spread.five_card import FiveCardCross
from nekomata.spread.celtic import CelticCross

CAT_WAITING_MESSAGES = [
    "Flipping through the book of fate… 🐱",
    "Meow~ the stars are aligning… ✨",
    "Ears perked, listening to the cosmos… 🌙",
    "Pondering the meaning of cat life… 🧶",
    "Cards fluttering between soft paws… 🃏",
    "Gazing into the crystal ball… 🔮",
    "Deciphering secrets by moonlight… 🌃",
    "Leaving paw prints on the star map… 🐾",
]


def get_spread(key: str) -> Spread:
    spreads = {
        "single": SingleCardSpread,
        "past_present_future": PastPresentFuture,
        "situation_action_result": SituationActionResult,
        "body_mind_spirit": BodyMindSpirit,
        "five_card_cross": FiveCardCross,
        "celtic_cross": CelticCross,
    }
    return spreads[key]()


class CardWidget(Static):
    class Selected(Message):
        def __init__(self, drawn_card: DrawnCard) -> None:
            super().__init__()
            self.drawn_card = drawn_card

    def __init__(self, drawn: DrawnCard, render_mode: str = "compact") -> None:
        self._drawn = drawn
        size = "compact" if render_mode == "text" else render_mode
        img_panel = render_card_image(drawn, size=size)
        super().__init__(img_panel if img_panel else render_card_text(drawn))

    def on_click(self) -> None:
        self.post_message(self.Selected(self._drawn))


class ReadingScreen(Screen):
    DEFAULT_CSS = """
    ReadingScreen {
        align: center top;
    }
    ReadingScreen #question-display {
        text-align: center;
        margin: 1 0;
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
        border: round $primary;
        padding: 1 2;
    }
    ReadingScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    ReadingScreen Button {
        width: 24;
        margin: 0 1;
    }
    """

    def __init__(self, spread_key: str, question: str) -> None:
        super().__init__()
        self._spread_key = spread_key
        self._question = question
        self._drawn_cards: list[DrawnCard] = []
        self._wait_idx = 0
        self._wait_timer = None

    def compose(self) -> ComposeResult:
        yield Static(f"🔮 {self._question}", id="question-display")
        with Horizontal(id="main-area"):
            with VerticalScroll(id="cards-container"):
                pass
            with Vertical(id="card-preview"):
                yield Static("点击左侧卡牌查看详情", id="preview-placeholder")
        with Center(id="actions"):
            yield Button("📖 解读", id="interpret", variant="primary")
            yield Button("🏠 返回首页", id="home")

    def on_mount(self) -> None:
        spread = get_spread(self._spread_key)
        deck = Deck()
        deck.shuffle()
        spread.draw(deck, reversal_prob=getattr(self.app, "reversal_prob", 0.5))
        self._drawn_cards = spread.drawn_cards

        container = self.query_one("#cards-container")
        mode = getattr(self.app, "render_mode", "compact")
        animation_enabled = getattr(self.app, "animation_enabled", True)

        for i, dc in enumerate(self._drawn_cards):
            widget = CardWidget(dc, render_mode=mode)
            container.mount(widget)
            if animation_enabled:
                self.set_timer(
                    i * 0.15,
                    lambda w=widget: self._reveal_card(w),
                )

        self.app.spread_name = spread.name
        self.app.spread_name_zh = spread.name_zh

    @staticmethod
    def _reveal_card(widget: CardWidget) -> None:
        from nekomata.render.animations import animate_reveal
        widget.run_worker(animate_reveal(widget))

    def _show_waiting(self) -> None:
        self.query_one("#interpret").display = False
        self.query_one("#home").display = False
        actions = self.query_one("#actions")
        actions.mount(Static(CAT_WAITING_MESSAGES[0], id="waiting-msg"))
        self._wait_idx = 0
        self._wait_timer = self.set_interval(2.0, self._tick_waiting)

    def _tick_waiting(self) -> None:
        self._wait_idx = (self._wait_idx + 1) % len(CAT_WAITING_MESSAGES)
        msg_widget = self.query_one("#waiting-msg", Static)
        msg_widget.update(CAT_WAITING_MESSAGES[self._wait_idx])

    def _hide_waiting(self) -> None:
        if self._wait_timer is not None:
            self._wait_timer.stop()
            self._wait_timer = None
        waiting = self.query_one("#waiting-msg", Static)
        waiting.remove()
        self.query_one("#interpret").display = True
        self.query_one("#home").display = True

    def on_card_widget_selected(self, event: CardWidget.Selected) -> None:
        preview = self.query_one("#card-preview")
        preview.remove_children()
        img_detail = render_card_image_detail(event.drawn_card)
        if img_detail:
            preview.mount(Static(img_detail))
        else:
            preview.mount(Static(render_card_detail(event.drawn_card)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home":
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        elif event.button.id == "interpret":
            self._show_waiting()
            self.run_worker(self._run_interpretation(), exclusive=True)

    async def _run_interpretation(self) -> None:
        from nekomata.ai.interpreter import get_interpreter, InterpretationError, template_interpret
        from nekomata.screens.interpretation import InterpretationScreen
        from nekomata.storage.config import AppConfig
        import asyncio

        config = AppConfig.load()
        interp = get_interpreter(config)
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, interp.interpret, self._drawn_cards, self._question
            )
        except InterpretationError:
            result = template_interpret(self._drawn_cards, self._question)
        self._hide_waiting()
        self.app.push_screen(InterpretationScreen(result, self._drawn_cards, self._question))
