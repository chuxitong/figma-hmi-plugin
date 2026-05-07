"""
Capture mentor-facing screenshots after week3 run: Swagger /docs and optional HTML files.
Run only while uvicorn is up on the given base URL.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from urllib.request import urlopen

async def _swagger_screenshot(out: Path, base: str) -> bool:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("playwright not installed; skip swagger screenshot", file=sys.stderr)
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    url = base.rstrip("/") + "/docs"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 2000})
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await page.screenshot(path=str(out), full_page=True, type="png")
        finally:
            await browser.close()
    return True


def _health_json(base: str) -> dict:
    with urlopen(base.rstrip("/") + "/health", timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000", help="API base")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "reports" / "screenshots",
    )
    args = ap.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        h = _health_json(args.base)
    except OSError as e:
        print(f"health check failed: {e}", file=sys.stderr)
        sys.exit(1)
    (out_dir / "week003_health_snapshot.json").write_text(
        json.dumps(h, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    out_png = out_dir / "week003_swagger_api_docs.png"
    ok = asyncio.run(_swagger_screenshot(out_png, args.base))
    print(json.dumps({"health": h, "swagger_png": str(out_png) if ok else None}))


if __name__ == "__main__":
    main()
