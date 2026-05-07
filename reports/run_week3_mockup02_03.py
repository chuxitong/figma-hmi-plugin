"""
与 ``run_week3_verified.py`` 相同步骤，对 mockups/png 下 02、03 各跑一遍完整流水线：

  mockup PNG → POST /generate → 保存 ``{stem}_01_generate*`` 与 ``{stem}_00_reference.png``（从 mockup 复制）
  → POST /edit（instruction 与主脚本一致）
  → 三轮 POST /render + POST /refine

文件前缀：
  - ``week003_m02`` 对应 ``02-alarm-event.png``
  - ``week003_m03`` 对应 ``03-trend-monitor.png``

若 ``/generate`` 或 ``/edit`` 未返回 ``preview_base64``，则用 ``POST /render`` 补全预览图（与主流程目标一致）。

  export API_BASE=http://127.0.0.1:8000
  local-service/.venv/bin/python reports/run_week3_mockup02_03.py
"""
from __future__ import annotations

import base64
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports"
SHOT = OUT / "screenshots"
REFINE_ROUNDS = 3
EDIT_INSTRUCTION = "Increase the main page title font size and make it more prominent."
REQUEST_TIMEOUT = 7200


def _base() -> str:
    import os

    b = (os.environ.get("API_BASE") or "").strip()
    return b if b else "http://127.0.0.1:8000"


def _post_json(path: str, body: object) -> dict:
    url = _base().rstrip("/") + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _assert_ui2() -> None:
    with urllib.request.urlopen(_base().rstrip("/") + "/health", timeout=30) as r:
        h = json.loads(r.read().decode("utf-8"))
    if not h.get("ui2code_n_active"):
        raise SystemExit(
            f"Refuse to record: ui2code_n_active is false. model_kind={h.get('model_kind')!r}."
        )


def _b64file(p: Path) -> str:
    return base64.standard_b64encode(p.read_bytes()).decode("ascii")


def _png_size(p: Path) -> tuple[int, int]:
    """Viewport must match mockup PNG (e.g. 1440×900 from layered-svg export)."""
    from PIL import Image

    with Image.open(p) as im:
        return int(im.width), int(im.height)


def _write_png_b64(b64: str | None, path: Path) -> None:
    if not b64:
        return
    path.write_bytes(base64.standard_b64decode(b64))


