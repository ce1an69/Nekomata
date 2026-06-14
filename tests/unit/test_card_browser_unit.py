"""Unit tests for CardBrowserScreen navigation helper branches."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from textual.geometry import Size
from textual.widgets import Button

from nekomata.core.card.data import load_all_cards
from nekomata.tui.screens.card_browser import CardBrowserScreen, CardListItem


class _TestCardBrowserScreen(CardBrowserScreen):
    @property
    def app(self):
        return self._test_app

    @property
    def focused(self):
        return self._test_focused

    @property
    def size(self):
        return self._test_size


class _TestCardListItem(CardListItem):
    def __init__(self, card, screen, *, display=True, mounted=True) -> None:
        self._test_screen = screen
        self._test_app = screen.app
        self._test_mounted = mounted
        super().__init__(card)
        self.display = display
        self.focus = MagicMock()
        self.add_class = MagicMock()
        self.remove_class = MagicMock()

    @property
    def screen(self):
        return self._test_screen

    @property
    def app(self):
        return self._test_app

    @property
    def is_mounted(self):
        return self._test_mounted


def _screen():
    screen = _TestCardBrowserScreen.__new__(_TestCardBrowserScreen)
    screen._cards = load_all_cards()
    screen._reversed_preview = False
    screen._active_arcana = None
    screen._detail_preview_id = None
    screen._test_app = SimpleNamespace(
        render_mode="full",
        animation_enabled=False,
        config=SimpleNamespace(lang="en"),
        pop_screen=MagicMock(),
    )
    screen._test_size = Size(100, 40)
    screen._test_focused = None
    screen.set_timer = MagicMock()
    screen._detail_debounce = MagicMock()
    screen._widgets = {
        "#card-list": SimpleNamespace(styles=SimpleNamespace(opacity=1, animate=MagicMock())),
        "#card-count": SimpleNamespace(update=MagicMock()),
        "#browser-area": SimpleNamespace(set_class=MagicMock()),
        "#detail-image-slot": SimpleNamespace(
            remove_children=MagicMock(),
            mount=MagicMock(),
            styles=SimpleNamespace(opacity=1, animate=MagicMock()),
        ),
        "#detail-text-slot": SimpleNamespace(
            update=MagicMock(),
            styles=SimpleNamespace(opacity=1, animate=MagicMock()),
        ),
        "#card-detail": SimpleNamespace(scroll_home=MagicMock()),
    }
    screen._buttons = []
    screen._items = []
    screen.query_one = MagicMock(side_effect=lambda selector, *args: screen._query_one(selector))
    screen.query = MagicMock(side_effect=lambda selector: screen._query(selector))
    return screen


def _query_one(self, selector):
    if selector.startswith("#filter-"):
        for button in self._buttons:
            if button.id == selector[1:]:
                return button
    return self._widgets[selector]


def _query(self, selector):
    if selector == CardListItem:
        return self._items
    if selector == "#filter-bar Button":
        return self._buttons
    return []


_TestCardBrowserScreen._query_one = _query_one
_TestCardBrowserScreen._query = _query


def test_detail_debounce_renders_only_mounted_item():
    screen = _screen()
    item = _TestCardListItem(screen._cards[0], screen, mounted=False)

    screen._on_detail_debounce(item)
    item.remove_class.assert_not_called()

    item._test_mounted = True
    item._render_detail = MagicMock()
    screen._on_detail_debounce(item)
    item._render_detail.assert_called_once()


def test_apply_responsive_layout_sets_stacked_class():
    screen = _screen()
    screen._test_size = Size(60, 20)

    screen._apply_responsive_layout()

    screen._widgets["#browser-area"].set_class.assert_called_once()


def test_focus_first_visible_card_skips_hidden_items():
    screen = _screen()
    first = _TestCardListItem(screen._cards[0], screen, display=False)
    second = _TestCardListItem(screen._cards[1], screen, display=True)
    screen._items = [first, second]

    screen._focus_first_visible_card()

    first.focus.assert_not_called()
    second.focus.assert_called_once()


def test_apply_filter_animates_when_enabled_and_sets_timer():
    screen = _screen()
    screen._test_app.animation_enabled = True
    screen._items = [_TestCardListItem(card, screen) for card in screen._cards[:3]]

    screen._apply_filter(screen._cards[0].arcana)

    assert screen._active_arcana == screen._cards[0].arcana
    assert screen._widgets["#card-list"].styles.opacity == 0.2
    screen._widgets["#card-list"].styles.animate.assert_called_once()
    screen.set_timer.assert_called_once()


def test_cycle_filter_wraps_and_applies_index():
    screen = _screen()
    screen._apply_filter_by_index = MagicMock()
    screen._active_arcana = None

    screen._cycle_filter(-1)

    screen._apply_filter_by_index.assert_called_once()
    assert screen._apply_filter_by_index.call_args.args[0] >= 0


def test_focus_next_visible_handles_empty_missing_and_bounds():
    screen = _screen()
    screen._items = []
    screen._test_focused = None
    screen._focus_next_visible_card(1)

    first = _TestCardListItem(screen._cards[0], screen)
    second = _TestCardListItem(screen._cards[1], screen)
    screen._items = [first, second]
    hidden = _TestCardListItem(screen._cards[2], screen, display=False)
    screen._test_focused = hidden
    screen._focus_next_visible_card(1)
    first.focus.assert_called_once()

    screen._test_focused = second
    screen._focus_next_visible_card(1)
    second.focus.assert_not_called()


def test_key_left_right_delegate_filter_cycle():
    screen = _screen()
    screen._cycle_filter = MagicMock()

    screen.key_left()
    screen.key_right()

    screen._cycle_filter.assert_any_call(-1)
    screen._cycle_filter.assert_any_call(1)


def test_key_tab_handles_cards_buttons_and_other_focus():
    screen = _screen()
    item = _TestCardListItem(screen._cards[0], screen)
    first_button = Button("All", id="filter-all")
    second_button = Button("Major", id="filter-major")
    first_button.focus = MagicMock()
    second_button.focus = MagicMock()
    screen._items = [item]
    screen._buttons = [first_button, second_button]
    event = SimpleNamespace(stop=MagicMock())

    screen._test_focused = item
    screen.key_tab(event)
    first_button.focus.assert_called_once()

    screen._test_focused = first_button
    screen.key_tab(event)
    second_button.focus.assert_called_once()

    screen._test_focused = second_button
    screen.key_tab(event)
    item.focus.assert_called_once()

    other_button = Button("Other", id="other")
    screen._test_focused = other_button
    screen.key_tab(event)
    assert item.focus.call_count == 2


def test_apply_filter_by_index_ignores_invalid_index():
    screen = _screen()
    screen._update_filter_highlight = MagicMock()

    screen._apply_filter_by_index(-1)
    screen._apply_filter_by_index(999)

    screen._update_filter_highlight.assert_not_called()


def test_placeholder_detail_resets_slots():
    screen = _screen()
    screen._detail_preview_id = "card:false"

    screen._show_placeholder_detail()

    assert screen._detail_preview_id is None
    screen._widgets["#detail-image-slot"].remove_children.assert_called_once()
    screen._widgets["#detail-text-slot"].update.assert_called_once()


def test_card_list_item_click_enter_select_and_skip_duplicate_render():
    screen = _screen()
    item = _TestCardListItem(screen._cards[0], screen)
    screen._items = [item]
    screen._detail_preview_id = f"{screen._cards[0].id}:False"

    item.on_focus()
    item._show_detail()
    item.key_enter()

    item.add_class.assert_called()
    screen._detail_debounce.schedule.assert_called_once_with(item)
    screen._widgets["#detail-text-slot"].update.assert_not_called()


def test_card_list_item_render_detail_text_mode_and_animation():
    screen = _screen()
    screen._test_app.render_mode = "text"
    screen._test_app.animation_enabled = True
    item = _TestCardListItem(screen._cards[0], screen)

    item._render_detail()

    image_slot = screen._widgets["#detail-image-slot"]
    text_slot = screen._widgets["#detail-text-slot"]
    image_slot.remove_children.assert_called_once()
    text_slot.update.assert_called_once()
    image_slot.styles.animate.assert_called_once()
    text_slot.styles.animate.assert_called_once()
    screen._widgets["#card-detail"].scroll_home.assert_called_once_with(animate=False)
