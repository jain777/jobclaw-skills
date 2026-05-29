#!/usr/bin/env python3
"""Deterministic layout QA for a rendered resume — the cheap first gate of the
review-render loop (no vision tokens). Measures page count and how far real ink
reaches down each page, so the loop can objectively flag under-fill (bottom
whitespace) and sparse trailing pages before calling Claude's vision rubric.

Run with the render-resume venv python (needs Pillow):
    .venv/bin/python qa_report.py <page1.png> [<page2.png> ...]

Emits JSON to stdout:
    {
      "pages": 2,
      "page_fills": [0.94, 0.31],     # ink_bottom / page_height, per page
      "last_page_fill": 0.31,
      "flags": ["sparse_last_page"],  # underfilled | sparse_last_page | overflow_risk
      "notes": "..."
    }

Heuristics are intentionally conservative; the nuanced calls (widows, balance,
alignment, readability) are the vision rubric's job, not this script's.
"""
import json
import sys

try:
    from PIL import Image
except ImportError:
    print(json.dumps({"error": "Pillow not installed in this interpreter; "
                               "run with the render-resume venv python."}))
    sys.exit(0)

# A page is "full enough" when ink reaches at least this far down (fraction of height).
FULL_THRESHOLD = 0.90
# A trailing page with less than this fill is wastefully sparse (should pull up / trim).
SPARSE_THRESHOLD = 0.45
# Ink detection: pixels darker than this (0-255 grayscale) count as content.
INK_CUTOFF = 235


def _ink_bottom_fraction(path):
    """Return (fill_fraction, page_w, page_h): how far down the lowest ink pixel sits."""
    im = Image.open(path).convert("L")
    w, h = im.size
    # Map near-white -> 0, ink -> 255, then getbbox finds the content rectangle.
    ink = im.point(lambda px: 255 if px < INK_CUTOFF else 0)
    bbox = ink.getbbox()  # (left, top, right, bottom) of non-zero region, or None
    if not bbox:
        return 0.0, w, h
    return bbox[3] / h, w, h


def main():
    paths = sys.argv[1:]
    if not paths:
        print(json.dumps({"error": "no PNG paths given"}))
        return 0

    fills = []
    for p in paths:
        try:
            frac, _, _ = _ink_bottom_fraction(p)
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"error": f"could not read {p}: {e}"}))
            return 0
        fills.append(round(frac, 3))

    pages = len(fills)
    last = fills[-1]
    flags, notes = [], []

    if pages == 1 and last < FULL_THRESHOLD:
        flags.append("underfilled")
        notes.append(f"single page only {int(last * 100)}% filled — restore content or "
                     f"loosen density to fill the page.")
    if pages > 1 and last < SPARSE_THRESHOLD:
        flags.append("sparse_last_page")
        notes.append(f"page {pages} only {int(last * 100)}% filled — trim to one page "
                     f"(densify / cut lowest-value lines) or rebalance.")
    # Every non-final page essentially full + a barely-used final page already covered above.
    if pages > 1 and all(f > 0.97 for f in fills[:-1]) and 0.0 < last < 0.15:
        if "overflow_risk" not in flags:
            flags.append("overflow_risk")
            notes.append("content spills just past a page boundary — a small trim likely "
                         "recovers a page.")

    print(json.dumps({
        "pages": pages,
        "page_fills": fills,
        "last_page_fill": last,
        "flags": flags,
        "notes": " ".join(notes) or "no deterministic layout issues detected.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
