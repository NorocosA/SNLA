"""SNLA Standalone Launcher — double-click to run.
 
Starts the Streamlit server and opens the default browser.
No command-line required.
"""
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser


def _wait_for_port(port: int, timeout: int = 60) -> bool:
    """Block until localhost:port is accepting connections, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection(("localhost", port), timeout=1)
            s.close()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.5)
    return False


def main():
    # When bundled by PyInstaller, sys._MEIPASS contains extracted files
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base, "snla", "ui", "streamlit_app.py")

    if not os.path.exists(app_path):
        print(f"ERROR: Streamlit app not found at {app_path}")
        input("Press Enter to exit...")
        sys.exit(1)

    print("=" * 50)
    print("  SPSS Natural Language Assistant")
    print("=" * 50)
    print()

    port = 8501

    # Use streamlit CLI module directly (works both dev and PyInstaller)
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", app_path,
         "--server.headless", "true",
         "--server.port", str(port),
         "--browser.serverAddress", "localhost"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Port-check thread (decoupled from stdout consumption)
    def _wait_and_open():
        print(f"  Waiting for server on port {port} ...")
        if _wait_for_port(port):
            print(f"  Server ready. Opening http://localhost:{port} ...")
            webbrowser.open(f"http://localhost:{port}")
        else:
            print(f"  WARNING: Server did not respond within 60 seconds.")
            print(f"  Please open http://localhost:{port} manually in your browser.")

    threading.Thread(target=_wait_and_open, daemon=True).start()

    print(f"  Press Ctrl+C or close this window to stop.")
    print("=" * 50)

    # Main thread: stream Streamlit's stdout to console
    try:
        for line in proc.stdout:
            print(line, end="")
    except KeyboardInterrupt:
        print("\nShutting down...")
        proc.terminate()
    finally:
        proc.wait()

    print("Server stopped.")


if __name__ == "__main__":
    main()