def _write_json(obj: object, path: Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_b64_text(b64: str | None, path: Path) -> None:
    if not b64:
        return
    path.write_text(b64, encoding="ascii", errors="strict")


def _ensure_preview_from_render(
    code: str,
    png_path: Path,
    b64_path: Path,
    lines: list[str],
    label: str,
    w: int,
    h: int,
) -> str | None:
    lines.append(f"    ({label}: API 无 preview_base64，POST /render 补图)")
    t0 = time.time()
    rend = _post_json("/render", {"html_code": code, "width": w, "height": h})
    lines.append(f"    /render elapsed {round(time.time() - t0, 1)}s")
    b64 = rend.get("image_base64")
    if b64:
        _write_png_b64(b64, png_path)
        _write_b64_text(b64, b64_path)
    return b64


def run_one_mockup(ref_png: Path, frame_name: str, stem: str, base: str, lines: list[str]) -> None:
    if not ref_png.is_file():
        lines.append(f"SKIP {stem}: missing {ref_png}")
        return

    rw, rh = _png_size(ref_png)
    lines.append(f"========== {stem} ref={ref_png} frame={frame_name!r} viewport={rw}x{rh} ==========")
    b64_ref = _b64file(ref_png)

    # 0) reference snapshot（与 week003_00_reference 对 01 的做法一致）
    shutil.copy2(ref_png, SHOT / f"{stem}_00_reference.png")
    lines.append(f"    copied mockup → screenshots/{stem}_00_reference.png")

    # 1) generate（输入即为 mockups 下 PNG，与第一个实例一致）
    t0 = time.time()
    lines.append("[1] POST /generate ...")
    gen = _post_json(
        "/generate",
        {
            "image_base64": b64_ref,
            "frame_name": frame_name,
            "width": rw,
            "height": rh,
        },
    )
    lines.append(f"    elapsed {round(time.time() - t0, 1)}s")
    _assert_ui2()
    code = gen.get("code") or ""
    (OUT / f"{stem}_01_generate.html").write_text(code, encoding="utf-8")
    _write_json(gen, OUT / f"{stem}_01_generate_response.json")
    pv = gen.get("preview_base64")
    if not pv:
        pv = _ensure_preview_from_render(
            code,
            SHOT / f"{stem}_01_generate_preview.png",
            SHOT / f"{stem}_01_generate_preview.b64",
            lines,
            "generate",
            rw,
            rh,
        )
    else:
        _write_png_b64(pv, SHOT / f"{stem}_01_generate_preview.png")
        _write_b64_text(pv, SHOT / f"{stem}_01_generate_preview.b64")
    lines.append(
        f"    saved: {stem}_01_generate.html, {stem}_01_generate_response.json, {stem}_01_generate_preview.png|.b64"
    )

    lines.extend(
        [
            "",
            f"--- POST /edit（{stem}_02_after_edit*）---",
            f"  instruction: {EDIT_INSTRUCTION!r}",
            "",
        ]
    )

    # 2) edit
    t1 = time.time()
    lines.append("[2] POST /edit ...")
    ed = _post_json(
        "/edit",
        {
            "current_code": code,
            "instruction": EDIT_INSTRUCTION,
            "width": rw,
            "height": rh,
        },
    )
    lines.append(f"    elapsed {round(time.time() - t1, 1)}s")
    _assert_ui2()
    code = ed.get("code") or code
    (OUT / f"{stem}_02_after_edit.html").write_text(code, encoding="utf-8")
    _write_json(ed, OUT / f"{stem}_02_after_edit_response.json")
    pv_ed = ed.get("preview_base64")
    if not pv_ed:
        pv_ed = _ensure_preview_from_render(
            code,
            SHOT / f"{stem}_02_after_edit_preview.png",
            SHOT / f"{stem}_02_after_edit_preview.b64",
            lines,
            "after_edit",
            rw,
            rh,
        )
    else:
        _write_png_b64(pv_ed, SHOT / f"{stem}_02_after_edit_preview.png")
        _write_b64_text(pv_ed, SHOT / f"{stem}_02_after_edit_preview.b64")
    lines.append(f"    saved: {stem}_02_after_edit*")

    # 3) refine（reference 始终为对应 mockup 的 PNG，与主流程一致）
    code_ref = code
    for i in range(1, REFINE_ROUNDS + 1):
        lines.append(f"[3.{i}] render + refine ...")
        rend = _post_json(
            "/render",
            {"html_code": code_ref, "width": rw, "height": rh},
        )
        r_b64 = rend.get("image_base64") or ""
        a_name = f"{stem}_refine_iter{i}_a_render_in.png"
        _write_png_b64(r_b64, SHOT / a_name)
        _write_json(rend, OUT / f"{stem}_refine_iter{i}_render_api.json")
        _write_b64_text(r_b64, SHOT / f"{stem}_refine_iter{i}_a_render_in.b64")
        t2 = time.time()
        rf = _post_json(
            "/refine",
            {
                "reference_image_base64": b64_ref,
                "current_code": code_ref,
                "rendered_image_base64": r_b64,
                "width": rw,
                "height": rh,
            },
        )
        lines.append(f"    refine elapsed {round(time.time() - t2, 1)}s")
        _assert_ui2()
        code_ref = rf.get("code") or code_ref
        b_name = f"{stem}_refine_iter{i}_b_preview.png"
        _write_png_b64(rf.get("preview_base64"), SHOT / b_name)
        _write_json(rf, OUT / f"{stem}_refine_iter{i}_refine_response.json")
        _write_b64_text(rf.get("preview_base64"), SHOT / f"{stem}_refine_iter{i}_b_preview.b64")
        (OUT / f"{stem}_refine_iter{i}.html").write_text(code_ref, encoding="utf-8")
        lines.append(f"    saved: {a_name}, {b_name}, {stem}_refine_iter{i}.html")
        lines.append("")

    lines.append("")


def main() -> int:
    base = _base()
    SHOT.mkdir(parents=True, exist_ok=True)
    mock_dir = ROOT / "mockups" / "png"

    lines: list[str] = [
        "=== Week3 mockup 02 & 03 — 与 run_week3_verified 相同步骤 ===",
        f"API_BASE={base}",
        f"Edit instruction: {EDIT_INSTRUCTION!r}",
        f"Refine rounds: {REFINE_ROUNDS}",
        "Reference 均来自 mockups/png（复制为各 stem 的 *_00_reference.png）",
        "",
    ]

    run_one_mockup(
        mock_dir / "02-alarm-event.png",
        "Alarm & Event Screen",
        "week003_m02",
        base,
        lines,
    )
    run_one_mockup(
        mock_dir / "03-trend-monitor.png",
        "Trend Monitor",
        "week003_m03",
        base,
        lines,
    )

    summary = f"""=== POST /edit 指令（与 run_week3_verified.py 一致）===
{EDIT_INSTRUCTION}

各 mockup 的 current_code 为对应 week003_m02_01_generate.html / week003_m03_01_generate.html。
"""
    (OUT / "week003_mockup02_03_RECORD.txt").write_text(summary, encoding="utf-8")
    (OUT / "week003_mockup02_03_RUN_LOG.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(summary)
    print(f"Wrote {OUT / 'week003_mockup02_03_RUN_LOG.txt'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        raise SystemExit(1)
