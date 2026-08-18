"""
Render the standalone HTML report to a PDF with a real text layer.

The report is a JavaScript bundle: the content is produced at runtime, so
converters that do not execute scripts emit a blank page. Chromium runs
the bundle, then prints to PDF, which preserves selectable text and live
hyperlinks — both required, since the assignment asks for a working link
at the start of the report.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SOURCE = Path("/home/claude/html/report.html").resolve()
OUTPUT = Path("/home/claude/html/Data_Visualization_Report.pdf")


def render() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none"])
        page = browser.new_page(viewport={"width": 1240, "height": 1754})

        page.goto(SOURCE.as_uri(), wait_until="networkidle", timeout=120_000)

        # The bundle paints a placeholder first; wait until it is gone and
        # real content has been mounted before printing.
        try:
            page.wait_for_selector("#__bundler_thumbnail", state="detached", timeout=60_000)
        except Exception:
            print("  note: loading placeholder did not detach; continuing")

        page.wait_for_timeout(6_000)

        text = page.evaluate("document.body.innerText") or ""
        print(f"  rendered text length: {len(text):,} characters")
        if len(text) < 2_000:
            print("  WARNING: very little text rendered — the bundle may not have mounted")

        anchors = page.evaluate(
            "Array.from(document.querySelectorAll('a')).map(a => a.href)"
        )
        print(f"  anchors found: {len(anchors)}")
        for a in anchors[:10]:
            print("    -", a)

        # Fonts must be settled before printing or glyphs fall back.
        page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
        page.emulate_media(media="print")
        page.wait_for_timeout(1_500)

        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        browser.close()

    print(f"  written: {OUTPUT}")


if __name__ == "__main__":
    render()
    sys.exit(0)
