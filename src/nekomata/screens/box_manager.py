"""Box-based focus navigation manager for the draw screen."""

from textual.css.query import NoMatches
from textual.widgets import Static

from nekomata.screens.draw_widgets import DeckCard, SpreadSlot

_BOX_SELECTORS = {
    "deck": "#deck-section",
    "spread": "#spread-area",
    "detail": "#card-preview",
    "interp": "#interp-dialog",
}


class BoxManager:
    """Manages focus cycling between logical box regions."""

    def __init__(self, screen, get_available_boxes) -> None:
        self._screen = screen
        self._get_available_boxes = get_available_boxes
        self.active_box: str | None = None
        self._last_card_widget: DeckCard | SpreadSlot | None = None

    def update_highlights(self) -> None:
        for box_id, selector in _BOX_SELECTORS.items():
            try:
                el = self._screen.query_one(selector)
                el.set_class(box_id == self.active_box, "box-active")
            except NoMatches:
                pass

    def on_focus_change(self, widget) -> str | None:
        if isinstance(widget, DeckCard):
            new_box = "deck"
        elif isinstance(widget, SpreadSlot):
            new_box = "spread"
        else:
            return None
        if new_box != self.active_box:
            self.active_box = new_box
            self.update_highlights()
        return new_box

    def cycle(self, delta: int) -> None:
        boxes = self._get_available_boxes()
        if len(boxes) <= 1:
            return
        self._save_last_card()
        current = self.active_box or boxes[0]
        try:
            idx = boxes.index(current)
        except ValueError:
            idx = 0
        self.active_box = boxes[(idx + delta) % len(boxes)]
        self.update_highlights()
        self.focus_widget()

    def focus_widget(self) -> None:
        box = self.active_box
        if box == "deck":
            cards = list(self._screen.query(DeckCard))
            if cards:
                cards[0].focus()
        elif box == "spread":
            if self._last_card_widget and self._last_card_widget.is_mounted:
                self._last_card_widget.focus()
            else:
                slots = list(self._screen.query(SpreadSlot))
                if slots:
                    slots[0].focus()
        elif box == "detail":
            self._screen.query_one("#card-preview").focus()
        elif box == "interp":
            self._screen.query_one("#interp-dialog").focus()

    def focus_neighbor(self, direction: str, phase, n_positions: int) -> None:
        from nekomata.screens.draw import Phase

        if phase == Phase.PICK:
            from nekomata.screens.draw_widgets import DECK_ROW_COUNT, NUM_DECK_CARDS
            widgets = list(self._screen.query(DeckCard))
            row_width = NUM_DECK_CARDS // DECK_ROW_COUNT
        elif phase == Phase.FLIP:
            widgets = [s for s in self._screen.query(SpreadSlot) if not s.is_revealed]
            row_width = self._spread_row_width(len(widgets))
        else:
            widgets = list(self._screen.query(SpreadSlot))
            row_width = self._spread_row_width(len(widgets))
        if not widgets:
            return
        try:
            idx = widgets.index(self._screen.focused)
        except ValueError:
            widgets[0].focus()
            return
        delta = self._direction_delta(direction, row_width)
        new_idx = idx + delta
        if 0 <= new_idx < len(widgets):
            widgets[new_idx].focus()

    def _save_last_card(self) -> None:
        if isinstance(self._screen.focused, (DeckCard, SpreadSlot)):
            self._last_card_widget = self._screen.focused

    @staticmethod
    def _direction_delta(direction: str, row_width: int) -> int:
        if direction == "left":
            return -1
        if direction == "right":
            return 1
        if direction == "up":
            return -row_width
        if direction == "down":
            return row_width
        return 0

    @staticmethod
    def _spread_row_width(count: int) -> int:
        if count >= 5:
            return 3
        return 1
