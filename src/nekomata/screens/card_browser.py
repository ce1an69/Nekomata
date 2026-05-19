"""Card browser screen — browse and filter all 78 tarot cards."""

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.css.scalar import ScalarOffset
from textual.events import Key
from textual.geometry import Offset
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.data import load_all_cards
from nekomata.card.types import Arcana, ARCANA_ZH, Card, DrawnCard, Position
from nekomata.render.animations import animate_fade_in
from nekomata.render.card_renderer import render_card_detail, render_card_image_detail
from nekomata.render.styles import (
    C_CRUST,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_SUBTEXT0,
    C_SURFACE0,
    C_SURFACE1,
    C_TEXT,
)
from nekomata.screens.widgets import focus_sibling

# Roman numerals for Major Arcana display
_ROMAN = [
    "0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
]

SUIT_FILTERS = [
    ("All", None),
    ("Major", Arcana.MAJOR),
    ("Cups", Arcana.CUPS),
    ("Wands", Arcana.WANDS),
    ("Swords", Arcana.SWORDS),
    ("Pentacles", Arcana.PENTACLES),
]

# Reusable position for card browser preview
_BROWSER_POS = Position(name="Browser", name_zh="Browser", description="Card browser")


class CardBrowserScreen(Screen):
    """Browse and filter all 78 tarot cards with detail preview."""

    BINDINGS = [
        ("r", "toggle_reversal", "Reversal"),
        ("q", "go_back", "Back"),
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
        transition: opacity 300ms out_cubic, offset 300ms out_cubic;
    }}
    CardBrowserScreen #filter-bar Button {{
        width: auto;
        min-width: 10;
        margin: 0 1;
        transition: background 180ms, border 180ms, color 180ms;
    }}
    CardBrowserScreen #filter-bar Button.active-filter {{
        border: round {C_MAUVE};
        color: {C_MAUVE};
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
        transition: opacity 300ms out_cubic, offset 300ms out_cubic;
    }}
    CardBrowserScreen #card-list {{
        width: 1fr;
        height: 1fr;
        border: round {C_SURFACE0};
        background: {C_CRUST};
        padding: 1 1;
        transition: opacity 220ms out_cubic;
    }}
    CardBrowserScreen #card-detail {{
        width: 1fr;
        height: 1fr;
        border: round {C_SURFACE1};
        background: {C_MANTLE};
        padding: 1 2;
        margin-left: 1;
        transition: opacity 250ms out_cubic;
    }}
    CardBrowserScreen #card-detail Static {{
        background: {C_MANTLE};
    }}
    CardBrowserScreen #back-bar {{
        align: center middle;
        height: auto;
        margin-top: 1;
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

    def compose(self) -> ComposeResult:
        with Horizontal(id="filter-bar"):
            for label, arcana in SUIT_FILTERS:
                btn_id = f"filter-{arcana.value}" if arcana else "filter-all"
                button = Button(label, id=btn_id)
                if btn_id == "filter-all":
                    button.add_class("active-filter")
                yield button
        yield Static(f"{len(self._cards)} cards", id="card-count")
        with Horizontal(id="browser-area"):
            with VerticalScroll(id="card-list"):
                pass
            with Vertical(id="card-detail"):
                yield Static("Select a card", id="detail-placeholder")
        with Center(id="back-bar"):
            yield Button("Back", id="back")
        yield Static("↑/↓ move · Enter inspect · R reversal · Q back", id="hints")

    def on_mount(self) -> None:
        """Populate card list, focus the first item, and animate entrance."""
        self._show_cards(self._cards)
        if self.app.animation_enabled:
            filter_bar = self.query_one("#filter-bar")
            filter_bar.styles.opacity = 0
            filter_bar.styles.offset = (0, -1)
            filter_bar.styles.animate("opacity", 1.0, duration=0.3, easing="out_cubic")
            filter_bar.styles.animate("offset", ScalarOffset.from_offset(Offset(0, 0)), duration=0.3, easing="out_cubic")
            browser_area = self.query_one("#browser-area")
            browser_area.styles.opacity = 0
            browser_area.styles.offset = (0, 1)
            browser_area.styles.animate("opacity", 1.0, duration=0.35, easing="out_cubic")
            browser_area.styles.animate("offset", ScalarOffset.from_offset(Offset(0, 0)), duration=0.35, easing="out_cubic")
        self.set_timer(0.1, self._focus_first_card)

    def _focus_first_card(self) -> None:
        items = list(self.query(CardListItem))
        if items:
            items[0].focus()

    def _show_cards(self, cards: list[Card], *, animate: bool = False) -> None:
        """Replace the card list with the given cards."""
        self._update_card_count_display()
        container = self.query_one("#card-list")
        if animate and self.app.animation_enabled:
            container.styles.opacity = 0.2
        container.remove_children()
        items = [CardListItem(card) for card in cards]
        container.mount(*items)
        if animate and self.app.animation_enabled:
            container.styles.animate("opacity", 1.0, duration=0.18, easing="out_cubic")

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
        rev_label = "  (reversed preview)" if self._reversed_preview else ""
        count.update(f"{len(filtered)}/{len(self._cards)} cards{rev_label}")

    def key_down(self) -> None:
        if isinstance(self.focused, CardListItem):
            focus_sibling(self, CardListItem, 1)

    def key_up(self) -> None:
        if isinstance(self.focused, CardListItem):
            focus_sibling(self, CardListItem, -1)

    def key_left(self) -> None:
        """Move left across filters or upward through cards."""
        if isinstance(self.focused, CardListItem):
            focus_sibling(self, CardListItem, -1)
        elif isinstance(self.focused, Button) and (self.focused.id or "").startswith("filter-"):
            focus_sibling(self, Button, -1)

    def key_right(self) -> None:
        """Move right across filters or downward through cards."""
        if isinstance(self.focused, CardListItem):
            focus_sibling(self, CardListItem, 1)
        elif isinstance(self.focused, Button) and (self.focused.id or "").startswith("filter-"):
            focus_sibling(self, Button, 1)

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
            items = list(self.query(CardListItem))
            if items:
                items[0].focus()
        elif focused_id.startswith("filter-"):
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
            self._show_placeholder_detail()
            self._show_cards(filtered, animate=True)
            self.set_timer(0.1, self._focus_first_card)

    def _show_placeholder_detail(self) -> None:
        """Reset the detail panel with the same soft swap used for card previews."""
        detail = self.query_one("#card-detail")
        if self.app.animation_enabled:
            detail.styles.opacity = 0.2
        detail.remove_children()
        detail.mount(Static("Select a card"))
        if self.app.animation_enabled:
            detail.styles.animate("opacity", 1.0, duration=0.18, easing="out_cubic")


