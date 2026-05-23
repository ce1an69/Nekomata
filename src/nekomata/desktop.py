"""PyWebView desktop entry point — opens a native window for the Web UI."""

import argparse
import socket
import sys
import threading
import time

# Force edgechromium backend on Windows — avoids pythonnet/clr dependency
# which doesn't work in PyInstaller bundles.
_FORCE_GUI = "edgechromium" if sys.platform == "win32" else None


def find_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(host: str, port: int, timeout: float = 10) -> None:
    """Block until the server accepts connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Server did not start within {timeout}s")


def main() -> None:
    parser = argparse.ArgumentParser(prog="nekomata-desktop")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with logs and devtools")
    args = parser.parse_args()

    debug = args.debug
    if debug:
        print("[debug] starting Nekomata desktop...")

    import webview

    from nekomata.web.server import create_app
    import uvicorn

    port = find_free_port()
    if debug:
        print(f"[debug] using port {port}")

    app = create_app()
    if debug:
        print("[debug] FastAPI app created")

    log_level = "info" if debug else "warning"

    server_thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": port, "log_level": log_level},
        daemon=True,
    )
    server_thread.start()
    _wait_for_server("127.0.0.1", port)

    url = f"http://127.0.0.1:{port}"
    if debug:
        # Test that the server actually responds
        import urllib.request
        try:
            resp = urllib.request.urlopen(url, timeout=2)
            print(f"[debug] GET {url} → {resp.status}")
        except Exception as e:
            print(f"[debug] GET {url} → ERROR: {e}")

    if debug:
        print(f"[debug] opening webview window → {url}")

    webview.create_window("Nekomata 猫又", url, width=1200, height=800, min_size=(800, 600))
    webview.start(debug=debug, gui=_FORCE_GUI)


if __name__ == "__main__":
    main()
