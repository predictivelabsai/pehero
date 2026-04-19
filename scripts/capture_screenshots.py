"""Capture a tour of the PEHero app into ./screenshots.

The script drives a real browser via Playwright against a locally-running
PEHero server (default http://localhost:5057). It produces a deterministic
set of frames for `make_gif.py` and `make_pdf.py`.

Usage:
    # server already running on :5057
    python -m scripts.capture_screenshots
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

log = logging.getLogger("capture")

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"

BASE_URL = os.environ.get("PEHERO_URL", "http://localhost:5057")
VIEWPORT = {"width": 1400, "height": 900}


TOUR = [
    # (filename, url, wait_selector, full_page, post_action)
    ("01-home-full.png",          "/",                       "text=22 specialist agents",    True,  None),
    ("02-platform-full.png",      "/platform",               "text=One system. Every stage", True,  None),
    ("03-agents-full.png",        "/agents",                 "text=Every role already",      True,  None),
    ("04-agent-detail-triage.png","/agents/deal_triage",     "text=Deal Triage Agent",       True,  None),
    ("05-how-it-works-full.png",  "/how-it-works",           "text=From broker flyer",       True,  None),
    ("06-pricing-full.png",       "/pricing",                "text=Start with synthetic",    True,  None),
    ("07-chat-empty.png",         "/app",                    "#chat-input",                  False, None),
    # chat flow — type + stream
    ("08-chat-rentroll.png",      "/app",                    "#chat-input",                  True, "rentroll"),
    ("09-chat-pro-forma.png",     "/app",                    "#chat-input",                  True, "proforma"),
    ("10-chat-memo.png",          "/app",                    "#chat-input",                  True, "memo"),
]


CHAT_MSGS = {
    "rentroll": "rr: summarize the rent roll for Silver Spring East Austin",
    "proforma": "pf: 5-year pro forma for Silver Spring East Austin at 3.5% rent growth",
    "memo":     "memo: draft the investment memo for Silver Spring East Austin",
}


def _run_chat(page, msg: str) -> None:
    page.fill("#chat-input", msg)
    page.evaluate(
        "() => document.querySelector('#chat-form').dispatchEvent("
        "new Event('submit', {cancelable: true}))"
    )
    # wait for agent_route + at least one assistant bubble with text
    page.wait_for_function(
        """() => {
            const m = document.querySelector('#messages');
            if (!m) return false;
            const bubbles = m.querySelectorAll('.msg-assistant .msg-bubble');
            if (!bubbles.length) return false;
            const last = bubbles[bubbles.length-1];
            return last && (last.textContent||'').length > 80
                   && !last.parentElement.classList.contains('streaming');
        }""",
        timeout=90_000,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    SHOTS.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = ctx.new_page()

        for fname, path, wait_for, full_page, action in TOUR:
            url = BASE_URL + path
            log.info("→ %s", url)
            page.goto(url, wait_until="networkidle", timeout=30_000)
            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=10_000)
                except Exception:
                    log.warning("selector %r didn't appear on %s", wait_for, path)
            if action and action in CHAT_MSGS:
                _run_chat(page, CHAT_MSGS[action])
                time.sleep(0.4)  # paint

            out = SHOTS / fname
            page.screenshot(path=str(out), full_page=full_page)
            log.info("  saved %s", out.relative_to(ROOT))

        browser.close()
    log.info("done — %d frames in %s", len(TOUR), SHOTS)


if __name__ == "__main__":
    main()
