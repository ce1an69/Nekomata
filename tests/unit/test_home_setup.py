"""Unit tests for HomeScreen and SetupScreen helper branches."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from textual.widgets import Select

from nekomata.tui.screens.home import HomeScreen
from nekomata.tui.screens.setup import SetupButton, SetupScreen


class _TestHomeScreen(HomeScreen):
    @property
    def app(self):
        return self._test_app


class _TestSetupScreen(SetupScreen):
    @property
    def app(self):
        return self._test_app


def test_home_unmount_stops_suggestion_hide_timer():
    screen = HomeScreen()
    timer = MagicMock()
    screen._suggestions_hide_timer = timer

    screen.on_unmount()

    timer.stop.assert_called_once()
    assert screen._suggestions_hide_timer is None


def test_home_input_changed_ignores_other_inputs():
    screen = HomeScreen()
    screen._refresh_command_suggestions = MagicMock()
    event = SimpleNamespace(input=SimpleNamespace(id="other"), value="/")

    screen.on_input_changed(event)

    screen._refresh_command_suggestions.assert_not_called()


def test_home_key_tab_without_match_does_not_stop_event():
    screen = HomeScreen()
    prompt = SimpleNamespace(value="plain", cursor_position=0)
    screen.query_one = MagicMock(return_value=prompt)
    event = SimpleNamespace(key="tab", stop=MagicMock())

    screen.on_key(event)

    event.stop.assert_not_called()


def test_home_input_submitted_ignores_other_or_empty_input():
    screen = HomeScreen()
    screen.query_one = MagicMock()

    event = SimpleNamespace(input=SimpleNamespace(id="other"), value="Question")
    screen.on_input_submitted(event)
    screen.query_one.assert_not_called()

    event = SimpleNamespace(input=SimpleNamespace(id="prompt-input"), value="   ")
    screen.on_input_submitted(event)
    screen.query_one.assert_not_called()


def test_home_refresh_suggestions_resets_visible_panel_without_animation():
    screen = _TestHomeScreen()
    suggestions = SimpleNamespace(display=True, update=MagicMock(), styles=SimpleNamespace(opacity=0, offset=(1, 1)))
    screen.query_one = MagicMock(return_value=suggestions)
    screen._test_app = SimpleNamespace(animation_enabled=False)
    screen._suggestions_hide_timer = MagicMock()

    screen._refresh_command_suggestions("plain")

    assert screen._suggestion_matches == []
    assert screen._suggestion_idx == -1
    assert suggestions.display is False
    suggestions.update.assert_called_with("")


def test_home_render_suggestions_hides_empty_matches():
    screen = HomeScreen()
    suggestions = SimpleNamespace(display=True, update=MagicMock())
    screen.query_one = MagicMock(return_value=suggestions)

    screen._render_suggestions()

    assert suggestions.display is False
    suggestions.update.assert_called_once_with("")


def test_home_finish_hide_suggestions_resets_styles():
    screen = HomeScreen()
    suggestions = SimpleNamespace(display=True, update=MagicMock(), styles=SimpleNamespace(opacity=0, offset=(1, 1)))
    screen.query_one = MagicMock(return_value=suggestions)
    screen._suggestions_hide_timer = MagicMock()

    screen._finish_hide_suggestions()

    assert suggestions.display is False
    suggestions.update.assert_called_once_with("")
    assert suggestions.styles.opacity == 1.0
    assert suggestions.styles.offset == (0, 0)
    assert screen._suggestions_hide_timer is None


def test_home_matching_command_requires_slash_prefix():
    screen = HomeScreen()

    assert screen._matching_command("browse") is None
    assert screen._matching_command("/br") == "/browse"


def _setup_screen():
    screen = _TestSetupScreen()
    widgets = {
        "#api-url-input": SimpleNamespace(id="api-url-input", focus=MagicMock(), value="https://api.test/v1"),
        "#api-key-input": SimpleNamespace(id="api-key-input", focus=MagicMock(), value="sk-test"),
        "#model-input": SimpleNamespace(id="model-input", focus=MagicMock(), value="model"),
        "#lang-select": SimpleNamespace(id="lang-select", focus=MagicMock(), value="en"),
        "#save-btn": SimpleNamespace(id="save-btn", focus=MagicMock()),
        "#setup-error": SimpleNamespace(display=False, update=MagicMock()),
        "#setup-stack": object(),
    }
    screen.query_one = MagicMock(side_effect=lambda selector, *args: widgets[selector])
    screen._test_app = SimpleNamespace(focused=widgets["#api-url-input"], config=None)
    screen.dismiss = MagicMock()
    return screen, widgets


def test_setup_on_mount_focuses_url_and_animates_stack():
    screen, widgets = _setup_screen()

    with patch("nekomata.tui.screens.setup.animate_entrance") as animate:
        screen.on_mount()

    widgets["#api-url-input"].focus.assert_called_once()
    animate.assert_called_once_with(widgets["#setup-stack"], duration=0.35)


def test_setup_navigate_field_ignores_unknown_focus_and_bounds():
    screen, widgets = _setup_screen()
    screen.app.focused = None
    screen._navigate_field(1)
    widgets["#api-key-input"].focus.assert_not_called()

    screen.app.focused = SimpleNamespace(id="unknown")
    screen._navigate_field(1)
    widgets["#api-key-input"].focus.assert_not_called()

    screen.app.focused = widgets["#api-url-input"]
    screen._navigate_field(-1)
    widgets["#api-key-input"].focus.assert_not_called()


def test_setup_key_up_down_delegate_navigation():
    screen, _widgets = _setup_screen()
    screen._navigate_field = MagicMock()

    screen.key_down()
    screen.key_up()

    screen._navigate_field.assert_any_call(1)
    screen._navigate_field.assert_any_call(-1)


def test_setup_input_submitted_focuses_next_field():
    screen, widgets = _setup_screen()

    for current_id, next_id in [
        ("api-url-input", "#api-key-input"),
        ("api-key-input", "#model-input"),
        ("model-input", "#lang-select"),
    ]:
        event = SimpleNamespace(input=SimpleNamespace(id=current_id))
        screen.on_input_submitted(event)
        widgets[next_id].focus.assert_called()


def test_setup_button_pressed_stops_event_and_saves():
    screen, _widgets = _setup_screen()
    screen._save = MagicMock()
    event = SimpleNamespace(stop=MagicMock())

    screen.on_setup_button_pressed(event)

    event.stop.assert_called_once()
    screen._save.assert_called_once()


def test_setup_save_blank_language_defaults_to_en():
    screen, widgets = _setup_screen()
    widgets["#lang-select"].value = Select.BLANK

    with (
        patch("nekomata.tui.screens.setup.AppConfig.save", return_value=SimpleNamespace(lang="en")) as save,
        patch("nekomata.tui.screens.setup.set_lang") as set_lang,
    ):
        screen._save()

    save.assert_called_once_with("https://api.test/v1", "sk-test", "model", lang="en")
    set_lang.assert_called_once_with("en")
    screen.dismiss.assert_called_once_with(None)


def test_setup_button_key_enter_posts_pressed_message():
    button = SetupButton("Save")
    button.post_message = MagicMock()

    button.key_enter()

    assert button.post_message.call_args.args[0].__class__.__name__ == "Pressed"
