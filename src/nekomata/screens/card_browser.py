"""Card browser screen — browse and filter all 78 tarot cards."""

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.data import load_all_cards
from nekomata.card.types import Arcana, ARCANA_ZH, Card, DrawnCard, Position
from nekomata.render.card_renderer import render_card_detail, render_card_image_detail
from nekomata.screens.widgets import focus_sibling

# Roman numerals for Major Arcana display
_ROMAN = [
    "0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
]

SUIT_FILTERS = [
    ("全部", None),
    ("大阿卡纳", Arcana.MAJOR),
    ("圣杯", Arcana.CUPS),
    ("权杖", Arcana.WANDS),
    ("宝剑", Arcana.SWORDS),
    ("星币", Arcana.PENTACLES),
]

# Reusable position for card browser preview (avoids creating one per focus)
_BROWSER_POS = Position(name="Browser", name_zh="浏览", description="牌库浏览")


class CardBrowserScreen(Screen):
    """Browse and filter all 78 tarot cards with detail preview."""

    BINDINGS = [
        ("r", "toggle_reversal", "逆位"),
        ("escape", "go_back", "返回"),
    ]

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
    CardBrowserScreen #filter-bar Button.active-filter {
        border: tall #cba6f7;
        color: #cba6f7;
    }
    CardBrowserScreen #card-count {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-bottom: 0;
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
        border: round #45475a;
        padding: 1 2;
    }
    CardBrowserScreen #back-bar {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    CardBrowserScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._cards = load_all_cards()
        self._reversed_preview = False
        self._active_arcana: Arcana | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="filter-bar"):
            for label, arcana in SUIT_FILTERS:
                btn_id = f"filter-{arcana.value}" if arcana else "filter-all"
                button = Button(label, id=btn_id)
                if btn_id == "filter-all":
                    button.add_class("active-filter")
                yield button
        yield Static(f"共 {len(self._cards)} 张", id="card-count")
        with Horizontal(id="browser-area"):
            with VerticalScroll(id="card-list"):
                pass
            with Vertical(id="card-detail"):
                yield Static("选择一张牌查看详情", id="detail-placeholder")
        with Center(id="back-bar"):
            yield Button("↩ 返回", id="back")
        yield Static("↑↓ 浏览 · Tab 切换面板 · R 切换逆位 · Alt+1~6 筛选 · Esc 返回", id="hints")

    def on_mount(self) -> None:
        """Populate card list and focus the first item."""
        self._show_cards(self._cards)
        self.set_timer(0.1, self._focus_first_card)

    def _focus_first_card(self) -> None:
        items = list(self.query(CardListItem))
        if items:
            items[0].focus()

    def _show_cards(self, cards: list[Card]) -> None:
        """Replace the card list with the given cards."""
        self._update_card_count_display()
        container = self.query_one("#card-list")
        container.remove_children()
        for card in cards:
            container.mount(CardListItem(card))

    def _update_filter_highlight(self, active_btn_id: str) -> None:
        """Highlight the active filter button and dim all others."""
        for _, arcana in SUIT_FILTERS:
            btn_id = f"filter-{arcana.value}" if arcana else "filter-all"
            btn = self.query_one(f"#{btn_id}", Button)
            btn.set_class(btn_id == active_btn_id, "active-filter")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle filter and back button clicks."""
        btn_id = event.button.id
        if btn_id == "back":
            self.app.pop_screen()
            return

        for i, (_, arcana) in enumerate(SUIT_FILTERS):
            filter_id = f"filter-{arcana.value}" if arcana else "filter-all"
            if btn_id == filter_id:
                self._apply_filter_by_index(i)
                return

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_toggle_reversal(self) -> None:
        """R key binding — toggle reversed preview and refresh the detail panel."""
        self._reversed_preview = not self._reversed_preview
        self._update_card_count_display()
        if isinstance(self.focused, CardListItem):
            self.focused._show_detail()

    def _update_card_count_display(self) -> None:
        """Update the card count line to reflect current filter and reversal state."""
        count = self.query_one("#card-count", Static)
        filtered = [c for c in self._cards if self._active_arcana is None or c.arcana == self._active_arcana]
        rev_label = "  [↕ 逆位预览]" if self._reversed_preview else ""
        count.update(f"显示 {len(filtered)}/{len(self._cards)} 张{rev_label}")

    def key_down(self) -> None:
        if isinstance(self.focused, CardListItem):
            focus_sibling(self, CardListItem, 1)

    def key_up(self) -> None:
        if isinstance(self.focused, CardListItem):
            focus_sibling(self, CardListItem, -1)

    def key_tab(self, event: Key) -> None:
        """Cycle focus: cards → filter buttons → back button → cards."""
        event.stop()
        filter_buttons = list(self.query("#filter-bar Button"))

        if isinstance(self.focused, CardListItem):
            if filter_buttons:
                filter_buttons[0].focus()
            return

        if not isinstance(self.focused, Button):
            return

        focused_id = self.focused.id or ""
        if focused_id == "back":
            # Back button → wrap to first card
            items = list(self.query(CardListItem))
            if items:
                items[0].focus()
        elif focused_id.startswith("filter-"):
            # Advance through filter buttons, then to back
            try:
                idx = filter_buttons.index(self.focused)
            except ValueError:
                idx = -1
            if idx < len(filter_buttons) - 1:
                filter_buttons[idx + 1].focus()
            else:
                self.query_one("#back", Button).focus()
        else:
            items = list(self.query(CardListItem))
            if items:
                items[0].focus()

    def _apply_filter_by_index(self, index: int) -> None:
        """Apply a suit filter by index into SUIT_FILTERS."""
        if 0 <= index < len(SUIT_FILTERS):
            _, arcana = SUIT_FILTERS[index]
            self._active_arcana = arcana
            filter_id = f"filter-{arcana.value}" if arcana else "filter-all"
            filtered = [c for c in self._cards if c.arcana == arcana] if arcana else self._cards
            self._update_filter_highlight(filter_id)
            # Clear detail panel to avoid stale card from previous filter
            detail = self.query_one("#card-detail")
            detail.remove_children()
            detail.mount(Static("选择一张牌查看详情"))
            self._show_cards(filtered)
            self.set_timer(0.1, self._focus_first_card)

    def key_alt_1(self) -> None: self._apply_filter_by_index(0)
    def key_alt_2(self) -> None: self._apply_filter_by_index(1)
    def key_alt_3(self) -> None: self._apply_filter_by_index(2)
    def key_alt_4(self) -> None: self._apply_filter_by_index(3)
    def key_alt_5(self) -> None: self._apply_filter_by_index(4)
    def key_alt_6(self) -> None: self._apply_filter_by_index(5)


class CardListItem(Static):
    """A focusable list item representing a single card in the browser."""

    can_focus = True

    DEFAULT_CSS = """
    CardListItem {
        padding: 0 1;
        height: auto;
    }
    CardListItem:focus {
        background: #313244;
        color: #cba6f7;
        text-style: bold;
    }
    CardListItem:hover {
        background: #313244;
    }
    CardListItem.selected {
        background: #181825;
        border-left: tall #f9e2af;
    }
    CardListItem.selected:focus {
        background: #313244;
        color: #cba6f7;
        text-style: bold;
    }
    """

    def __init__(self, card: Card) -> None:
        self._card = card
        suit = ARCANA_ZH.get(card.arcana, card.arcana.value)
        num = _ROMAN[card.number] if card.arcana == Arcana.MAJOR and card.number < len(_ROMAN) else str(card.number)
        super().__init__(f"{num:>3s}  {card.name_zh} ({card.name}) [{suit}]")

    def on_click(self) -> None:
        self._show_detail()

    def on_focus(self) -> None:
        self._show_detail()

    def key_enter(self) -> None:
        self._show_detail()

    def _show_detail(self) -> None:
        """Render this card's detail preview in the side panel."""
        for item in self.screen.query(CardListItem):
            item.remove_class("selected")
        self.add_class("selected")
        is_reversed = self.screen._reversed_preview
        drawn = DrawnCard(card=self._card, position=_BROWSER_POS, is_reversed=is_reversed)
        detail_panel = self.screen.query_one("#card-detail")
        detail_panel.remove_children()
        if self.app.render_mode != "text":
            img_detail = render_card_image_detail(drawn)
            if img_detail:
                detail_panel.mount(Static(img_detail))
                return
        detail_panel.mount(Static(render_card_detail(drawn)))
