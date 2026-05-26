"""Tests for desktop entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest


def test_find_free_port():
    from nekomata.desktop import find_free_port

    port = find_free_port()
    assert 1024 <= port <= 65535


def test_main_starts_server_and_webview():
    mock_webview = MagicMock()
    mock_uvicorn = MagicMock()
    mock_app = MagicMock()
    mock_server = MagicMock()
    mock_server.create_app.return_value = mock_app

    with (
        patch.dict(sys.modules, {
            "webview": mock_webview,
            "uvicorn": mock_uvicorn,
            "nekomata.web.server": mock_server,
        }),
        patch("nekomata.desktop.find_free_port", return_value=9999),
        patch("nekomata.desktop._wait_for_server"),
        patch("sys.argv", ["nekomata-desktop"]),
    ):
        from nekomata.desktop import main

        main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=9999,
            log_level="warning",
        )

        mock_webview.create_window.assert_called_once()
        call_args = mock_webview.create_window.call_args
        assert "http://127.0.0.1:9999" in call_args.args

        mock_webview.start.assert_called_once()


def test_server_runs_in_daemon_thread():
    mock_server = MagicMock()
    mock_server.create_app.return_value = MagicMock()

    with (
        patch.dict(sys.modules, {
            "webview": MagicMock(),
            "uvicorn": MagicMock(),
            "nekomata.web.server": mock_server,
        }),
        patch("nekomata.desktop.find_free_port", return_value=9999),
        patch("nekomata.desktop._wait_for_server"),
        patch("nekomata.desktop.threading.Thread") as mock_thread,
        patch("sys.argv", ["nekomata-desktop"]),
    ):
        from nekomata.desktop import main

        main()

        mock_thread.assert_called_once()
        _, kwargs = mock_thread.call_args
        assert kwargs["daemon"] is True
