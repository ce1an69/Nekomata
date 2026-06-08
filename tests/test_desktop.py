"""Tests for desktop entry point."""

import queue
import sys
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("webview")

import nekomata.desktop as _desktop


def test_find_free_port():
    port = _desktop.find_free_port()
    assert 1024 <= port <= 65535


def test_main_starts_server_and_webview():
    mock_webview = MagicMock()
    mock_uvicorn = MagicMock()
    mock_app = MagicMock()
    mock_create_app = MagicMock(return_value=mock_app)

    with (
        patch.object(_desktop, "webview", mock_webview),
        patch.object(_desktop, "create_app", mock_create_app),
        patch.dict(sys.modules, {"uvicorn": mock_uvicorn}),
        patch("nekomata.desktop.find_free_port", return_value=9999),
        patch("nekomata.desktop._wait_for_server"),
    ):
        _desktop.main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=9999,
            log_level="warning",
            log_config=None,
        )

        mock_webview.create_window.assert_called_once()
        call_args = mock_webview.create_window.call_args
        assert "http://127.0.0.1:9999" in call_args.args

        mock_webview.start.assert_called_once_with(debug=False)


def test_main_debug_mode():
    mock_webview = MagicMock()
    mock_uvicorn = MagicMock()
    mock_app = MagicMock()
    mock_create_app = MagicMock(return_value=mock_app)

    with (
        patch.object(_desktop, "webview", mock_webview),
        patch.object(_desktop, "create_app", mock_create_app),
        patch.dict(sys.modules, {"uvicorn": mock_uvicorn}),
        patch("nekomata.desktop.find_free_port", return_value=9999),
        patch("nekomata.desktop._wait_for_server"),
        patch("nekomata.desktop.urllib.request.urlopen"),
    ):
        _desktop.main(debug=True)

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=9999,
            log_level="info",
            log_config=None,
        )

        mock_webview.start.assert_called_once_with(debug=True)


def test_server_runs_in_daemon_thread():
    mock_create_app = MagicMock(return_value=MagicMock())

    with (
        patch.object(_desktop, "webview", MagicMock()),
        patch.object(_desktop, "create_app", mock_create_app),
        patch.dict(sys.modules, {"uvicorn": MagicMock()}),
        patch("nekomata.desktop.find_free_port", return_value=9999),
        patch("nekomata.desktop._wait_for_server"),
        patch("nekomata.desktop.threading.Thread") as mock_thread,
    ):
        _desktop.main()

        mock_thread.assert_called_once()
        _, kwargs = mock_thread.call_args
        assert kwargs["daemon"] is True


def test_wait_for_server_raises_thread_error():
    errors: queue.SimpleQueue[BaseException] = queue.SimpleQueue()
    errors.put(RuntimeError("server failed"))

    with pytest.raises(RuntimeError, match="server failed"):
        _desktop._wait_for_server("127.0.0.1", 9, timeout=0.1, errors=errors)


def test_wait_for_server_timeout_defaults_to_ten_seconds():
    with (
        patch("nekomata.desktop.time.monotonic", side_effect=[100, 111]),
        pytest.raises(RuntimeError, match="within 10s"),
    ):
        _desktop._wait_for_server("127.0.0.1", 9)
