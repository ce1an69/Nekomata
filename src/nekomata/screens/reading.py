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

    def __init__(self, drawn: DrawnCard) -> None:
        self._drawn = drawn
        img_panel = render_card_image(drawn)
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
        spread.draw(deck)
        self._drawn_cards = spread.drawn_cards

        container = self.query_one("#cards-container")
        for dc in self._drawn_cards:
            container.mount(CardWidget(dc))

        self.app.spread_name = spread.name
        self.app.spread_name_zh = spread.name_zh

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
            from nekomata.ai.interpreter import template_interpret
            from nekomata.screens.interpretation import InterpretationScreen
            interp = template_interpret(self._drawn_cards, self._question)
            self.app.push_screen(InterpretationScreen(interp, self._drawn_cards, self._question))
