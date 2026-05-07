"""
Linux-friendly clone of run_week3_verified.ps1 for remote GPUs (e.g. AutoDL).

  export API_BASE=http://127.0.0.1:8000
  python reports/run_week3_verified.py

Project root is detected from this file’s location; requires an active local-service
(USE_REAL_MODEL=1, real weights). Refuses to write artifacts if /health has
ui2code_n_active false.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports"
SHOT = OUT / "screenshots"
REF_PNG = ROOT / "mockups" / "png" / "01-equipment-status.png"
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
    """Match API viewport / render pipeline to reference PNG pixels (often 1440×900)."""
    from PIL import Image

    with Image.open(p) as im:
        return int(im.width), int(im.height)


def _write_png_b64(b64: str | None, path: Path) -> None:
    if not b64:
        return
    path.write_bytes(base64.standard_b64decode(b64))


def _write_json(obj: object, path: Path) -> None:
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_b64_text(b64: str | None, path: Path) -> None:
    if not b64:
        return
    path.write_text(b64, encoding="ascii", errors="strict")


def main() -> int:
    base = _base()
    if not REF_PNG.is_file():
        print(f"Missing input mockup: {REF_PNG}", file=sys.stderr)
        return 1
    SHOT.mkdir(parents=True, exist_ok=True)
    vw, vh = _png_size(REF_PNG)

    lines: list[str] = [
        f"=== Week3 verified run (python) base={base} ===",
        f"Ref PNG: {REF_PNG}",
        f"Viewport from PNG: {vw} x {vh}",
        f"Edit instruction: {EDIT_INSTRUCTION!r}",
        f"Refine rounds: {REFINE_ROUNDS}",
        "",
    ]

    # 1) generate
    t0 = time.time()
    lines.append("[1] POST /generate ...")
    gen = _post_json(
        "/generate",
        {
            "image_base64": _b64file(REF_PNG),
            "frame_name": "Equipment Status Dashboard",
            "width": vw,
            "height": vh,
        },
    )
    lines.append(f"    elapsed {round(time.time() - t0, 1)}s")
    _assert_ui2()
    code = gen.get("code") or ""
    (OUT / "week003_01_generate.html").write_text(code, encoding="utf-8")
    _write_png_b64(gen.get("preview_base64"), SHOT / "week003_01_generate_preview.png")
    _write_json(gen, OUT / "week003_01_generate_response.json")
    _write_b64_text(gen.get("preview_base64"), SHOT / "week003_01_generate_preview.b64")
    import shutil

    shutil.copy2(REF_PNG, SHOT / "week003_00_reference.png")
    lines.append("    saved: week003_00_reference.png, week003_01_generate* html|png|json|b64")
    lines.append("")
    lines.extend(
        [
            "--- POST /edit（产生 week003_02_after_edit*）请求说明 ---",
            f"  URL: POST {base.rstrip('/')}/edit",
            "  JSON 键: current_code, instruction, width, height",
            f"  instruction（自然语言，英文）: {EDIT_INSTRUCTION!r}",
            f"  width x height: {vw} x {vh} （与 REF_PNG 一致）",
            "  current_code: 与上一步 /generate 返回的 code 相同（落盘为 week003_01_generate.html，日志不重复全文）",
            "  源码常量: 本脚本 EDIT_INSTRUCTION",
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
            "width": vw,
            "height": vh,
        },
    )
    lines.append(f"    elapsed {round(time.time() - t1, 1)}s")
    _assert_ui2()
    code = ed.get("code") or code
    (OUT / "week003_02_after_edit.html").write_text(code, encoding="utf-8")
    _write_png_b64(ed.get("preview_base64"), SHOT / "week003_02_after_edit_preview.png")
    _write_json(ed, OUT / "week003_02_after_edit_response.json")
    _write_b64_text(ed.get("preview_base64"), SHOT / "week003_02_after_edit_preview.b64")
    lines.append("    saved: week003_02_* html|png|json|b64")
    lines.append("")

    # 3) refine rounds
    b64_ref = _b64file(REF_PNG)
    code_ref = code
    for i in range(1, REFINE_ROUNDS + 1):
        lines.append(f"[3.{i}] render + refine, iteration {i} ...")
        rend = _post_json(
            "/render",
            {"html_code": code_ref, "width": vw, "height": vh},
        )
        r_b64 = rend.get("image_base64") or ""
        a_name = f"week003_refine_iter{i}_a_render_in.png"
        _write_png_b64(r_b64, SHOT / a_name)
        _write_json(rend, OUT / f"week003_refine_iter{i}_render_api.json")
        _write_b64_text(r_b64, SHOT / f"week003_refine_iter{i}_a_render_in.b64")
        t2 = time.time()
        rf = _post_json(
            "/refine",
            {
                "reference_image_base64": b64_ref,
                "current_code": code_ref,
                "rendered_image_base64": r_b64,
                "width": vw,
                "height": vh,
            },
        )
        lines.append(f"    refine elapsed {round(time.time() - t2, 1)}s")
        _assert_ui2()
        code_ref = rf.get("code") or code_ref
        b_name = f"week003_refine_iter{i}_b_preview.png"
        _write_png_b64(rf.get("preview_base64"), SHOT / b_name)
        _write_json(rf, OUT / f"week003_refine_iter{i}_refine_response.json")
        _write_b64_text(rf.get("preview_base64"), SHOT / f"week003_refine_iter{i}_b_preview.b64")
        (OUT / f"week003_refine_iter{i}.html").write_text(code_ref, encoding="utf-8")
        lines.append(
            f"    saved: {a_name}, a_render_in.b64, {b_name}, b_preview.b64, *response.json, week003_refine_iter{i}.html"
        )
        lines.append("")

    # 4) evidence (playwright) — use project venv if present so Playwright is found
    cap = ROOT / "local-service" / "capture_week3_evidence.py"
    if cap.is_file():
        vpy_linux = ROOT / "local-service" / ".venv" / "bin" / "python"
        vpy_win = ROOT / "local-service" / ".venv" / "Scripts" / "python.exe"
        if vpy_linux.is_file():
            py = str(vpy_linux)
        elif vpy_win.is_file():
            py = str(vpy_win)
        else:
            py = sys.executable
        lines.append("[4] capture Swagger + health JSON ...")
        r = subprocess.run(
            [py, str(cap), "--base", base, "--out-dir", str(SHOT)],
            cwd=str(ROOT),
        )
        if r.returncode != 0:
            lines.append("    (evidence script failed; check server)")

    summary = f"""=== POST /edit（After-edit）复现说明 ===
URL: POST {base.rstrip("/")}/edit
Body（JSON）:
  "current_code": <与 week003_01_generate.html 相同，即上一步 /generate 的完整 HTML>
  "instruction": {EDIT_INSTRUCTION!r}
  "width": {vw}
  "height": {vh}

自然语言指令（instruction）英文原文:
{EDIT_INSTRUCTION}

===
VERIFY: GET {base.rstrip("/")}/health 应显示 ui2code_n_active: true
"""
    (OUT / "week003_RECORD.txt").write_text(summary, encoding="utf-8")
    (OUT / "week003_RUN_LOG.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        raise SystemExit(1)
