"""
CV Watcher — runs silently in the background via pythonw.exe.
When Tehman CV.docx is saved, opens a visible terminal running deploy.py.
"""

import sys
import time
import subprocess
import logging
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "watchdog"], check=True)
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

BASE_DIR      = Path(__file__).parent.resolve()
DOCX          = BASE_DIR / "Tehman CV.docx"
DEPLOY_SCRIPT = BASE_DIR / "deploy.py"
LOG_FILE      = BASE_DIR / "watcher.log"

# pythonw.exe never opens a window, so find python.exe explicitly for the popup
_pythonw = Path(sys.executable)
PYTHON_EXE = str(_pythonw.parent / "python.exe") if (_pythonw.parent / "python.exe").exists() else "python"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def open_deploy_terminal():
    """Open a new visible terminal window running deploy.py."""
    logging.info("Change detected — opening deploy terminal.")
    # Use cmd /c start — the only reliable way to get a visible window
    # regardless of whether the parent process is a service or scheduled task
    subprocess.Popen(
        ['cmd', '/c', 'start', 'CV Auto-Deploy', PYTHON_EXE, str(DEPLOY_SCRIPT)],
        cwd=str(BASE_DIR),
    )


class CVHandler(FileSystemEventHandler):
    def __init__(self):
        self._last = 0

    def _handle(self, event):
        if Path(event.src_path).resolve() != DOCX:
            return
        now = time.time()
        if now - self._last < 4:    # debounce multiple rapid saves
            return
        self._last = now
        open_deploy_terminal()

    on_modified = _handle
    on_created  = _handle


if __name__ == "__main__":
    if not DOCX.exists():
        logging.error(f"'{DOCX}' not found.")
        sys.exit(1)

    logging.info(f"Watcher started. Monitoring: {DOCX.name}")

    handler  = CVHandler()
    observer = Observer()
    observer.schedule(handler, path=str(BASE_DIR), recursive=False)
    observer.start()

    try:
        observer.join()
    except KeyboardInterrupt:
        logging.info("Watcher stopped.")
        observer.stop()
        observer.join()
