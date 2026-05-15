#!/usr/bin/env python3
"""
CV Auto-Deploy Pipeline
- Watches Tehman CV.docx for changes
- Converts to PDF automatically
- Commits and pushes to GitHub
- Vercel picks up the push and auto-deploys
"""

import sys
import time
import subprocess
import os
from pathlib import Path

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


def git(args, **kwargs):
    return subprocess.run(
        ["git"] + args,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        **kwargs
    )


def convert_and_deploy():
    print("\n  Change detected — converting to PDF...", flush=True)

    try:
        convert(str(DOCX), str(PDF))
        print("  PDF updated successfully.", flush=True)
    except Exception as e:
        print(f"  Conversion failed: {e}", flush=True)
        return

    print("  Pushing to GitHub...", flush=True)

    git(["add", "Tehman CV.pdf"])

    result = git(["commit", "-m", "chore: auto-update CV PDF [skip ci]"])
    if "nothing to commit" in result.stdout:
        print("  No changes — PDF was identical, skipping push.\n", flush=True)
        return

    push = git(["push"])
    if push.returncode == 0:
        print("  Pushed! Vercel is now deploying the new version.\n", flush=True)
    else:
        print(f"  Push failed:\n{push.stderr}", flush=True)
        print("  Tip: make sure 'git remote add origin <your-repo-url>' is set.\n", flush=True)


class CVHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_trigger = 0

    def on_modified(self, event):
        if Path(event.src_path).resolve() != DOCX:
            return
        # Debounce: Word/Office saves the file multiple times in quick succession
        now = time.time()
        if now - self._last_trigger < 4:
            return
        self._last_trigger = now
        convert_and_deploy()

    # Also catch "moved to" saves (some editors do atomic saves)
    on_created = on_modified


if __name__ == "__main__":
    if not DOCX.exists():
        print(f"Error: '{DOCX}' not found.")
        sys.exit(1)

    print(f"Watching: {DOCX}")
    print("Edit and save the .docx file to trigger an auto-deploy.")
    print("Press Ctrl+C to stop.\n")

    handler  = CVHandler()
    observer = Observer()
    observer.schedule(handler, path=str(BASE_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        observer.stop()

    observer.join()
