"""Tests for desktop entry point."""

import queue
import sys
from unittest.mock import MagicMock, patch

import pytest

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
        patch.dict(sys.modules, {"webview": mock_webview}),
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
        patch.dict(sys.modules, {"webview": mock_webview}),
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


def test_main_debug_logs_probe_error():
    mock_webview = MagicMock()
    mock_uvicorn = MagicMock()
    mock_app = MagicMock()

    with (
        patch.dict(sys.modules, {"webview": mock_webview}),
        patch.object(_desktop, "create_app", return_value=mock_app),
        patch.dict(sys.modules, {"uvicorn": mock_uvicorn}),
        patch("nekomata.desktop.find_free_port", return_value=9999),
        patch("nekomata.desktop._wait_for_server"),
        patch("nekomata.desktop.urllib.request.urlopen", side_effect=OSError("offline")),
        patch("builtins.print") as mock_print,
    ):
        _desktop.main(debug=True)

    calls = [str(c) for c in mock_print.call_args_list]
    assert any("ERROR" in c and "offline" in c for c in calls)


def test_server_runs_in_daemon_thread():
    mock_create_app = MagicMock(return_value=MagicMock())

    with (
        patch.dict(sys.modules, {"webview": MagicMock()}),
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


def test_wait_for_server_returns_when_socket_connects():
    connection = MagicMock()
    errors: queue.SimpleQueue[BaseException] = queue.SimpleQueue()

    with patch("nekomata.desktop.socket.create_connection", return_value=connection) as create_connection:
        _desktop._wait_for_server("127.0.0.1", 9999, timeout=0.1, errors=errors)

    create_connection.assert_called_once_with(("127.0.0.1", 9999), timeout=0.5)
    connection.__enter__.assert_called_once()
    connection.__exit__.assert_called_once()


def test_wait_for_server_retries_until_connection_succeeds():
    connection = MagicMock()

    with (
        patch("nekomata.desktop.socket.create_connection", side_effect=[OSError("nope"), connection]),
        patch("nekomata.desktop.time.sleep") as sleep,
    ):
        _desktop._wait_for_server("127.0.0.1", 9999, timeout=1)

    sleep.assert_called_once_with(0.1)


def test_wait_for_server_timeout_defaults_to_ten_seconds():
    with (
        patch("nekomata.desktop.time.monotonic", side_effect=[100, 111]),
        pytest.raises(RuntimeError, match="within 10s"),
    ):
        _desktop._wait_for_server("127.0.0.1", 9)


def test_run_server_delegates_to_uvicorn():
    mock_uvicorn = MagicMock()
    app = MagicMock()

    with patch.dict(sys.modules, {"uvicorn": mock_uvicorn}):
        _desktop._run_server(app, "127.0.0.1", 9999, "info", queue.SimpleQueue())

    mock_uvicorn.run.assert_called_once_with(app, host="127.0.0.1", port=9999, log_level="info", log_config=None)
