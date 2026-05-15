#!/usr/bin/env python3
"""
CV Auto-Deploy Pipeline — runs silently in the background.
Watches Tehman CV.docx, converts to PDF, pushes to GitHub.
Vercel auto-deploys on every push.
"""

import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "watchdog"], check=True)
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

try:
    from docx2pdf import convert
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "docx2pdf"], check=True)
    from docx2pdf import convert

BASE_DIR = Path(__file__).parent.resolve()
DOCX     = BASE_DIR / "Tehman CV.docx"
PDF      = BASE_DIR / "Tehman CV.pdf"
LOG_FILE = BASE_DIR / "watcher.log"

# Log to file so you can check what happened even when running silently
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def log(msg):
    logging.info(msg)
    print(msg, flush=True)


def git(args):
    return subprocess.run(
        ["git"] + args,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )


def convert_and_deploy():
    log("Change detected — converting to PDF...")

    try:
        convert(str(DOCX), str(PDF))
        log("PDF updated.")
    except Exception as e:
        log(f"Conversion failed: {e}")
        return

    log("Pushing to GitHub...")
    git(["add", "Tehman CV.pdf"])

    result = git(["commit", "-m", "chore: auto-update CV PDF [skip ci]"])
    if "nothing to commit" in result.stdout:
        log("PDF unchanged — nothing to push.")
        return

    push = git(["push"])
    if push.returncode == 0:
        log("Pushed. Vercel is deploying the new version.")
    else:
        log(f"Push failed: {push.stderr.strip()}")


class CVHandler(FileSystemEventHandler):
    def __init__(self):
        self._last = 0

    def _handle(self, event):
        if Path(event.src_path).resolve() != DOCX:
            return
        now = time.time()
        if now - self._last < 4:   # debounce — Word saves multiple times
            return
        self._last = now
        convert_and_deploy()

    on_modified = _handle
    on_created  = _handle


if __name__ == "__main__":
    if not DOCX.exists():
        log(f"Error: '{DOCX}' not found.")
        sys.exit(1)

    log(f"Watcher started. Monitoring: {DOCX.name}")

    handler  = CVHandler()
    observer = Observer()
    observer.schedule(handler, path=str(BASE_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Watcher stopped.")
        observer.stop()

    observer.join()
