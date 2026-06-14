"""Unit tests for the Textual application shell."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from nekomata.tui.app import NekomataApp
from nekomata.tui.screens.home import HomeScreen


class _TestApp(NekomataApp):
    @property
    def screen(self):
        return self._test_screen


def _make_app_without_init() -> NekomataApp:
    app = _TestApp.__new__(_TestApp)
    app.theme_name = "catppuccin"
    app.render_mode = "compact"
    app.push_screen = MagicMock()
    app._test_screen = None
    return app


def test_theme_variable_defaults_include_catppuccin_colors():
    app = _make_app_without_init()

    defaults = NekomataApp.get_theme_variable_defaults(app)

    assert defaults["crust"].startswith("#")
    assert defaults["mauve"].startswith("#")
    assert defaults["text"].startswith("#")


def test_on_mount_pushes_home_only_when_config_exists():
    app = _make_app_without_init()

    with (
        patch("nekomata.tui.app.get_render_mode", return_value="full"),
        patch("nekomata.tui.app.set_default_theme") as set_theme,
        patch("nekomata.tui.app.AppConfig.config_exists", return_value=True),
    ):
        NekomataApp.on_mount(app)

    assert app.render_mode == "full"
    set_theme.assert_called_once_with("catppuccin")
    assert isinstance(app.push_screen.call_args_list[0].args[0], HomeScreen)
    assert app.push_screen.call_count == 1


def test_on_mount_pushes_setup_when_config_missing():
    app = _make_app_without_init()

    with (
        patch("nekomata.tui.app.get_render_mode", return_value="compact"),
        patch("nekomata.tui.app.set_default_theme"),
        patch("nekomata.tui.app.AppConfig.config_exists", return_value=False),
    ):
        NekomataApp.on_mount(app)

    assert isinstance(app.push_screen.call_args_list[0].args[0], HomeScreen)
    setup_call = app.push_screen.call_args_list[1]
    assert setup_call.args[0].__class__.__name__ == "SetupScreen"
    assert setup_call.kwargs["callback"] == app._on_setup_done


def test_setup_done_reopens_setup_when_config_still_missing():
    app = _make_app_without_init()

    with patch("nekomata.tui.app.AppConfig.config_exists", return_value=False):
        NekomataApp._on_setup_done(app, None)

    setup_call = app.push_screen.call_args
    assert setup_call.args[0].__class__.__name__ == "SetupScreen"
    assert setup_call.kwargs["callback"] == app._on_setup_done


def test_setup_done_resumes_home_screen_when_config_exists():
    app = _make_app_without_init()
    home = HomeScreen()
    home.resume = MagicMock()
    app._test_screen = home

    with patch("nekomata.tui.app.AppConfig.config_exists", return_value=True):
        NekomataApp._on_setup_done(app, None)

    home.resume.assert_called_once()
    app.push_screen.assert_not_called()


def test_setup_done_does_not_resume_non_home_screen():
    app = _make_app_without_init()
    app._test_screen = SimpleNamespace()

    with patch("nekomata.tui.app.AppConfig.config_exists", return_value=True):
        NekomataApp._on_setup_done(app, None)

    app.push_screen.assert_not_called()


def test_resize_refreshes_render_mode():
    app = _make_app_without_init()

    with patch("nekomata.tui.app.get_render_mode", return_value="text"):
        NekomataApp.on_resize(app, MagicMock())

    assert app.render_mode == "text"
