from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.data import load_all_cards
from nekomata.card.types import Arcana, Card
from nekomata.render.card_renderer import render_card_detail, render_card_image_detail
from nekomata.card.types import Position, DrawnCard


SUIT_FILTERS = [
    ("全部", None),
    ("大阿卡纳", Arcana.MAJOR),
    ("圣杯", Arcana.CUPS),
    ("权杖", Arcana.WANDS),
    ("宝剑", Arcana.SWORDS),
    ("星币", Arcana.PENTACLES),
]


class CardBrowserScreen(Screen):
    DEFAULT_CSS = """
    CardBrowserScreen {
        align: center top;
    }
    CardBrowserScreen #filter-bar {
        align: center middle;
        height: auto;
        margin: 1 0;
    }
    CardBrowserScreen #filter-bar Button {
        width: auto;
        min-width: 10;
        margin: 0 1;
    }
    CardBrowserScreen #browser-area {
        height: 1fr;
    }
    CardBrowserScreen #card-list {
        width: 1fr;
        height: 1fr;
    }
    CardBrowserScreen #card-detail {
        width: 1fr;
        height: 1fr;
        border: round $primary;
        padding: 1 2;
    }
    CardBrowserScreen #back-bar {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._cards = load_all_cards()
        self._current_filter: Arcana | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="filter-bar"):
            for label, arcana in SUIT_FILTERS:
                btn_id = f"filter-{arcana.value}" if arcana else "filter-all"
                yield Button(label, id=btn_id)
        with Horizontal(id="browser-area"):
            with VerticalScroll(id="card-list"):
                pass
            with Vertical(id="card-detail"):
                yield Static("选择一张牌查看详情", id="detail-placeholder")
        with Center(id="back-bar"):
            yield Button("↩ 返回", id="back")

    def on_mount(self) -> None:
        self._show_cards(self._cards)

    def _show_cards(self, cards: list[Card]) -> None:
        container = self.query_one("#card-list")
        container.remove_children()
        for card in cards:
            widget = CardListItem(card)
            container.mount(widget)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "back":
            self.app.pop_screen()
            return

        for label, arcana in SUIT_FILTERS:
            filter_id = f"filter-{arcana.value}" if arcana else "filter-all"
            if btn_id == filter_id:
                self._current_filter = arcana
                filtered = (
                    [c for c in self._cards if c.arcana == arcana]
                    if arcana
                    else self._cards
                )
                self._show_cards(filtered)
                return


class CardListItem(Static):
    def __init__(self, card: Card) -> None:
        self._card = card
        status = f"[{card.arcana.value}]"
        super().__init__(f"{card.name_zh} ({card.name}) {status}")

    def on_click(self) -> None:
        fake_pos = Position(name="Browser", name_zh="浏览", description="牌库浏览")
        drawn = DrawnCard(card=self._card, position=fake_pos, is_reversed=False)
        browser = self.app.screen
        detail_panel = browser.query_one("#card-detail")
        detail_panel.remove_children()
        img_detail = render_card_image_detail(drawn)
        if img_detail:
            detail_panel.mount(Static(img_detail))
        else:
            detail_panel.mount(Static(render_card_detail(drawn)))
