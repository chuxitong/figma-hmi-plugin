"""
HTML-to-PNG rendering module using Playwright headless browser.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_browser = None
_playwright = None
_browser_lock = asyncio.Lock()


def _goto_timeout_ms() -> int:
    """CDN + in-browser Babel can exceed 120s on cold cache; override via env."""
    raw = os.environ.get("PLAYWRIGHT_GOTO_TIMEOUT_MS", "").strip()
    if raw.isdigit():
        return max(30_000, int(raw))
    return 300_000


async def _get_browser():
    global _browser, _playwright
    if _browser is not None:
        return _browser
    async with _browser_lock:
        if _browser is None:
            from playwright.async_api import async_playwright

            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(headless=True)
    return _browser


def _normalise_html_document(html_code: str) -> str:
    """Ensure the browser receives a standards-mode HTML document.

    Model output is sometimes a fragment or a full document without a doctype.
    Chromium then falls back to quirks mode, which can distort spacing and
    layout in screenshots and make the render look "wrong" even when the HTML
    itself is acceptable.
    """
    text = (html_code or "").lstrip("\ufeff")
    stripped = text.lstrip()
    if not stripped.lower().startswith("<!doctype html"):
        logger.info("render_html_to_png: prepending missing <!DOCTYPE html>.")
        return "<!DOCTYPE html>\n" + text
    return text


def _js_mount_ready() -> str:
    """Return a browser function string: true when there is real UI to capture.

    If a mount node exists (``#root`` / ``#app``), we **only** treat the page
    as ready when that node has real content. Otherwise ``body`` background
    (e.g. ``#f1f5f9``) plus early ``innerText``/structural heuristics could
    succeed while React/Babel is still working — leaving an empty root and a
    uniform "blank" PNG.
    """
    return """
    () => {
      const byId = (id) => document.getElementById(id);
      const root = byId("root");
      const app = byId("app");
      const mount = root || app;
      if (mount) {
        const inner = (mount.innerHTML || "").replace(/\\s/g, "");
        if (mount.children && mount.children.length > 0) return true;
        if (inner.length > 60) return true;
        return false;
      }
      const b = document.body;
      if (!b) return false;
      const t = (b.innerText || "").trim();
      if (t.length > 10) return true;
      if (b.querySelector(
        "svg, table, canvas, img, main, section, header, article, aside, nav, footer, [role=main]"
      )) {
        return true;
      }
      return false;
    }
    """


async def _wait_for_something_to_paint(page, timeout_ms: int = 90_000) -> None:
    """Wait until client-rendered (React/Babel) or static content is visible.

    VLM output often references React+CDN+Tailwind. ``networkidle`` can fire
    while ``#root`` is still empty (Babel/JSX not yet mounted), which yields
    all-white captures — the user-visible blank PNG issue.

    We no longer use ``body.scrollHeight`` alone: empty ``#root`` with Tailwind
    on ``body`` still looked ``tall`` and fooled early heuristics.

    If the optional CDN/JS never completes (no network, blocked), the poll may
    time out; we then add a long fallback sleep so slow links can still finish.
    """
    await asyncio.sleep(2.0)  # let first external scripts and layout start
    try:
        await page.wait_for_function(_js_mount_ready(), timeout=timeout_ms)
    except Exception as e:
        logger.warning(
            "Paint wait timed out (CDN/JS may be slow or blocked); extra delay then screenshot: %s",
            e,
        )
        await asyncio.sleep(20.0)
    else:
        await asyncio.sleep(1.0)
        await asyncio.sleep(0.4)


async def _post_poll_root_if_still_empty(page, max_wait_s: float = 90.0) -> None:
    """If #root|#app exists but is still empty, keep polling (Babel late mount)."""
    js_empty = """
    () => {
      const m = document.getElementById("root") || document.getElementById("app");
      if (!m) return false;
      const inner = (m.innerHTML || "").replace(/\\s/g, "");
      if (m.children && m.children.length > 0) return false;
      if (inner.length > 60) return false;
      return true;
    }
    """
    deadline = time.monotonic() + max_wait_s
    while time.monotonic() < deadline:
        try:
            still = await page.evaluate(js_empty)
        except Exception:
            still = False
        if not still:
            return
        await asyncio.sleep(1.5)
    logger.warning(
        "Mount node (#root/#app) still empty after %ss; screenshot may be blank (CDN/JS or broken JSX).",
        int(max_wait_s),
    )


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
    goto_ms = _goto_timeout_ms()
    page.set_default_timeout(goto_ms)
    html_doc = _normalise_html_document(html_code)

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    try:
        tmp.write(html_doc)
        tmp.close()
        # Windows: ``file://C:\...`` is invalid; use RFC file URI.
        file_url = Path(tmp.name).as_uri()
        # ``load`` waits for external scripts to be fetched/executed start; for CDN+in-browser
        # Babel, real paint happens later than first ``load``; ``networkidle`` helps CDNs
        # finish. We still do a mount-aware paint wait (see _js_mount_ready).
        await page.goto(file_url, wait_until="load", timeout=goto_ms)
        try:
            idle_ms = min(120_000, max(20_000, goto_ms // 2))
            await page.wait_for_load_state("networkidle", timeout=idle_ms)
        except Exception as e:
            logger.debug("networkidle after load skipped: %s", e)
        paint_ms = min(180_000, max(90_000, goto_ms - 30_000))
        await _wait_for_something_to_paint(page, timeout_ms=paint_ms)
        await _post_poll_root_if_still_empty(page, max_wait_s=min(90.0, paint_ms / 1000.0))
        png_bytes = await page.screenshot(full_page=False, type="png")
    finally:
        await page.close()
        try:
            os.unlink(tmp.name)
        except FileNotFoundError:
            pass

    return png_bytes


async def shutdown_renderer() -> None:
    """Close Playwright browser to avoid asyncio teardown warnings on Windows."""
    global _browser, _playwright
    if _browser is not None:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright is not None:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None
