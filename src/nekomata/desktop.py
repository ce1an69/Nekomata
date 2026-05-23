"""PyWebView desktop entry point — opens a native window for the Web UI."""

import socket
import threading


def find_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    import webview

    from nekomata.web.server import create_app
    import uvicorn

    port = find_free_port()
    app = create_app()
    url = f"http://127.0.0.1:{port}"

    server_thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": port, "log_level": "warning"},
        daemon=True,
    )
    server_thread.start()

    webview.create_window("Nekomata 猫又", url, width=1200, height=800, min_size=(800, 600))
    webview.start()


if __name__ == "__main__":
    main()
