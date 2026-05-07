#!/usr/bin/env python3
"""
Rasterise authoritative screen SVGs to PNG (mockups/png/01–08).

⚠️ 不得在此文件手写内联 HTML 来冒充工业画面；必须与
   ``mockups/layered-svg/screens/*.svg`` 像素级一致后再截屏导出。

Recommended:
    cd repo && local-service/.venv/bin/python mockups/build_mockups.py

Uses the same Chromium pipeline as `_localtools/rasterise_svg.py`.
"""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parents[1]
SCREENS = REPO / "mockups" / "layered-svg" / "screens"
PNG_DIR = REPO / "mockups" / "png"

STEMS = [
    "01-equipment-status",
    "02-alarm-event",
    "03-trend-monitor",
    "04-operator-panel",
    "05-production-overview",
    "06-tank-synoptic",
    "07-energy-dashboard",
    "08-batch-recipe",
]


def svg_viewport(path: Path) -> tuple[int, int]:
    head = path.read_text(encoding="utf-8")[:2000]
    mw = re.search(r'\bwidth="(\d+)"', head)
    mh = re.search(r'\bheight="(\d+)"', head)
    if not mw or not mh:
        raise SystemExit(f"Cannot parse svg width/height from {path}")
    return int(mw.group(1)), int(mh.group(1))


async def _shoot(browser, src: Path, dst: Path, w: int, h: int) -> None:
    page = await browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:#f3f5f8;}</style>"
        f"</head><body>{src.read_text(encoding='utf-8')}</body></html>"
    )
    await page.set_content(html, wait_until="load")
    await page.screenshot(
        path=str(dst),
        full_page=False,
        omit_background=False,
        clip={"x": 0, "y": 0, "width": w, "height": h},
    )
    await page.close()
    print(f"  ✓ {dst.name} ({w}×{h})")


async def main() -> int:
    if not SCREENS.is_dir():
        print(f"Missing screens dir: {SCREENS}", file=sys.stderr)
        return 1
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for stem in STEMS:
            svg = SCREENS / f"{stem}.svg"
            if not svg.is_file():
                print(f"Missing SVG: {svg}", file=sys.stderr)
                await browser.close()
                return 1
            w, h = svg_viewport(svg)
            dst = PNG_DIR / f"{stem}.png"
            await _shoot(browser, svg, dst, w, h)
        await browser.close()
    print(f"\nDone — {len(STEMS)} PNGs from layered-svg/screens → {PNG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
