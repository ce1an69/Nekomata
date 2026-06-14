"""Unit tests for nekomata.app entry-point dispatch."""

from unittest.mock import MagicMock

from nekomata import app as entrypoint


def test_apply_tui_env_fixes_disables_kitty_key_on_macos(monkeypatch):
    monkeypatch.setattr(entrypoint.sys, "platform", "darwin")
    monkeypatch.setenv("TERM", "xterm-kitty")
    monkeypatch.delenv("TEXTUAL_DISABLE_KITTY_KEY", raising=False)

    entrypoint._apply_tui_env_fixes()

    assert entrypoint.os.environ["TEXTUAL_DISABLE_KITTY_KEY"] == "1"


def test_apply_tui_env_fixes_preserves_existing_value(monkeypatch):
    monkeypatch.setattr(entrypoint.sys, "platform", "darwin")
    monkeypatch.setenv("TERM", "xterm-kitty")
    monkeypatch.setenv("TEXTUAL_DISABLE_KITTY_KEY", "custom")

    entrypoint._apply_tui_env_fixes()

    assert entrypoint.os.environ["TEXTUAL_DISABLE_KITTY_KEY"] == "custom"


def test_main_dispatches_cli(monkeypatch):
    run_cli = MagicMock()
    monkeypatch.setattr(entrypoint.sys, "argv", ["nekomata-tarot", "--cli", "--question", "q"])
    monkeypatch.setattr("nekomata.cli.run_cli", run_cli)

    entrypoint.main()

    run_cli.assert_called_once()
    assert run_cli.call_args.args[0].question == "q"


def test_main_dispatches_desktop(monkeypatch):
    desktop_main = MagicMock()
    monkeypatch.setattr(entrypoint.sys, "argv", ["nekomata-tarot", "--desktop", "--debug"])
    monkeypatch.setattr("nekomata.desktop.main", desktop_main)

    entrypoint.main()

    desktop_main.assert_called_once_with(debug=True)


def test_main_runs_tui_by_default(monkeypatch):
    app_instance = MagicMock()
    app_class = MagicMock(return_value=app_instance)
    monkeypatch.setattr(entrypoint.sys, "argv", ["nekomata-tarot"])
    monkeypatch.setattr("nekomata.tui.app.NekomataApp", app_class)

    entrypoint.main()

    app_class.assert_called_once()
    app_instance.run.assert_called_once()