class CardListItem(Static):
    """A focusable list item representing a single card in the browser."""

    can_focus = True

    DEFAULT_CSS = f"""
    CardListItem {{
        padding: 0 1;
        height: auto;
        border: round {C_CRUST};
        background: {C_CRUST};
        transition: background 180ms, border 180ms, color 180ms, opacity 250ms out_cubic;
    }}
    CardListItem:focus {{
        background: #1e1e2e;
        color: {C_MAUVE};
        text-style: bold;
        border: round {C_MAUVE};
    }}
    CardListItem:hover {{
        background: #1e1e2e;
    }}
    CardListItem.selected {{
        background: {C_MANTLE};
        border: round {C_MAUVE};
    }}
    CardListItem.selected:focus {{
        background: #1e1e2e;
        color: {C_MAUVE};
        text-style: bold;
    }}
    """

    def __init__(self, card: Card) -> None:
        self._card = card
        suit = ARCANA_ZH.get(card.arcana, card.arcana.value)
        num = _ROMAN[card.number] if card.arcana == Arcana.MAJOR and card.number < len(_ROMAN) else str(card.number)
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
        drawn = DrawnCard(card=self._card, position=_BROWSER_POS, is_reversed=is_reversed)
        detail_panel = self.screen.query_one("#card-detail")
        if self.app.animation_enabled:
            detail_panel.styles.opacity = 0.2
        detail_panel.remove_children()
        if self.app.render_mode != "text":
            img_detail = render_card_image_detail(drawn)
            if img_detail:
                widget = Static(img_detail)
                detail_panel.mount(widget)
                if self.app.animation_enabled:
                    animate_fade_in(widget)
                    detail_panel.styles.animate("opacity", 1.0, duration=0.18, easing="out_cubic")
                return
        widget = Static(render_card_detail(drawn))
        detail_panel.mount(widget)
        if self.app.animation_enabled:
            animate_fade_in(widget)
            detail_panel.styles.animate("opacity", 1.0, duration=0.18, easing="out_cubic")
