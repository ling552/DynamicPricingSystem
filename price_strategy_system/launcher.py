from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_free_port(start: int = DEFAULT_PORT) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError("No available local port found.")


def initialize_database() -> None:
    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=0)


def open_browser_later(url: str) -> None:
    def _open() -> None:
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    app_runtime_dir = runtime_dir()
    data_dir = app_runtime_dir / "data"
    logs_dir = app_runtime_dir / "logs"
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "price_system.settings")
    os.environ.setdefault("DPS_RUNTIME_DIR", str(app_runtime_dir))
    os.environ.setdefault("DPS_DATA_DIR", str(data_dir))

    import django
    from django.core.management import call_command

    django.setup()
    initialize_database()

    port = find_free_port()
    url = f"http://{HOST}:{port}/"
    open_browser_later(url)

    print("Dynamic Pricing System")
    print(f"Data directory: {data_dir}")
    print(f"Open: {url}")
    print("Close this window to stop the application.")
    call_command("runserver", f"{HOST}:{port}", use_reloader=False)


if __name__ == "__main__":
    main()
