"""Unit tests for draw screen box focus navigation."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from textual.geometry import Size

from nekomata.tui.screens.box_manager import BoxManager
from nekomata.tui.screens.draw_phase import Phase
from nekomata.tui.screens.draw_widgets import DeckCard, SpreadSlot


class _DeckCard(DeckCard):
    def __init__(self, index: int) -> None:
        super().__init__(index)
        self.focus = MagicMock()


class _SpreadSlot(SpreadSlot):
    def __init__(self, index: int, *, revealed: bool = False, mounted: bool = True) -> None:
        super().__init__(index, f"pos-{index}")
        self.is_revealed = revealed
        self._mounted = mounted
        self.focus = MagicMock()

    @property
    def is_mounted(self) -> bool:
        return self._mounted


class _Screen:
    def __init__(self, deck=None, slots=None):
        self.deck = deck or []
        self.slots = slots or []
        self.focused = None
        self.size = Size(120, 40)
        self.app = SimpleNamespace(render_mode="full")
        self.elements = {
            "#deck-section": MagicMock(),
            "#spread-area": MagicMock(),
            "#card-preview": MagicMock(),
            "#interp-dialog": MagicMock(),
        }

    def query(self, widget_type):
        if issubclass(widget_type, DeckCard):
            return self.deck
        if issubclass(widget_type, SpreadSlot):
            return self.slots
        return []

    def query_one(self, selector):
        return self.elements[selector]


def test_update_highlights_marks_only_active_box():
    screen = _Screen()
    manager = BoxManager(screen, lambda: ["deck", "spread"])
    manager.active_box = "spread"

    manager.update_highlights()

    screen.elements["#deck-section"].set_class.assert_called_once_with(False, "box-active")
    screen.elements["#spread-area"].set_class.assert_called_once_with(True, "box-active")
    screen.elements["#card-preview"].set_class.assert_called_once_with(False, "box-active")
    screen.elements["#interp-dialog"].set_class.assert_called_once_with(False, "box-active")


def test_focus_change_updates_active_box_for_cards_and_slots():
    screen = _Screen()
    manager = BoxManager(screen, lambda: ["deck", "spread"])
    deck_card = _DeckCard(0)
    slot = _SpreadSlot(0)

    assert manager.on_focus_change(deck_card) == "deck"
    assert manager.active_box == "deck"

    assert manager.on_focus_change(slot) == "spread"
    assert manager.active_box == "spread"

    assert manager.on_focus_change(object()) is None


def test_cycle_wraps_boxes_and_focuses_target_widget():
    deck = [_DeckCard(0)]
    slots = [_SpreadSlot(0)]
    screen = _Screen(deck=deck, slots=slots)
    screen.focused = deck[0]
    manager = BoxManager(screen, lambda: ["deck", "spread", "detail", "interp"])
    manager.active_box = "deck"

    manager.cycle(1)

    assert manager.active_box == "spread"
    slots[0].focus.assert_called_once()

    manager.cycle(-1)

    assert manager.active_box == "deck"
    deck[0].focus.assert_called_once()


def test_cycle_ignores_single_available_box():
    screen = _Screen(deck=[_DeckCard(0)])
    manager = BoxManager(screen, lambda: ["deck"])
    manager.active_box = "deck"

    manager.cycle(1)

    assert manager.active_box == "deck"
    screen.deck[0].focus.assert_not_called()


def test_focus_widget_uses_last_mounted_spread_card():
    first = _SpreadSlot(0)
    last = _SpreadSlot(1)
    screen = _Screen(slots=[first, last])
    manager = BoxManager(screen, lambda: ["spread"])
    manager.active_box = "spread"
    manager._last_card_widget = last

    manager.focus_widget()

    last.focus.assert_called_once()
    first.focus.assert_not_called()


def test_focus_widget_falls_back_when_last_card_unmounted():
    first = _SpreadSlot(0)
    last = _SpreadSlot(1, mounted=False)
    screen = _Screen(slots=[first, last])
    manager = BoxManager(screen, lambda: ["spread"])
    manager.active_box = "spread"
    manager._last_card_widget = last

    manager.focus_widget()

    first.focus.assert_called_once()
    last.focus.assert_not_called()


def test_focus_widget_focuses_detail_and_interp_boxes():
    screen = _Screen()
    manager = BoxManager(screen, lambda: ["detail", "interp"])

    manager.active_box = "detail"
    manager.focus_widget()
    screen.elements["#card-preview"].focus.assert_called_once()

    manager.active_box = "interp"
    manager.focus_widget()
    screen.elements["#interp-dialog"].focus.assert_called_once()


def test_focus_neighbor_pick_moves_between_deck_cards():
    deck = [_DeckCard(i) for i in range(3)]
    screen = _Screen(deck=deck)
    screen.focused = deck[0]
    manager = BoxManager(screen, lambda: ["deck"])

    manager.focus_neighbor("right", Phase.PICK)

    deck[1].focus.assert_called_once()


def test_focus_neighbor_flip_skips_revealed_slots():
    slots = [_SpreadSlot(0), _SpreadSlot(1, revealed=True), _SpreadSlot(2)]
    screen = _Screen(slots=slots)
    screen.focused = slots[0]
    manager = BoxManager(screen, lambda: ["spread"])

    manager.focus_neighbor("right", Phase.FLIP)

    slots[2].focus.assert_called_once()
    slots[1].focus.assert_not_called()


def test_focus_neighbor_focuses_first_when_current_not_in_widgets():
    slots = [_SpreadSlot(0), _SpreadSlot(1)]
    screen = _Screen(slots=slots)
    screen.focused = object()
    manager = BoxManager(screen, lambda: ["spread"])

    manager.focus_neighbor("right", Phase.DONE)

    slots[0].focus.assert_called_once()


def test_focus_neighbor_ignores_out_of_bounds_move():
    slots = [_SpreadSlot(0), _SpreadSlot(1)]
    screen = _Screen(slots=slots)
    screen.focused = slots[0]
    manager = BoxManager(screen, lambda: ["spread"])

    manager.focus_neighbor("left", Phase.DONE)

    slots[0].focus.assert_not_called()
    slots[1].focus.assert_not_called()


def test_direction_delta_and_spread_row_width_helpers():
    assert BoxManager._direction_delta("left", 3) == -1
    assert BoxManager._direction_delta("right", 3) == 1
    assert BoxManager._direction_delta("up", 3) == -3
    assert BoxManager._direction_delta("down", 3) == 3
    assert BoxManager._direction_delta("unknown", 3) == 0
    assert BoxManager._spread_row_width(4) == 1
    assert BoxManager._spread_row_width(5) == 3
