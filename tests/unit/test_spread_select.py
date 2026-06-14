"""Unit tests for spread selection helper branches."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from nekomata.tui.screens.spread_select import SpreadOption, SpreadSelectScreen


class _TestSpreadSelectScreen(SpreadSelectScreen):
    @property
    def app(self):
        return self._test_app

    @property
    def focused(self):
        return self._test_focused


def test_spread_option_click_and_enter_post_selected_message():
    option = SpreadOption("Single", "spread-single")
    option.post_message = MagicMock()

    option.on_click()
    option.key_enter()

    assert option.post_message.call_count == 2
    assert option.post_message.call_args.args[0].option_id == "spread-single"


def _screen(options=None, focused=None):
    screen = _TestSpreadSelectScreen()
    screen._test_app = SimpleNamespace(pop_screen=MagicMock(), screen=SimpleNamespace())
    screen._test_focused = focused
    widgets = {
        "#preview-title": SimpleNamespace(update=MagicMock()),
        "#preview-desc": SimpleNamespace(update=MagicMock()),
        "#preview-positions": SimpleNamespace(update=MagicMock()),
        "#spread-shell": object(),
    }
    screen.query_one = MagicMock(side_effect=lambda selector, *args: widgets[selector])
    screen.query = MagicMock(return_value=options or [])
    screen.dismiss = MagicMock()
    return screen, widgets


def test_update_preview_handles_back_option():
    screen, widgets = _screen()

    screen._update_preview("back")

    widgets["#preview-title"].update.assert_called_once_with("Back")
    widgets["#preview-desc"].update.assert_called_once()
    widgets["#preview-positions"].update.assert_called_once_with("")


def test_option_selected_delegates_activation():
    screen, _widgets = _screen()
    screen._activate_option = MagicMock()
    event = SimpleNamespace(option_id="spread-single")

    screen.on_spread_option_selected(event)

    screen._activate_option.assert_called_once_with("spread-single")


def test_select_by_index_ignores_out_of_range():
    screen, _widgets = _screen()

    screen._select_by_index(-1)
    screen._select_by_index(99)

    screen.dismiss.assert_not_called()


def test_on_key_ignores_non_digit_characters():
    screen, _widgets = _screen()
    event = SimpleNamespace(character="x", stop=MagicMock())

    screen.on_key(event)

    event.stop.assert_not_called()
    screen.dismiss.assert_not_called()


def test_next_option_handles_empty_missing_and_bounds():
    screen, _widgets = _screen(options=[])
    assert screen._next_option(1) is None

    first = SpreadOption("First", "spread-single")
    second = SpreadOption("Second", "spread-past_present_future")
    first.focus = MagicMock()
    second.focus = MagicMock()
    screen.query = MagicMock(return_value=[first, second])
    screen._test_focused = object()

    assert screen._next_option(1) is first
    first.focus.assert_called_once()

    screen._test_focused = second
    assert screen._next_option(1) is None


def test_move_option_updates_preview_for_target():
    first = SpreadOption("First", "spread-single")
    second = SpreadOption("Second", "spread-past_present_future")
    first.focus = MagicMock()
    second.focus = MagicMock()
    screen, _widgets = _screen(options=[first, second], focused=first)
    screen._update_preview = MagicMock()

    screen._move_option(1)

    second.focus.assert_called_once()
    screen._update_preview.assert_called_once_with("spread-past_present_future")


def test_activate_option_back_or_unknown():
    screen, _widgets = _screen()
    screen.action_go_back = MagicMock()

    screen._activate_option("back")
    screen._activate_option("unknown")

    screen.action_go_back.assert_called_once()
    screen.dismiss.assert_not_called()
