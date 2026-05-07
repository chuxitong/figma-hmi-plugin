"""
Re-render week003 pipeline PNGs with the current ``renderer.render_html_to_png`` (fixed paint-wait + file URI).

Run from repo root or ``local-service`` (script resolves paths):

  python rerender_week003_previews.py

Deletes existing target PNGs (and sidecar .b64) then writes new ones.
"""
from __future__ import annotations

import asyncio
import base64
import os
import sys
from pathlib import Path

# Allow ``python local-service/rerender_week003_previews.py`` or cwd = local-service
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORTS = ROOT / "reports"
SHOTS = REPORTS / "screenshots"
W, H = 1280, 720


# (source html path, output png name under screenshots) — same semantics as run_week3_verified.ps1
def _jobs() -> list[tuple[Path, str]]:
    return [
        (REPORTS / "week003_01_generate.html", "week003_01_generate_preview.png"),
        (REPORTS / "week003_02_after_edit.html", "week003_02_after_edit_preview.png"),
        (REPORTS / "week003_02_after_edit.html", "week003_refine_iter1_a_render_in.png"),
        (REPORTS / "week003_refine_iter1.html", "week003_refine_iter1_b_preview.png"),
        (REPORTS / "week003_refine_iter1.html", "week003_refine_iter2_a_render_in.png"),
        (REPORTS / "week003_refine_iter2.html", "week003_refine_iter2_b_preview.png"),
        (REPORTS / "week003_refine_iter2.html", "week003_refine_iter3_a_render_in.png"),
        (REPORTS / "week003_refine_iter3.html", "week003_refine_iter3_b_preview.png"),
    ]


def _remove_if_exists(p: Path) -> None:
    if p.is_file():
        p.unlink()
        print(f"  deleted: {p.name}")


async def _run() -> int:
    os.chdir(HERE)
    sys.path.insert(0, str(HERE))
    from renderer import render_html_to_png, shutdown_renderer  # noqa: WPS433

    SHOTS.mkdir(parents=True, exist_ok=True)
    failed = 0
    for src, png_name in _jobs():
        dest = SHOTS / png_name
        b64_sidecar = dest.with_suffix(".b64")
        if not src.is_file():
            print(f"SKIP (missing source): {src}")
            continue
        html = src.read_text(encoding="utf-8")
        _remove_if_exists(dest)
        _remove_if_exists(b64_sidecar)
        try:
            png = await render_html_to_png(html, W, H)
        except Exception as e:
            print(f"ERR {png_name} <- {src.name}: {e}")
            failed += 1
            continue
        dest.write_bytes(png)
        b64_sidecar.write_text(
            base64.standard_b64encode(png).decode("ascii"), encoding="ascii"
        )
        print(f"OK  {dest.relative_to(ROOT)} ({len(png)} bytes)")

    await shutdown_renderer()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
