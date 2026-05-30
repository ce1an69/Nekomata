"""Card browser screen — browse and filter all 78 tarot cards."""

from rich.panel import Panel
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.data import load_all_cards
from nekomata.card.types import ROMAN, Arcana, Card, DrawnCard, Position
from nekomata.i18n import arcana_label, lazy_section, ui_section
from nekomata.render.animations import animate_entrance
from nekomata.render.card_renderer import (
    _build_detail_text,
    create_card_origin_widget,
)
from nekomata.render.styles import (
    C_BASE,
    C_CRUST,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_SURFACE0,
    C_SURFACE1,
    C_TEXT,
)

_STR = lazy_section("card_browser")

_SUIT_ARCANAS = [
    None,
    Arcana.MAJOR,
    Arcana.CUPS,
    Arcana.WANDS,
    Arcana.SWORDS,
    Arcana.PENTACLES,
]
_ARCANA_KEYS = ["all", "major", "cups", "wands", "swords", "pentacles"]

# Reusable position for card browser preview
_BROWSER_POS = Position(name="Browser", name_zh="浏览", description="Card browser")


class CardBrowserScreen(Screen):
    """Browse and filter all 78 tarot cards with detail preview."""

    BINDINGS = [
        ("r", "toggle_reversal", "Reversal"),
        ("escape", "go_back", "Back"),
    ]

    DEFAULT_CSS = f"""
    CardBrowserScreen {{
        align: center top;
    }}
    CardBrowserScreen #filter-bar {{
        align: center middle;
        height: auto;
        margin: 0 0 1 0;
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 0 1;
        transition: opacity 300ms out_quint, offset 300ms out_quint;
    }}
    CardBrowserScreen #filter-bar Button {{
        width: auto;
        min-width: 10;
        margin: 0 1;
        background: {C_SURFACE0};
        border: round {C_SURFACE0};
        color: {C_OVERLAY0};
    }}
    CardBrowserScreen #filter-bar Button:focus {{
        background: {C_SURFACE1};
        border: round {C_MAUVE};
        color: {C_MAUVE};
    }}
    CardBrowserScreen #filter-bar Button.active-filter {{
        background: {C_MANTLE};
        border: round {C_MAUVE};
        color: {C_MAUVE};
        text-style: bold;
    }}
    CardBrowserScreen #card-count {{
        width: 100%;
        height: auto;
        color: {C_OVERLAY0};
        text-align: center;
        margin-bottom: 0;
    }}
    CardBrowserScreen #browser-area {{
        height: 1fr;
        transition: opacity 300ms out_quint, offset 300ms out_quint;
    }}
    CardBrowserScreen #card-list {{
        width: 1fr;
        height: 1fr;
        border: round {C_SURFACE0};
        background: {C_CRUST};
        padding: 1 1;
        transition: opacity 220ms out_quint;
    }}
    CardBrowserScreen #card-detail {{
        width: 1fr;
        height: 1fr;
        border: round {C_SURFACE1};
        background: {C_MANTLE};
        padding: 1 2;
        margin-left: 1;
        align: center top;
        scrollbar-gutter: stable;
    }}
    CardBrowserScreen #card-detail .card-origin-frame {{
        width: 100%;
        height: 26;
        align: center middle;
        background: {C_CRUST};
        border: round {C_SURFACE1};
        padding: 1 1;
        transition: opacity 160ms out_quint;
    }}
    CardBrowserScreen #card-detail .card-origin {{
        width: auto;
        height: 100%;
        background: {C_CRUST};
    }}
    CardBrowserScreen #detail-text-slot {{
        width: 100%;
        height: auto;
        transition: opacity 160ms out_quint;
    }}
    CardBrowserScreen #card-detail Static {{
        background: {C_MANTLE};
    }}
    CardBrowserScreen #hints {{
        width: 100%;
        height: auto;
        color: {C_OVERLAY0};
        text-align: center;
        margin-top: 1;
    }}
    """

    def __init__(self) -> None:
        super().__init__()
        self._cards = load_all_cards()
        self._reversed_preview = False
        self._active_arcana: Arcana | None = None
        self._detail_preview_id: str | None = None

    def compose(self) -> ComposeResult:
        labels = ui_section("arcana_labels")
        with Horizontal(id="filter-bar"):
            for key, arcana in zip(_ARCANA_KEYS, _SUIT_ARCANAS):
                btn_id = f"filter-{arcana.value}" if arcana else "filter-all"
                button = Button(labels[key], id=btn_id)
                if btn_id == "filter-all":
                    button.add_class("active-filter")
                yield button
        yield Static(f"{len(self._cards)} cards", id="card-count")
        with Horizontal(id="browser-area"):
            with VerticalScroll(id="card-list"):
                pass
            with VerticalScroll(id="card-detail"):
                with Horizontal(id="detail-image-slot", classes="card-origin-frame"):
                    pass
                yield Static(_STR["select_placeholder"], id="detail-text-slot")
        yield Static(_STR["hints"], id="hints")

    def on_mount(self) -> None:
        """Populate card list, focus the first item, and animate entrance."""
        container = self.query_one("#card-list")
        container.mount(*(CardListItem(card) for card in self._cards))
        animate_entrance(self.query_one("#filter-bar"), duration=0.3, dy=-1)
        animate_entrance(self.query_one("#browser-area"), duration=0.35)
        self.set_timer(0.1, self._focus_first_visible_card)

    def _focus_first_visible_card(self) -> None:
        for item in self.query(CardListItem):
            if item.display:
                item.focus()
                return

    def _apply_filter(self, arcana: Arcana | None) -> None:
        """Toggle visibility of card items to match the selected suit filter."""
        self._active_arcana = arcana
        self._update_card_count_display()
        container = self.query_one("#card-list")
        if self.app.animation_enabled:
            container.styles.opacity = 0.2
        for item in self.query(CardListItem):
            item.display = arcana is None or item._card.arcana == arcana
        if self.app.animation_enabled:
            container.styles.animate("opacity", 1.0, duration=0.18, easing="out_quint")
        self.set_timer(0.05, self._focus_first_visible_card)

    def _update_filter_highlight(self, active_btn_id: str) -> None:
        """Highlight the active filter button and dim all others."""
        for arcana in _SUIT_ARCANAS:
            btn_id = f"filter-{arcana.value}" if arcana else "filter-all"
            btn = self.query_one(f"#{btn_id}", Button)
            btn.set_class(btn_id == active_btn_id, "active-filter")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle filter button clicks."""
        btn_id = event.button.id

        for i, arcana in enumerate(_SUIT_ARCANAS):
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
        filtered = [
            c
            for c in self._cards
            if self._active_arcana is None or c.arcana == self._active_arcana
        ]
        rev_label = _STR["reversed_preview"] if self._reversed_preview else ""
        count.update(
            _STR["card_count"].format(filtered=len(filtered), total=len(self._cards))
            + rev_label
        )

    def key_down(self) -> None:
        if isinstance(self.focused, CardListItem):
            self._focus_next_visible_card(1)

    def key_up(self) -> None:
        if isinstance(self.focused, CardListItem):
            self._focus_next_visible_card(-1)

    def key_left(self) -> None:
        self._cycle_filter(-1)

    def key_right(self) -> None:
        self._cycle_filter(1)

    def _cycle_filter(self, delta: int) -> None:
        """Switch filter tab left or right."""
        current_idx = 0
        for i, arcana in enumerate(_SUIT_ARCANAS):
            if arcana == self._active_arcana:
                current_idx = i
                break
        new_idx = (current_idx + delta) % len(_SUIT_ARCANAS)
        self._apply_filter_by_index(new_idx)

    def _focus_next_visible_card(self, delta: int) -> None:
        items = [i for i in self.query(CardListItem) if i.display]
        if not items or not isinstance(self.focused, CardListItem):
            return
        try:
            idx = items.index(self.focused)
        except ValueError:
            items[0].focus()
            return
        new_idx = idx + delta
        if 0 <= new_idx < len(items):
            items[new_idx].focus()

    def key_tab(self, event: Key) -> None:
        """Cycle focus: cards → filter buttons → cards."""
        event.stop()
        filter_buttons = list(self.query("#filter-bar Button"))
        visible_items = [i for i in self.query(CardListItem) if i.display]

        if isinstance(self.focused, CardListItem):
            if filter_buttons:
                filter_buttons[0].focus()
            return

        if not isinstance(self.focused, Button):
            return

        focused_id = self.focused.id or ""
        if focused_id.startswith("filter-"):
            try:
                idx = filter_buttons.index(self.focused)
            except ValueError:
                idx = -1
            if idx < len(filter_buttons) - 1:
                filter_buttons[idx + 1].focus()
            else:
                if visible_items:
                    visible_items[0].focus()
        else:
            if visible_items:
                visible_items[0].focus()

    def _apply_filter_by_index(self, index: int) -> None:
        """Apply a suit filter by index into SUIT_FILTERS."""
        if 0 <= index < len(_SUIT_ARCANAS):
            arcana = _SUIT_ARCANAS[index]
            filter_id = f"filter-{arcana.value}" if arcana else "filter-all"
            self._update_filter_highlight(filter_id)
            self._show_placeholder_detail()
            self._apply_filter(arcana)

    def _show_placeholder_detail(self) -> None:
        """Reset the detail panel to the placeholder."""
        self._detail_preview_id = None
        self.query_one("#detail-image-slot").remove_children()
        self.query_one("#detail-text-slot", Static).update(_STR["select_placeholder"])


class CardListItem(Static):
    """A focusable list item representing a single card in the browser."""

    can_focus = True

    DEFAULT_CSS = f"""
    CardListItem {{
        padding: 0 1;
        height: auto;
        border: round {C_CRUST};
        background: {C_CRUST};
        transition: background 180ms, border 180ms, color 180ms, opacity 250ms out_quint;
    }}
    CardListItem:focus {{
        background: {C_BASE};
        color: {C_MAUVE};
        text-style: bold;
        border: round {C_MAUVE};
    }}
    CardListItem:hover {{
        background: {C_BASE};
    }}
    CardListItem.selected {{
        background: {C_MANTLE};
        border: round {C_MAUVE};
    }}
    CardListItem.selected:focus {{
        background: {C_BASE};
        color: {C_MAUVE};
        text-style: bold;
    }}
    """

    def __init__(self, card: Card) -> None:
        self._card = card
        suit = arcana_label(card.arcana.value)
        num = (
            ROMAN[card.number]
            if card.arcana == Arcana.MAJOR and card.number < len(ROMAN)
            else str(card.number)
        )
        super().__init__(f"{num:>3s}  {card.name} [{suit}]")

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
        drawn = DrawnCard(
            card=self._card, position=_BROWSER_POS, is_reversed=is_reversed
        )
        preview_id = f"{drawn.card.id}:{drawn.is_reversed}"
        if self.screen._detail_preview_id == preview_id:
            return
        self.screen._detail_preview_id = preview_id

        image_slot = self.screen.query_one("#detail-image-slot")
        text_slot = self.screen.query_one("#detail-text-slot", Static)
        if self.app.animation_enabled:
            image_slot.styles.opacity = 0.35
            text_slot.styles.opacity = 0.35
        image_slot.remove_children()

        if self.app.render_mode != "text":
            img_widget = create_card_origin_widget(drawn)
            if img_widget is not None:
                image_slot.mount(img_widget)

        text_slot.update(
            Panel(
                _build_detail_text(drawn, self.app.config.lang, orientation_only=True),
                border_style="none",
                padding=(0, 0),
            )
        )
        if self.app.animation_enabled:
            image_slot.styles.animate("opacity", 1.0, duration=0.16, easing="out_quint")
            text_slot.styles.animate("opacity", 1.0, duration=0.16, easing="out_quint")
        self.screen.query_one("#card-detail").scroll_home(animate=False)
