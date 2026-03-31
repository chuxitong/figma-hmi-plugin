"""
HTML-to-PNG rendering module using Playwright headless browser.
"""

import asyncio
import tempfile
import os

_browser = None
_playwright = None


async def _get_browser():
    global _browser, _playwright
    if _browser is None:
        from playwright.async_api import async_playwright
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
    return _browser


async def render_html_to_png(
    html_code: str,
    width: int = 1280,
    height: int = 720,
) -> bytes:
    """
    Render an HTML string into a PNG screenshot.

    Args:
        html_code: Complete HTML document as a string.
        width: Viewport width in pixels.
        height: Viewport height in pixels.

    Returns:
        PNG image as bytes.
    """
    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": width, "height": height})

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    try:
        tmp.write(html_code)
        tmp.close()
        await page.goto(f"file://{tmp.name}", wait_until="networkidle")
        png_bytes = await page.screenshot(full_page=False, type="png")
    finally:
        await page.close()
        os.unlink(tmp.name)

    return png_bytes
