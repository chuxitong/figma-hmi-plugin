"""
Формирует иллюстрации в reports/screenshots из уже сохранённых артефактов
(baseline-tests/outputs/, mockups/png/): панель UI, GIF, сравнения этапов, копии PNG недель 3 и 7.

Запуск: py baseline-tests/build_report_screenshots.py
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports" / "screenshots"


def _ensure_pil():
    try:
        from PIL import Image  # noqa: WPS433
    except ImportError as exc:
        raise SystemExit("Install Pillow: py -m pip install pillow") from exc
    return Image


def _hstack(paths: list[Path], out: Path, target_h: int = 360) -> None:
    Image = _ensure_pil()
    imgs = [Image.open(p).convert("RGB") for p in paths]
    scaled = []
    for im in imgs:
        w, h = im.size
        if h != target_h:
            new_w = int(w * (target_h / h))
            im = im.resize((new_w, target_h), Image.Resampling.LANCZOS)
        scaled.append(im)
    total_w = sum(im.size[0] for im in scaled) + 16 * (len(scaled) - 1)
    canvas = Image.new("RGB", (total_w, target_h), (32, 32, 40))
    x = 0
    for im in scaled:
        canvas.paste(im, (x, 0))
        x += im.size[0] + 16
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "PNG")


async def _screenshot_plugin_ui() -> Path:
    from playwright.async_api import async_playwright

    ui = ROOT / "figma-plugin" / "src" / "ui.html"
    out = REPORTS / "week05_plugin_panel.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    uri = ui.as_uri()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 420, "height": 920})
            await page.goto(uri, wait_until="domcontentloaded")
            await page.screenshot(path=str(out), type="png", full_page=True)
        finally:
            await browser.close()
    return out


def _build_week5_gif(frame_paths: list[Path], out: Path) -> None:
    Image = _ensure_pil()
    frames: list = []
    for p in frame_paths:
        im = Image.open(p).convert("RGB")
        im.thumbnail((720, 405), Image.Resampling.LANCZOS)
        frames.append(im)
    if not frames:
        return
    duration = 900
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
    )


async def main_async() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    out_dir = ROOT / "baseline-tests" / "outputs"

    week3 = [
        ("week03_baseline_test1_generated.png", out_dir / "test1-generated.png"),
        ("week03_baseline_test2_generated.png", out_dir / "test2-generated.png"),
        ("week03_baseline_test3_generated.png", out_dir / "test3-generated.png"),
    ]
    for name, src in week3:
        if src.exists():
            shutil.copy2(src, REPORTS / name)

    fe = out_dir / "full-eval"
    pairs = [
        (
            "week06_m1_reference_generate_refine2.png",
            [
                ROOT / "mockups" / "png" / "01-equipment-status.png",
                fe / "m1_equipment_status" / "generate.png",
                fe / "m1_equipment_status" / "refine_iter2.png",
            ],
        ),
        (
            "week06_m4_reference_generate_refine2.png",
            [
                ROOT / "mockups" / "png" / "04-operator-panel.png",
                fe / "m4_operator_panel" / "generate.png",
                fe / "m4_operator_panel" / "refine_iter2.png",
            ],
        ),
    ]
    for out_name, paths in pairs:
        if all(p.exists() for p in paths):
            _hstack(paths, REPORTS / out_name)

    w7 = out_dir / "week7-edits"
    if w7.exists():
        for p in sorted(w7.glob("edit_*.png")):
            shutil.copy2(p, REPORTS / f"week07_{p.name}")
        base_png = w7 / "base.png"
        if base_png.exists():
            shutil.copy2(base_png, REPORTS / "week07_base.png")

    w7c = out_dir / "week7-context"
    if w7c.exists():
        for p in sorted(w7c.glob("*.png")):
            shutil.copy2(p, REPORTS / f"week07_context_{p.stem}.png")

    ui_shot = await _screenshot_plugin_ui()
    gen_shot = fe / "m1_equipment_status" / "generate.png"
    ref_shot = ROOT / "mockups" / "png" / "01-equipment-status.png"
    gif_frames: list[Path] = []
    if ui_shot.exists():
        gif_frames.append(ui_shot)
    if gen_shot.exists():
        gif_frames.append(gen_shot)
    if ref_shot.exists():
        gif_frames.append(ref_shot)
    if len(gif_frames) >= 2:
        _build_week5_gif(gif_frames, REPORTS / "week05_pipeline_demo.gif")

    readme = REPORTS / "README.txt"
    readme.write_text(
        "Скриншоты и GIF собираются скриптом baseline-tests/build_report_screenshots.py.\n"
        "Исходные данные экспериментов: baseline-tests/outputs/.\n",
        encoding="utf-8",
    )
    print(f"[done] report screenshots -> {REPORTS}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
