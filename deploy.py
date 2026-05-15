"""
CV Deploy Script — runs in a visible terminal window.
Shows step-by-step progress: convert → push → Vercel live status.
"""

import sys
import os
import time
import subprocess
import urllib.request
import urllib.error
import json
from pathlib import Path
from datetime import datetime

# Enable ANSI colours on Windows
os.system("")

BASE_DIR = Path(__file__).parent.resolve()
DOCX     = BASE_DIR / "Tehman CV.docx"
PDF      = BASE_DIR / "Tehman CV.pdf"

# ── Colours ────────────────────────────────────────────────────────────────────
G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
C  = "\033[96m"   # cyan
B  = "\033[1m"    # bold
D  = "\033[2m"    # dim
RS = "\033[0m"    # reset

def header():
    w = 52
    print(f"\n{B}{'─' * w}{RS}")
    print(f"{B}  CV Auto-Deploy Pipeline{RS}  {D}{datetime.now().strftime('%d %b %Y  %H:%M:%S')}{RS}")
    print(f"{B}{'─' * w}{RS}\n")

def step(n, label):
    print(f"{B}{C}  [{n}] {label}{RS}")

def ok(msg):
    print(f"      {G}✓{RS}  {msg}")

def fail(msg):
    print(f"      {R}✗{RS}  {msg}")

def info(msg):
    print(f"      {D}{msg}{RS}")

def done_banner():
    w = 52
    print(f"\n{G}{B}{'─' * w}{RS}")
    print(f"{G}{B}      All done! Your CV is live on Vercel.{RS}")
    print(f"{G}{B}{'─' * w}{RS}\n")


# ── Git helper ─────────────────────────────────────────────────────────────────
def git(args):
    return subprocess.run(
        ["git"] + args,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )


# ── Vercel API helpers ─────────────────────────────────────────────────────────
def vercel_request(path, token):
    req = urllib.request.Request(
        f"https://api.vercel.com{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


def wait_for_vercel(token, project_name, pushed_at):
    """Poll Vercel API until the latest deployment is READY or ERROR."""
    print()
    info("Polling Vercel for deployment status...")

    deadline = time.time() + 180  # give up after 3 minutes
    last_state = ""
    deployment_url = ""

    while time.time() < deadline:
        data = vercel_request(f"/v6/deployments?limit=5&projectSlug={project_name}", token)
        if not data:
            time.sleep(5)
            continue

        deployments = data.get("deployments", [])
        if not deployments:
            time.sleep(5)
            continue

        latest = deployments[0]
        state  = latest.get("state", "").upper()      # BUILDING / READY / ERROR
        url    = latest.get("url", "")
        created = latest.get("createdAt", 0) / 1000   # ms → s

        # Only track deployments created after our push
        if created < pushed_at - 10:
            info("Waiting for Vercel to pick up the push...")
            time.sleep(5)
            continue

        deployment_url = f"https://{url}" if url else ""

        if state != last_state:
            if state == "BUILDING":
                print(f"\r      {Y}⟳{RS}  Building...                    ", end="", flush=True)
            elif state == "READY":
                print(f"\r      {G}✓{RS}  Deployment READY!              ")
                return True, deployment_url
            elif state in ("ERROR", "CANCELED"):
                print(f"\r      {R}✗{RS}  Deployment {state}!              ")
                return False, deployment_url
            last_state = state

        # Show a spinner while building
        for ch in "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏":
            print(f"\r      {Y}{ch}{RS}  {state.capitalize()}...             ", end="", flush=True)
            time.sleep(0.3)

    print(f"\r      {Y}?{RS}  Timed out waiting — check Vercel dashboard.  ")
    return False, deployment_url


def countdown_fallback(seconds=45):
    """Show a countdown when no Vercel token is configured."""
    info("No Vercel token configured — using countdown instead.")
    info(f"(Add VERCEL_TOKEN to config.py for live status)")
    print()
    for i in range(seconds, 0, -1):
        bar   = "█" * (seconds - i) + "░" * i
        short = bar[:30]
        print(f"\r      {D}Deploying  [{short}]  {i:2d}s{RS}", end="", flush=True)
        time.sleep(1)
    print(f"\r      {G}✓{RS}  Should be live now!                          ")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    try:
        import config
        VERCEL_URL     = getattr(config, "VERCEL_URL",     "").strip()
        VERCEL_TOKEN   = getattr(config, "VERCEL_TOKEN",   "").strip()
        VERCEL_PROJECT = getattr(config, "VERCEL_PROJECT", "").strip()
    except ImportError:
        VERCEL_URL = VERCEL_TOKEN = VERCEL_PROJECT = ""

    try:
        from docx2pdf import convert
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "docx2pdf", "-q"])
        from docx2pdf import convert

    header()

    # ── Step 1: Convert ────────────────────────────────────────────────────────
    step(1, "Converting .docx → PDF")
    try:
        convert(str(DOCX), str(PDF))
        ok("PDF updated successfully")
    except Exception as e:
        fail(f"Conversion failed: {e}")
        input("\n  Press Enter to close...")
        return

    # ── Step 2: Git commit & push ──────────────────────────────────────────────
    print()
    step(2, "Pushing to GitHub")

    git(["add", "Tehman CV.pdf"])
    commit = git(["commit", "-m", "chore: auto-update CV PDF [skip ci]"])

    if "nothing to commit" in commit.stdout or "nothing to commit" in commit.stderr:
        ok("PDF is identical — nothing to push")
        done_banner()
        input("  Press Enter to close...")
        return

    pushed_at = time.time()
    push = git(["push"])

    if push.returncode != 0:
        fail("Push failed:")
        for line in push.stderr.strip().splitlines():
            info(f"  {line}")
        info("Make sure 'git remote add origin <url>' is set and you have internet.")
        input("\n  Press Enter to close...")
        return

    ok("Pushed to GitHub")

    # ── Step 3: Vercel deployment ──────────────────────────────────────────────
    print()
    step(3, "Vercel Deployment")

    if VERCEL_TOKEN and VERCEL_PROJECT:
        success, deployment_url = wait_for_vercel(VERCEL_TOKEN, VERCEL_PROJECT, pushed_at)
        if success:
            url_to_show = VERCEL_URL or deployment_url
            if url_to_show:
                ok(f"Live at: {B}{url_to_show}{RS}")
        else:
            fail("Deployment had an error — check your Vercel dashboard.")
            if VERCEL_URL:
                info(f"Dashboard: https://vercel.com")
    else:
        countdown_fallback(45)
        if VERCEL_URL:
            ok(f"Live at: {B}{VERCEL_URL}{RS}")
        else:
            ok("Vercel should be live now.")
            info("Add VERCEL_URL to config.py to see your link here.")

    done_banner()
    input("  Press Enter to close...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Y}Cancelled.{RS}\n")
