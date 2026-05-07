"""
Week 6 minimum deliverables on the real UI2Code^N model.

Hits the running uvicorn (default http://127.0.0.1:8000) and produces week-6
style artifacts. This repo keeps **two** mockups: **m1** (production overview)
and **m4** (operator panel) — each with generate + refine x2, same file layout.
Use ``WEEK6_ONLY=m1_production_overview`` when m4 is already on disk and you only
need to refresh m1.

  * 3-panel collages:
      week06_m1_reference_generate_refine2.png
      week06_m4_reference_generate_refine2.png

Outputs:
  reports/deliverables_week6/
      <mockup>/generate.html
      <mockup>/generate.png
      <mockup>/refine_iter1.html | refine_iter1.png        (refine targets)
      <mockup>/refine_iter2.html | refine_iter2.png
      <mockup>/responses/*.json
  reports/deliverables_week6/week06_*.png   (3-panel collages)
  reports/deliverables_week6/run-log.txt
  reports/deliverables_week6/metrics.json

Environment (optional):
  WEEK6_ONLY — comma-separated mockup folder ids; restrict generate+refine
               (e.g. ``m1_production_overview`` only when m4 already exists).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "deliverables_week6"
OUT.mkdir(parents=True, exist_ok=True)

API_BASE = (os.environ.get("API_BASE") or "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = int(os.environ.get("WEEK6_TIMEOUT") or 1800)

# Comma-separated mockup folder ids, e.g. m1_production_overview
# When set, only those ids run in generate + refine.
def _week6_only_ids() -> set[str] | None:
    raw = (os.environ.get("WEEK6_ONLY") or "").strip()
    if not raw:
        return None
    return {p.strip() for p in raw.split(",") if p.strip()}


def _filter_mockups(
    targets: list[tuple[str, str, str]], only: set[str] | None
) -> list[tuple[str, str, str]]:
    if only is None:
        return list(targets)
    return [t for t in targets if t[0] in only]


# Two use cases: production line overview (m1) and operator panel (m4).
GENERATE_TARGETS: list[tuple[str, str, str]] = [
    ("m1_production_overview", "Production Line Overview", "mockups/png/05-production-overview.png"),
    ("m4_operator_panel", "Operator Control Panel", "mockups/png/04-operator-panel.png"),
]

# Same as generate: per mockup, generate + refine x2, shared layout under OUT/<id>/.
REFINE_TARGETS: list[tuple[str, str, str]] = [
    ("m1_production_overview", "Production Line Overview", "mockups/png/05-production-overview.png"),
    ("m4_operator_panel", "Operator Control Panel", "mockups/png/04-operator-panel.png"),
]


def b64_file(p: Path) -> str:
    return base64.standard_b64encode(p.read_bytes()).decode("ascii")


def write_b64_png(b64: str | None, path: Path) -> None:
    if not b64:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.standard_b64decode(b64))


def write_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def post_json(path: str, body: dict) -> dict:
    url = API_BASE + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def get_health() -> dict:
    with urllib.request.urlopen(API_BASE + "/health", timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def assert_real_model() -> None:
    h = get_health()
    if not h.get("ui2code_n_active"):
        raise SystemExit(
            "Refuse to run week-6 deliverables: ui2code_n_active is False. "
            f"/health says {h}."
        )


def run_generate(mockup_id: str, frame_name: str, ref_png: Path) -> tuple[str, dict]:
    body = {
        "image_base64": b64_file(ref_png),
        "frame_name": frame_name,
        "width": 1280,
        "height": 720,
    }
    t0 = time.time()
    resp = post_json("/generate", body)
    elapsed = round(time.time() - t0, 2)

    out_dir = OUT / mockup_id
    out_dir.mkdir(parents=True, exist_ok=True)
    code = resp.get("code") or ""
    (out_dir / "generate.html").write_text(code, encoding="utf-8")
    write_b64_png(resp.get("preview_base64"), out_dir / "generate.png")
    write_json(resp, out_dir / "responses" / "generate.json")

    return code, {"elapsed_s": elapsed, "code_chars": len(code), "preview_ok": bool(resp.get("preview_base64"))}


def run_refine(
    mockup_id: str,
    frame_name: str,
    ref_png: Path,
    seed_code: str,
    iterations: int = 2,
) -> list[dict]:
    out_dir = OUT / mockup_id
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_b64 = b64_file(ref_png)
    code = seed_code
    timings: list[dict] = []

    for i in range(1, iterations + 1):
        # render current code → PNG (this is the "what the model already produced")
        rend = post_json("/render", {"html_code": code, "width": 1280, "height": 720})
        rendered_b64 = rend.get("image_base64") or ""
        write_b64_png(rendered_b64, out_dir / f"refine_iter{i}_in.png")
        write_json(rend, out_dir / "responses" / f"refine_iter{i}_render.json")

        t0 = time.time()
        rf = post_json(
            "/refine",
            {
                "reference_image_base64": ref_b64,
                "current_code": code,
                "rendered_image_base64": rendered_b64,
                "width": 1280,
                "height": 720,
            },
        )
        elapsed = round(time.time() - t0, 2)

        code = rf.get("code") or code
        (out_dir / f"refine_iter{i}.html").write_text(code, encoding="utf-8")
        write_b64_png(rf.get("preview_base64"), out_dir / f"refine_iter{i}.png")
        write_json(rf, out_dir / "responses" / f"refine_iter{i}.json")

        timings.append(
            {
                "iter": i,
                "refine_elapsed_s": elapsed,
                "code_chars": len(code),
                "preview_ok": bool(rf.get("preview_base64")),
            }
        )

    return timings


def build_collage(reference: Path, generate: Path, refine_iter2: Path, out: Path, label_left: str) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:
        print(f"[warn] Pillow missing, skip collage {out.name}: {exc}")
        return

    target_h = 540
    panels: list[tuple[Image.Image, str]] = []
    for path, caption in [
        (reference, f"{label_left} — reference (PNG mockup)"),
        (generate, "Generate (real model first pass)"),
        (refine_iter2, "Refine ×2 (real model)"),
    ]:
        if not path.is_file():
            print(f"[warn] missing panel {path}, skip collage {out.name}")
            return
        im = Image.open(path).convert("RGB")
        w, h = im.size
        if h != target_h:
            new_w = max(1, int(w * (target_h / h)))
            im = im.resize((new_w, target_h), Image.Resampling.LANCZOS)
        panels.append((im, caption))

    gap = 16
    total_w = sum(im.size[0] for im, _ in panels) + gap * (len(panels) - 1)
    caption_h = 36
    canvas = Image.new("RGB", (total_w, target_h + caption_h), (24, 24, 28))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    x = 0
    for im, cap in panels:
        canvas.paste(im, (x, caption_h))
        draw.text((x + 8, 8), cap, fill=(220, 220, 220), font=font)
        x += im.size[0] + gap

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "PNG")


def main() -> int:
    print(f"[info] base={API_BASE} out={OUT}")
    try:
        assert_real_model()
    except urllib.error.URLError as e:
        print(f"[fatal] cannot reach {API_BASE}: {e}")
        return 1

    metrics: dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "api_base": API_BASE,
        "model": "ui2coden",
        "generate": {},
        "refine": {},
    }

    seed_codes: dict[str, str] = {}
    only = _week6_only_ids()
    if only:
        print(f"[info] WEEK6_ONLY={sorted(only)}")

    # generate phase
    for mid, name, rel in _filter_mockups(GENERATE_TARGETS, only):
        ref = ROOT / rel
        if not ref.is_file():
            print(f"[skip] {mid}: missing {ref}")
            continue
        print(f"[generate] {mid} ({name})")
        code, stats = run_generate(mid, name, ref)
        seed_codes[mid] = code
        metrics["generate"][mid] = {"frame": name, **stats}
        write_json(metrics, OUT / "metrics.json")

    # refine phase (2 iters each)
    for mid, name, rel in _filter_mockups(REFINE_TARGETS, only):
        ref = ROOT / rel
        if not ref.is_file():
            print(f"[skip-refine] {mid}: missing {ref}")
            continue
        seed = seed_codes.get(mid)
        if seed is None:
            print(f"[generate-for-refine] {mid} ({name})")
            seed, gstats = run_generate(mid, name, ref)
            metrics["generate"].setdefault(mid, {"frame": name, **gstats})
            seed_codes[mid] = seed
        print(f"[refine x2] {mid} ({name})")
        timings = run_refine(mid, name, ref, seed, iterations=2)
        metrics["refine"][mid] = {"frame": name, "iters": timings}
        write_json(metrics, OUT / "metrics.json")

    metrics["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(metrics, OUT / "metrics.json")

    # collages
    build_collage(
        reference=ROOT / "mockups" / "png" / "05-production-overview.png",
        generate=OUT / "m1_production_overview" / "generate.png",
        refine_iter2=OUT / "m1_production_overview" / "refine_iter2.png",
        out=OUT / "week06_m1_reference_generate_refine2.png",
        label_left="Production Line Overview",
    )
    build_collage(
        reference=ROOT / "mockups" / "png" / "04-operator-panel.png",
        generate=OUT / "m4_operator_panel" / "generate.png",
        refine_iter2=OUT / "m4_operator_panel" / "refine_iter2.png",
        out=OUT / "week06_m4_reference_generate_refine2.png",
        label_left="Operator Control Panel",
    )

    log = [
        f"=== Week-6 real-model run ({metrics.get('started_at')} -> {metrics.get('finished_at')}) ===",
        f"API base: {API_BASE}",
        f"Generate: {list(metrics['generate'].keys())}",
        f"Refine x2: {list(metrics['refine'].keys())}",
        f"Outputs: {OUT}",
    ]
    (OUT / "run-log.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
