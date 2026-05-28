"""PyWebView desktop entry point — opens a native window for the Web UI."""

import argparse
import queue
import socket
import threading
import time
import urllib.request

import webview

from nekomata.web.server import create_app


def find_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(
    host: str,
    port: int,
    timeout: float = 10,
    errors: "queue.SimpleQueue[BaseException] | None" = None,
) -> None:
    """Block until the server accepts connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if errors is not None:
            try:
                raise errors.get_nowait()
            except queue.Empty:
                pass
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Server did not start within {timeout}s")


def _run_server(
    app,
    host: str,
    port: int,
    log_level: str,
    errors: "queue.SimpleQueue[BaseException]",
) -> None:
    """Run uvicorn and pass background-thread startup failures to the caller."""
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level=log_level, log_config=None)


def main() -> None:
    parser = argparse.ArgumentParser(prog="nekomata-desktop")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with logs and devtools"
    )
    args = parser.parse_args()

    debug = args.debug
    if debug:
        print("[debug] starting Nekomata desktop...")

    port = find_free_port()
    if debug:
        print(f"[debug] using port {port}")

    app = create_app()
    if debug:
        print("[debug] FastAPI app created")

    log_level = "info" if debug else "warning"
    server_errors: queue.SimpleQueue[BaseException] = queue.SimpleQueue()

    server_thread = threading.Thread(
        target=_run_server,
        args=(app, "127.0.0.1", port, log_level, server_errors),
        daemon=True,
    )
    server_thread.start()
    _wait_for_server("127.0.0.1", port, errors=server_errors)

    url = f"http://127.0.0.1:{port}"
    if debug:
        try:
            resp = urllib.request.urlopen(url, timeout=2)
            print(f"[debug] GET {url} → {resp.status}")
        except Exception as e:
            print(f"[debug] GET {url} → ERROR: {e}")

    if debug:
        print(f"[debug] opening webview window → {url}")
    webview.create_window("Nekomata", url, width=1200, height=800, min_size=(800, 600))
    webview.start(debug=debug)


if __name__ == "__main__":
    main()
